from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from bikeshop.models import GameSession, Supplier, SupplierPrice
from .models import ProcurementOrder, ProcurementOrderItem
from .forms import ProcurementForm
from warehouse.models import Warehouse, ComponentStock
import json
from decimal import Decimal


@login_required
def procurement_view(request, session_id):
    """Einkaufsansicht"""
    session = get_object_or_404(GameSession, id=session_id, user=request.user)
    suppliers = Supplier.objects.filter(session=session)

    # Hole Preise für alle Lieferanten
    supplier_data = {}
    supplier_data_json = {}
    for supplier in suppliers:
        prices = SupplierPrice.objects.filter(session=session, supplier=supplier).select_related(
            'component__component_type')
        supplier_data[supplier.id] = {
            'supplier': supplier,
            'prices': prices
        }
        
        # Create JSON-serializable version for JavaScript
        supplier_data_json[str(supplier.id)] = {
            'supplier': {
                'id': supplier.id,
                'name': supplier.name,
                'quality': supplier.quality,
                'delivery_time': supplier.delivery_time,
                'payment_terms': supplier.payment_terms,
                'complaint_probability': float(supplier.complaint_probability)
            },
            'prices': [
                {
                    'component': {
                        'id': price.component.id,
                        'name': price.component.name,
                        'component_type': {
                            'name': price.component.component_type.name
                        }
                    },
                    'price': float(price.price)
                }
                for price in prices
            ]
        }

    if request.method == 'POST':
        try:
            with transaction.atomic():
                order_data = json.loads(request.body)
                total_cost = Decimal('0')

                # Get or create warehouse for this session
                warehouse, created = Warehouse.objects.get_or_create(
                    session=session,
                    defaults={
                        'name': 'Hauptlager',
                        'location': 'Standort 1',
                        'capacity_m2': 1000.0,
                        'rent_per_month': Decimal('2000.00')
                    }
                )

                # Erstelle Bestellungen für jeden Lieferanten
                for supplier_id, items in order_data.items():
                    if not items:
                        continue

                    supplier = get_object_or_404(Supplier, id=supplier_id, session=session)
                    order = ProcurementOrder.objects.create(
                        session=session,
                        supplier=supplier,
                        month=session.current_month,
                        year=session.current_year
                    )

                    order_total = Decimal('0')
                    for item in items:
                        component_id = item['component_id']
                        quantity = int(item['quantity'])

                        price_obj = get_object_or_404(SupplierPrice,
                                                      session=session,
                                                      supplier=supplier,
                                                      component_id=component_id
                                                      )

                        ProcurementOrderItem.objects.create(
                            order=order,
                            component=price_obj.component,
                            quantity_ordered=quantity,
                            quantity_delivered=quantity,  # Vereinfachung
                            unit_price=price_obj.price
                        )

                        # Add to warehouse inventory
                        component_stock, created = ComponentStock.objects.get_or_create(
                            session=session,
                            warehouse=warehouse,
                            component=price_obj.component,
                            defaults={'quantity': 0}
                        )
                        component_stock.quantity += quantity
                        component_stock.save()

                        order_total += price_obj.price * quantity

                    order.total_cost = order_total
                    order.save()
                    total_cost += order_total

                # Guthaben reduzieren
                session.balance -= total_cost
                session.save()

                return JsonResponse({'success': True, 'message': 'Bestellung erfolgreich aufgegeben und Komponenten ins Lager eingelagert!'})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return render(request, 'procurement/procurement.html', {
        'session': session,
        'supplier_data': supplier_data,
        'supplier_data_json': json.dumps(supplier_data_json)
    })
