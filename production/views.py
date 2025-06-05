from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from bikeshop.models import GameSession, BikeType, Worker
from .models import ProductionPlan, ProductionOrder, ProducedBike
from warehouse.models import Warehouse, ComponentStock
import json


@login_required
def production_view(request, session_id):
    """Produktionsansicht"""
    session = get_object_or_404(GameSession, id=session_id, user=request.user)
    bike_types = BikeType.objects.filter(session=session)
    workers = Worker.objects.filter(session=session)

    # Aktuelle Lagerbestände
    component_stocks = ComponentStock.objects.filter(session=session)

    if request.method == 'POST':
        try:
            production_data = json.loads(request.body)

            plan, created = ProductionPlan.objects.get_or_create(
                session=session,
                month=session.current_month,
                year=session.current_year
            )

            # Lösche alte Aufträge
            plan.orders.all().delete()

            total_skilled_hours = 0
            total_unskilled_hours = 0

            for item in production_data:
                bike_type = get_object_or_404(BikeType, id=item['bike_type_id'], session=session)

                for segment in ['cheap', 'standard', 'premium']:
                    quantity = int(item.get(f'quantity_{segment}', 0))

                    if quantity > 0:
                        ProductionOrder.objects.create(
                            plan=plan,
                            bike_type=bike_type,
                            price_segment=segment,
                            quantity_planned=quantity
                        )

                        total_skilled_hours += bike_type.skilled_worker_hours * quantity
                        total_unskilled_hours += bike_type.unskilled_worker_hours * quantity

            # Prüfe Arbeiterkapazität
            skilled_worker = workers.filter(worker_type='skilled').first()
            unskilled_worker = workers.filter(worker_type='unskilled').first()

            skilled_capacity = skilled_worker.count * skilled_worker.monthly_hours if skilled_worker else 0
            unskilled_capacity = unskilled_worker.count * unskilled_worker.monthly_hours if unskilled_worker else 0

            if total_skilled_hours > skilled_capacity or total_unskilled_hours > unskilled_capacity:
                return JsonResponse({
                    'success': False,
                    'error': 'Nicht genügend Arbeiterkapazität vorhanden!'
                })

            return JsonResponse({'success': True, 'message': 'Produktionsplan erstellt!'})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return render(request, 'production/production.html', {
        'session': session,
        'bike_types': bike_types,
        'workers': workers,
        'component_stocks': component_stocks
    })
