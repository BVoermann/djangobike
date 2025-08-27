from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from bikeshop.models import GameSession
from .models import Warehouse, ComponentStock, BikeStock
import json


@login_required
def warehouse_view(request, session_id):
    """Lageransicht"""
    session = get_object_or_404(GameSession, id=session_id, user=request.user)
    warehouses = Warehouse.objects.filter(session=session)

    warehouse_data = []
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

    return render(request, 'warehouse/warehouse.html', {
        'session': session,
        'warehouse_data': warehouse_data
    })
