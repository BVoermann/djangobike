from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import transaction
from django.db.models import Count, Avg, Min, Sum
from bikeshop.models import GameSession, BikePrice, BikeType
from .models import Market, MarketDemand, SalesOrder, SalesDecision
from production.models import ProducedBike
from finance.models import Transaction
from .market_simulator import MarketSimulator
from collections import defaultdict
import json
from decimal import Decimal


def get_price_range(bike_type, price_segment, session):
    """Calculate realistic price range for selling based on quality and base price"""
    try:
        base_price = BikePrice.objects.get(
            session=session, 
            bike_type=bike_type, 
            price_segment=price_segment
        ).price
    except BikePrice.DoesNotExist:
        # Fallback to default ranges if no base price found
        default_ranges = {
            'cheap': (200, 500),
            'standard': (400, 800), 
            'premium': (600, 1200)
        }
        return default_ranges.get(price_segment, (200, 500))
    
    # Define multipliers for each quality level
    multipliers = {
        'cheap': (0.8, 1.2),      # 80-120% of base price
        'standard': (1.0, 1.5),   # 100-150% of base price  
        'premium': (1.2, 2.0)     # 120-200% of base price
    }
    
    min_mult, max_mult = multipliers.get(price_segment, (0.8, 1.2))
    min_price = float(base_price * Decimal(str(min_mult)))
    max_price = float(base_price * Decimal(str(max_mult)))
    
    return (round(min_price, 2), round(max_price, 2))


