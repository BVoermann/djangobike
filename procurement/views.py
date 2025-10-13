from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from bikeshop.models import GameSession, Supplier, SupplierPrice, BikeType
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
    bike_types = BikeType.objects.filter(session=session)

    # Create bike type component mapping using new flexible system
    bike_component_mapping = {}
    for bike_type in bike_types:
        # Get all compatible component IDs for this bike type
        from bikeshop.models import Component, ComponentType
        compatible_component_ids = []
        
        requirements = bike_type.get_required_components()
        
        # If no requirements are set, use fallback to legacy system or include all components
        if not requirements:
            # Fallback: use legacy system if available
            legacy_components = []
            if bike_type.wheel_set:
                legacy_components.append(bike_type.wheel_set.id)
            if bike_type.frame:
                legacy_components.append(bike_type.frame.id)
            if bike_type.handlebar:
                legacy_components.append(bike_type.handlebar.id)
            if bike_type.saddle:
                legacy_components.append(bike_type.saddle.id)
            if bike_type.gearshift:
                legacy_components.append(bike_type.gearshift.id)
            if bike_type.motor:
                legacy_components.append(bike_type.motor.id)
                
            if legacy_components:
                compatible_component_ids = legacy_components
            else:
                # Ultimate fallback: include all components (let user decide)
                all_components = Component.objects.filter(session=session)
                compatible_component_ids = [c.id for c in all_components]
        else:
            # Use the new requirements system
            for component_type_name, compatible_names in requirements.items():
                component_type = ComponentType.objects.filter(
                    session=session, 
                    name=component_type_name
                ).first()
                
                if component_type:
                    compatible_components = Component.objects.filter(
                        session=session,
                        component_type=component_type,
                        name__in=compatible_names
                    )
                    compatible_component_ids.extend([c.id for c in compatible_components])
        
        bike_component_mapping[bike_type.id] = compatible_component_ids

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

                # Get all warehouses for this session
                warehouses = Warehouse.objects.filter(session=session)

                # Create warehouse if none exist
                if not warehouses.exists():
                    warehouse = Warehouse.objects.create(
                        session=session,
                        name='Hauptlager',
                        location='Standort 1',
                        capacity_m2=200.0,
                        rent_per_month=Decimal('2500.00')
                    )
                    warehouses = [warehouse]

                # Calculate total remaining capacity across all warehouses
                total_remaining_capacity = sum(w.remaining_capacity for w in warehouses)
                total_current_usage = sum(w.current_usage for w in warehouses)
                total_capacity = sum(w.capacity_m2 for w in warehouses)

                # First pass: Check warehouse capacity for all items
                total_required_space = 0
                for supplier_id, items in order_data.items():
                    if not items:
                        continue

                    for item in items:
                        component_id = item['component_id']
                        quantity = int(item['quantity'])

                        if quantity <= 0:
                            continue

                        price_obj = SupplierPrice.objects.filter(
                            session=session,
                            supplier_id=supplier_id,
                            component_id=component_id
                        ).first()

                        if price_obj:
                            # Use a warehouse to calculate required space (any will do for calculation)
                            required_space = warehouses[0].get_required_space_for_components(price_obj.component, quantity)
                            total_required_space += required_space

                # Check if total order would exceed total warehouse capacity
                if total_required_space > total_remaining_capacity:
                    current_percentage = (total_current_usage / total_capacity * 100) if total_capacity > 0 else 100
                    new_usage = total_current_usage + total_required_space
                    new_percentage = (new_usage / total_capacity) * 100 if total_capacity > 0 else 100

                    return JsonResponse({
                        'success': False,
                        'error': f'Lagerkapazität überschritten! Diese Bestellung würde {total_required_space:.1f}m² benötigen, aber nur {total_remaining_capacity:.1f}m² sind in allen Lagern verfügbar. Aktuelle Auslastung: {current_percentage:.1f}%, nach Bestellung: {new_percentage:.1f}%. Bitte kaufen Sie zusätzliche Lagerkapazität oder reduzieren Sie die Bestellmenge.'
                    })

                # Second pass: Create orders (capacity check passed)
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
                        
                        # Validate quantity
                        if quantity <= 0:
                            return JsonResponse({'success': False, 'error': 'Quantity must be greater than 0'})

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

                        # Find a warehouse with available capacity
                        required_space = warehouses[0].get_required_space_for_components(price_obj.component, quantity)
                        target_warehouse = None

                        for wh in warehouses:
                            if wh.remaining_capacity >= required_space:
                                target_warehouse = wh
                                break

                        # If no single warehouse has enough space, use the one with most space
                        if not target_warehouse:
                            target_warehouse = max(warehouses, key=lambda w: w.remaining_capacity)

                        # Add to warehouse inventory
                        component_stock, created = ComponentStock.objects.get_or_create(
                            session=session,
                            warehouse=target_warehouse,
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
        'supplier_data_json': json.dumps(supplier_data_json),
        'bike_types': bike_types,
        'bike_component_mapping': json.dumps(bike_component_mapping)
    })
