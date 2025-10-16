from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import transaction
from django.db.models import Count, Avg, Min, Sum
from bikeshop.models import GameSession, BikePrice, BikeType
from .models import Market, MarketDemand, SalesOrder
from production.models import ProducedBike
from finance.models import Transaction
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
                total_revenue = 0

                for item in sales_data:
                    market = get_object_or_404(Market, id=item['market_id'], session=session)
                    bike_groups_to_sell = item['bike_groups']

                    for group_data in bike_groups_to_sell:
                        bike_type_id = group_data['bike_type_id']
                        price_segment = group_data['price_segment']
                        quantity = int(group_data['quantity'])
                        sale_price = group_data['price']
                        transport_cost = group_data['transport_cost']

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

                        # Fetch the requested number of bikes
                        bikes = ProducedBike.objects.filter(
                            session=session,
                            bike_type_id=bike_type_id,
                            price_segment=price_segment,
                            is_sold=False
                        )[:quantity]

                        if len(bikes) < quantity:
                            return JsonResponse({
                                'success': False,
                                'error': f'Nicht genügend {bike_type.name} ({dict(ProducedBike._meta.get_field("price_segment").choices)[price_segment]}) verfügbar. Verfügbar: {len(bikes)}, Angefordert: {quantity}'
                            })

                        # Sell each bike
                        for bike in bikes:
                            # Create sales order
                            sales_order = SalesOrder.objects.create(
                                session=session,
                                market=market,
                                bike=bike,
                                sale_month=session.current_month,
                                sale_year=session.current_year,
                                sale_price=sale_price,
                                transport_cost=transport_cost
                            )

                            # Calculate net revenue (sale price minus transport cost)
                            net_revenue = sale_price - transport_cost
                            total_revenue += net_revenue

                            # Create financial transaction
                            Transaction.objects.create(
                                session=session,
                                transaction_type='income',
                                category='Verkäufe',
                                amount=net_revenue,
                                description=f'Verkauf {bike.bike_type.name} ({bike.get_price_segment_display()}) an {market.name}',
                                month=session.current_month,
                                year=session.current_year
                            )

                            # Mark bike as sold
                            bike.is_sold = True
                            bike.save()

                # Update session balance
                session.balance += total_revenue
                session.save()

            return JsonResponse({
                'success': True,
                'message': f'Verkaufsaufträge erstellt! Umsatz: {total_revenue:.2f}€',
                'revenue': float(total_revenue),
                'new_balance': float(session.balance)
            })

        except Exception as e:
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

    return render(request, 'sales/sales.html', {
        'session': session,
        'markets': markets,
        'bike_groups': bike_groups,
        'total_bikes_count': total_bikes_count,
        'current_month_sales': current_month_sales,
        'sales_stats': sales_stats,
        'sales_by_market': dict(sales_by_market)
    })