@login_required
def sales_view(request, session_id):
    """Verkaufsansicht"""
    session = get_object_or_404(GameSession, id=session_id, user=request.user)
    markets = Market.objects.filter(session=session)

    # Group available bikes by bike_type and price_segment
    bike_groups = ProducedBike.objects.filter(
        session=session,
        is_sold=False
    ).values(
        'bike_type__id',
        'bike_type__name',
        'price_segment'
    ).annotate(
        count=Count('id'),
        avg_production_cost=Avg('production_cost')
    ).order_by('bike_type__name', 'price_segment')

    # Add price range information to each group
    for group in bike_groups:
        bike_type = BikeType.objects.get(id=group['bike_type__id'])
        min_price, max_price = get_price_range(
            bike_type,
            group['price_segment'],
            session
        )
        group['min_price'] = min_price
        group['max_price'] = max_price
        group['suggested_price'] = round((min_price + max_price) / 2, 2)

    if request.method == 'POST':
        try:
            with transaction.atomic():  # Ensure all operations succeed or fail together
                sales_data = json.loads(request.body)
                total_expected_revenue = 0
                total_quantity = 0
                decisions_created = []

                for item in sales_data:
                    market = get_object_or_404(Market, id=item['market_id'], session=session)
                    bike_groups_to_sell = item['bike_groups']

                    for group_data in bike_groups_to_sell:
                        bike_type_id = group_data['bike_type_id']
                        price_segment = group_data['price_segment']
                        quantity = int(group_data['quantity'])
                        sale_price = Decimal(str(group_data['price']))
                        transport_cost = Decimal(str(group_data['transport_cost']))

                        # Get bike_type for validation
                        bike_type = get_object_or_404(BikeType, id=bike_type_id)

                        # Validate price is within acceptable range
                        min_price, max_price = get_price_range(bike_type, price_segment, session)

                        if sale_price < min_price:
                            return JsonResponse({
                                'success': False,
                                'error': f'Preis für {bike_type.name} ({dict(ProducedBike._meta.get_field("price_segment").choices)[price_segment]}) zu niedrig. Minimum: {min_price}€'
                            })

                        if sale_price > max_price:
                            return JsonResponse({
                                'success': False,
                                'error': f'Preis für {bike_type.name} ({dict(ProducedBike._meta.get_field("price_segment").choices)[price_segment]}) zu hoch. Maximum: {max_price}€'
                            })

                        # Check if bikes are available
                        available_bikes = ProducedBike.objects.filter(
                            session=session,
                            bike_type_id=bike_type_id,
                            price_segment=price_segment,
                            is_sold=False
                        ).count()

                        if available_bikes < quantity:
                            return JsonResponse({
                                'success': False,
                                'error': f'Nicht genügend {bike_type.name} ({dict(ProducedBike._meta.get_field("price_segment").choices)[price_segment]}) verfügbar. Verfügbar: {available_bikes}, Angefordert: {quantity}'
                            })

                        # Create sales decision (NOT immediate sale)
                        decision = SalesDecision.objects.create(
                            session=session,
                            market=market,
                            bike_type=bike_type,
                            price_segment=price_segment,
                            quantity=quantity,
                            desired_price=sale_price,
                            transport_cost=transport_cost,
                            decision_month=session.current_month,
                            decision_year=session.current_year,
                            is_processed=False
                        )

                        # Calculate expected revenue (transport cost is per shipment, not per bike)
                        expected_net_revenue = (sale_price * quantity) - transport_cost
                        total_expected_revenue += expected_net_revenue
                        total_quantity += quantity

                        decisions_created.append({
                            'bike_type': bike_type.name,
                            'segment': dict(ProducedBike._meta.get_field("price_segment").choices)[price_segment],
                            'quantity': quantity,
                            'market': market.name,
                            'expected_revenue': float(expected_net_revenue)
                        })

                # Get simulator for preview summary
                simulator = MarketSimulator(session)
                preview_summary = simulator.get_pending_decisions_summary()

            return JsonResponse({
                'success': True,
                'message': f'Verkaufsentscheidungen gespeichert! Die Verkäufe werden beim nächsten Monatswechsel verarbeitet.',
                'total_quantity': total_quantity,
                'expected_revenue': float(total_expected_revenue),
                'decisions': decisions_created,
                'preview': {
                    'total_pending_quantity': preview_summary['total_quantity'],
                    'total_pending_revenue': float(preview_summary['total_expected_revenue']),
                },
                'info': 'Ihre Fahrräder werden beim nächsten Monatswechsel basierend auf Marktbedingungen verkauft.'
            })

        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'success': False, 'error': str(e)})

    # Calculate total available bikes count
    total_bikes_count = ProducedBike.objects.filter(session=session, is_sold=False).count()

    # Get sales history for current month
    current_month_sales = SalesOrder.objects.filter(
        session=session,
        sale_month=session.current_month,
        sale_year=session.current_year
    ).select_related('market', 'bike__bike_type')

    # Calculate sales statistics
    sales_stats = current_month_sales.aggregate(
        total_bikes_sold=Count('id'),
        total_revenue=Sum('sale_price'),
        total_transport_costs=Sum('transport_cost')
    )

    # Calculate net revenue
    total_revenue = sales_stats['total_revenue'] or 0
    total_transport = sales_stats['total_transport_costs'] or 0
    net_revenue = total_revenue - total_transport

    sales_stats['net_revenue'] = net_revenue

    # Group sales by market and then by bike type/segment for detailed view
    sales_by_market = defaultdict(lambda: {'bikes': {}, 'total': 0, 'count': 0})

    for sale in current_month_sales:
        market_name = sale.market.name
        bike_key = f"{sale.bike.bike_type.name}_{sale.bike.price_segment}"

        # Initialize bike group if not exists
        if bike_key not in sales_by_market[market_name]['bikes']:
            sales_by_market[market_name]['bikes'][bike_key] = {
                'bike_type': sale.bike.bike_type.name,
                'price_segment': sale.bike.get_price_segment_display(),
                'count': 0,
                'total_sale_price': 0,
                'total_transport_cost': 0,
                'total_net_revenue': 0
            }

        # Add to grouped data
        sales_by_market[market_name]['bikes'][bike_key]['count'] += 1
        sales_by_market[market_name]['bikes'][bike_key]['total_sale_price'] += float(sale.sale_price)
        sales_by_market[market_name]['bikes'][bike_key]['total_transport_cost'] += float(sale.transport_cost)
        sales_by_market[market_name]['bikes'][bike_key]['total_net_revenue'] += float(sale.sale_price - sale.transport_cost)

        sales_by_market[market_name]['total'] += sale.sale_price - sale.transport_cost
        sales_by_market[market_name]['count'] += 1

    # Convert bikes dict to list for template
    for market_name in sales_by_market:
        sales_by_market[market_name]['bikes'] = list(sales_by_market[market_name]['bikes'].values())

    # Get pending sales decisions
    simulator = MarketSimulator(session)
    pending_decisions_summary = simulator.get_pending_decisions_summary()

    # Get recent sales results (for feedback)
    recent_sales_results = simulator.get_recent_sales_results(months_back=1)

    return render(request, 'sales/sales.html', {
        'session': session,
        'markets': markets,
        'bike_groups': bike_groups,
        'total_bikes_count': total_bikes_count,
        'current_month_sales': current_month_sales,
        'sales_stats': sales_stats,
        'sales_by_market': dict(sales_by_market),
        'pending_decisions': pending_decisions_summary,
        'recent_sales_results': recent_sales_results,
    })


