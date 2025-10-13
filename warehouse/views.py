from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import transaction
from bikeshop.models import GameSession
from .models import Warehouse, ComponentStock, BikeStock, WarehouseType
from decimal import Decimal
import json


@login_required
def warehouse_view(request, session_id):
    """Lageransicht"""
    session = get_object_or_404(GameSession, id=session_id, user=request.user)
    warehouses = Warehouse.objects.filter(session=session)

    warehouse_data = []
    total_capacity = 0
    total_rent = 0

    for warehouse in warehouses:
        stocks = ComponentStock.objects.filter(warehouse=warehouse).select_related('component__component_type')
        bike_stocks = BikeStock.objects.filter(warehouse=warehouse).select_related('bike__bike_type')
        warehouse_data.append({
            'warehouse': warehouse,
            'stocks': stocks,
            'bike_stocks': bike_stocks,
            'usage': warehouse.current_usage,
            'remaining': warehouse.remaining_capacity
        })
        total_capacity += warehouse.capacity_m2
        total_rent += warehouse.rent_per_month

    return render(request, 'warehouse/warehouse.html', {
        'session': session,
        'warehouse_data': warehouse_data,
        'total_capacity': total_capacity,
        'total_rent': total_rent
    })


@login_required
def purchase_warehouse(request, session_id):
    """Warehouse purchase view"""
    session = get_object_or_404(GameSession, id=session_id, user=request.user)

    # Ensure warehouse types exist
    if not WarehouseType.objects.exists():
        for warehouse_type_data in WarehouseType.get_default_types():
            WarehouseType.objects.create(**warehouse_type_data)

    warehouse_types = WarehouseType.objects.all()
    existing_warehouses = Warehouse.objects.filter(session=session)

    if request.method == 'POST':
        try:
            with transaction.atomic():
                data = json.loads(request.body)
                warehouse_type_id = data.get('warehouse_type_id')
                warehouse_name = data.get('name', '')
                warehouse_location = data.get('location', '')

                warehouse_type = get_object_or_404(WarehouseType, id=warehouse_type_id)

                # Check if player has enough money
                if session.balance < warehouse_type.purchase_price:
                    return JsonResponse({
                        'success': False,
                        'error': f'Nicht genügend Guthaben! Kaufpreis: {warehouse_type.purchase_price}€, Verfügbar: {session.balance}€'
                    })

                # Create warehouse
                warehouse = Warehouse.objects.create(
                    session=session,
                    name=warehouse_name or f"{warehouse_type.name} Lager #{existing_warehouses.count() + 1}",
                    location=warehouse_location or f"Standort {existing_warehouses.count() + 1}",
                    capacity_m2=warehouse_type.capacity_m2,
                    rent_per_month=warehouse_type.monthly_rent
                )

                # Deduct purchase price from balance
                session.balance -= warehouse_type.purchase_price
                session.save()

                return JsonResponse({
                    'success': True,
                    'message': f'Lager "{warehouse.name}" erfolgreich gekauft!',
                    'new_balance': float(session.balance),
                    'warehouse': {
                        'id': warehouse.id,
                        'name': warehouse.name,
                        'capacity': warehouse.capacity_m2,
                        'rent': float(warehouse.rent_per_month)
                    }
                })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return render(request, 'warehouse/purchase_warehouse.html', {
        'session': session,
        'warehouse_types': warehouse_types,
        'existing_warehouses': existing_warehouses
    })
