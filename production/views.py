from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from bikeshop.models import GameSession, BikeType, Worker
from .models import ProductionPlan, ProductionOrder, ProducedBike
from warehouse.models import Warehouse, ComponentStock, BikeStock
import json
import random
from decimal import Decimal


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
            with transaction.atomic():
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
                total_bikes_produced = 0
                
                # Check if upgrades are needed and collect upgrade information
                upgrades_needed = []
                component_requirements = {}
                
                # First pass: Calculate requirements and check feasibility
                for item in production_data:
                    bike_type = get_object_or_404(BikeType, id=item['bike_type_id'], session=session)

                    for segment in ['cheap', 'standard', 'premium']:
                        quantity = int(item.get(f'quantity_{segment}', 0))

                        if quantity > 0:
                            # Calculate worker hours
                            total_skilled_hours += bike_type.skilled_worker_hours * quantity
                            total_unskilled_hours += bike_type.unskilled_worker_hours * quantity
                            total_bikes_produced += quantity
                            
                            # Use the new flexible component matching system
                            component_match_result = bike_type.find_best_components_for_segment(session, segment)
                            
                            # Check if any components are missing
                            if component_match_result['missing']:
                                missing_components = ', '.join(component_match_result['missing'])
                                return JsonResponse({
                                    'success': False,
                                    'error': f'Keine verfügbaren Komponenten für {segment} {bike_type.name}! Fehlend: {missing_components}'
                                })
                            
                            # Collect upgrade information for confirmation
                            if component_match_result['upgrades']:
                                for upgrade in component_match_result['upgrades']:
                                    upgrade_info = {
                                        'bike_type': bike_type.name,
                                        'segment': segment,
                                        'component_type': upgrade['component_type'],
                                        'component_name': upgrade['component_name'],
                                        'component_quality': upgrade['component_quality'],
                                        'target_segment': upgrade['target_segment']
                                    }
                                    upgrades_needed.append(upgrade_info)
                            
                            # Add component requirements
                            for component_type_name, component in component_match_result['components'].items():
                                if component.id not in component_requirements:
                                    component_requirements[component.id] = 0
                                component_requirements[component.id] += quantity
                
                # If upgrades are needed and user hasn't confirmed, ask for confirmation
                confirm_upgrades = request.GET.get('confirm_upgrades', '').lower() == 'true'
                if upgrades_needed and not confirm_upgrades:
                    return JsonResponse({
                        'success': False,
                        'upgrades_needed': True,
                        'upgrades': upgrades_needed,
                        'message': 'Qualitäts-Upgrades erforderlich. Bestätigung benötigt.'
                    })

                # Check worker capacity
                skilled_worker = workers.filter(worker_type='skilled').first()
                unskilled_worker = workers.filter(worker_type='unskilled').first()

                skilled_capacity = skilled_worker.count * skilled_worker.monthly_hours if skilled_worker else 0
                unskilled_capacity = unskilled_worker.count * unskilled_worker.monthly_hours if unskilled_worker else 0

                if total_skilled_hours > skilled_capacity:
                    return JsonResponse({
                        'success': False,
                        'error': f'Nicht genügend Facharbeiter-Kapazität! Benötigt: {total_skilled_hours}h, Verfügbar: {skilled_capacity}h'
                    })
                
                if total_unskilled_hours > unskilled_capacity:
                    return JsonResponse({
                        'success': False,
                        'error': f'Nicht genügend Hilfsarbeiter-Kapazität! Benötigt: {total_unskilled_hours}h, Verfügbar: {unskilled_capacity}h'
                    })

                # Check component availability
                component_stocks_dict = {}
                for stock in component_stocks:
                    component_stocks_dict[stock.component.id] = stock
                
                for component_id, required_quantity in component_requirements.items():
                    if component_id not in component_stocks_dict:
                        return JsonResponse({
                            'success': False,
                            'error': f'Komponente nicht im Lager vorhanden!'
                        })
                    
                    available_quantity = component_stocks_dict[component_id].quantity
                    if available_quantity < required_quantity:
                        component_name = component_stocks_dict[component_id].component.name
                        return JsonResponse({
                            'success': False,
                            'error': f'Nicht genügend {component_name} im Lager! Benötigt: {required_quantity}, Verfügbar: {available_quantity}'
                        })

                # Get warehouse for storage
                warehouse = Warehouse.objects.filter(session=session).first()
                if not warehouse:
                    return JsonResponse({
                        'success': False,
                        'error': 'Kein Lager verfügbar!'
                    })

                # Second pass: Actually produce bikes and update inventory
                for item in production_data:
                    bike_type = get_object_or_404(BikeType, id=item['bike_type_id'], session=session)

                    for segment in ['cheap', 'standard', 'premium']:
                        quantity = int(item.get(f'quantity_{segment}', 0))

                        if quantity > 0:
                            # Create production order
                            production_order = ProductionOrder.objects.create(
                                plan=plan,
                                bike_type=bike_type,
                                price_segment=segment,
                                quantity_planned=quantity
                            )

                            # Produce individual bikes and add to warehouse
                            for _ in range(quantity):
                                produced_bike = ProducedBike.objects.create(
                                    session=session,
                                    bike_type=bike_type,
                                    price_segment=segment,
                                    production_month=session.current_month,
                                    production_year=session.current_year
                                )
                                
                                # Add to warehouse inventory
                                BikeStock.objects.create(
                                    session=session,
                                    warehouse=warehouse,
                                    bike=produced_bike
                                )

                # Update component stocks (reduce quantities)
                for component_id, used_quantity in component_requirements.items():
                    stock = component_stocks_dict[component_id]
                    stock.quantity -= used_quantity
                    stock.save()

                return JsonResponse({
                    'success': True, 
                    'message': f'Produktion erfolgreich! {total_bikes_produced} Fahrräder produziert und ins Lager eingelagert.'
                })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return render(request, 'production/production.html', {
        'session': session,
        'bike_types': bike_types,
        'workers': workers,
        'component_stocks': component_stocks
    })


@login_required
def hire_worker(request, session_id):
    """Arbeiter aus der Produktion einstellen"""
    session = get_object_or_404(GameSession, id=session_id, user=request.user)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            worker_type = data.get('worker_type')
            count = int(data.get('count', 1))
            
            if worker_type not in ['skilled', 'unskilled']:
                return JsonResponse({'success': False, 'error': 'Ungültiger Arbeitertyp'})
            
            # Get or create the Worker for this session and type
            worker, created = Worker.objects.get_or_create(
                session=session,
                worker_type=worker_type,
                defaults={
                    'hourly_wage': Decimal('25.00') if worker_type == 'skilled' else Decimal('15.00'),
                    'monthly_hours': 150,
                    'count': 0
                }
            )
            
            # Increment the count
            worker.count += count
            worker.save()
            
            # Calculate monthly cost per worker
            monthly_cost_per_worker = worker.hourly_wage * worker.monthly_hours
            total_cost = monthly_cost_per_worker * count
            
            worker_type_display = 'Facharbeiter' if worker_type == 'skilled' else 'Hilfsarbeiter'
            
            return JsonResponse({
                'success': True, 
                'message': f'{count} {worker_type_display} erfolgreich eingestellt!',
                'total_cost': float(total_cost),
                'new_count': worker.count
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Nur POST-Anfragen erlaubt'})