@login_required
@transaction.atomic
def get_market_demand_estimates(request, session_id):
    """
    API endpoint to get market demand estimates with research precision.

    Returns demand ranges based on player's market research investments.
    """
    session = get_object_or_404(GameSession, id=session_id, user=request.user)

    from .demand_calculator import DemandCalculator

    calculator = DemandCalculator(session)
    estimates = calculator.get_all_market_estimates(session.current_month, session.current_year)

    # Format for JSON response
    response_data = []
    for market_id, market_data in estimates.items():
        market_info = {
            'market_id': str(market_data['market'].id),
            'market_name': market_data['market'].name,
            'bike_types': []
        }

        for bike_type_id, bike_data in market_data['bike_types'].items():
            market_info['bike_types'].append({
                'bike_type_id': str(bike_data['bike_type'].id),
                'bike_type_name': bike_data['bike_type'].name,
                'estimated_min': bike_data['estimated_min'],
                'estimated_max': bike_data['estimated_max'],
                'research_level': bike_data['research_level'],
                'precision_percentage': bike_data['precision_percentage'],
            })

        response_data.append(market_info)

    return JsonResponse({
        'success': True,
        'estimates': response_data,
        'current_month': session.current_month,
        'current_year': session.current_year
    })


@login_required
@transaction.atomic
def purchase_market_research_view(request, session_id):
    """
    API endpoint to purchase market research.

    POST params:
        - market_id: UUID of the market
        - bike_type_id: UUID of the bike type
        - research_level: 'basic', 'advanced', or 'premium'
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)

    session = get_object_or_404(GameSession, id=session_id, user=request.user)

    try:
        data = json.loads(request.body)
        market_id = data.get('market_id')
        bike_type_id = data.get('bike_type_id')
        research_level = data.get('research_level')

        if not all([market_id, bike_type_id, research_level]):
            return JsonResponse({
                'success': False,
                'error': 'Missing required parameters'
            }, status=400)

        # Get market and bike type
        market = get_object_or_404(Market, id=market_id, session=session)
        bike_type = get_object_or_404(BikeType, id=bike_type_id, session=session)

        # Purchase research
        from .demand_calculator import purchase_market_research
        from .models_market_research import MarketResearch

        research, cost = purchase_market_research(
            session=session,
            market=market,
            bike_type=bike_type,
            research_level=research_level,
            current_month=session.current_month,
            current_year=session.current_year
        )

        return JsonResponse({
            'success': True,
            'message': f'{research_level.title()} research purchased',
            'cost': float(cost),
            'new_balance': float(session.balance),
            'estimated_min': research.estimated_min,
            'estimated_max': research.estimated_max,
            'expires_at': research.expires_at.isoformat(),
            'research_costs': {
                level: float(MarketResearch.get_research_cost(level))
                for level in ['basic', 'advanced', 'premium']
            }
        })

    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Server error: {str(e)}'}, status=500)
