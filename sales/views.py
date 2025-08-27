from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import transaction
from bikeshop.models import GameSession, BikePrice
from .models import Market, MarketDemand, SalesOrder
from production.models import ProducedBike
from finance.models import Transaction
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

    # Verfügbare Fahrräder with price ranges
    available_bikes = ProducedBike.objects.filter(session=session, is_sold=False)
    
    # Add price range information to each bike
    for bike in available_bikes:
        min_price, max_price = get_price_range(bike.bike_type, bike.price_segment, session)
        bike.min_price = min_price
        bike.max_price = max_price
        bike.suggested_price = round((min_price + max_price) / 2, 2)  # Midpoint as suggestion

    if request.method == 'POST':
        try:
            with transaction.atomic():  # Ensure all operations succeed or fail together
                sales_data = json.loads(request.body)
                total_revenue = 0

                for item in sales_data:
                    market = get_object_or_404(Market, id=item['market_id'], session=session)
                    bikes_to_sell = item['bikes']

                    for bike_data in bikes_to_sell:
                        bike = get_object_or_404(ProducedBike, id=bike_data['bike_id'], session=session)

                        if not bike.is_sold:
                            # Validate price is within acceptable range
                            min_price, max_price = get_price_range(bike.bike_type, bike.price_segment, session)
                            sale_price = bike_data['price']
                            
                            if sale_price < min_price:
                                return JsonResponse({
                                    'success': False, 
                                    'error': f'Preis für {bike.bike_type.name} ({bike.get_price_segment_display()}) zu niedrig. Minimum: {min_price}€'
                                })
                            
                            if sale_price > max_price:
                                return JsonResponse({
                                    'success': False, 
                                    'error': f'Preis für {bike.bike_type.name} ({bike.get_price_segment_display()}) zu hoch. Maximum: {max_price}€'
                                })
                            # Create sales order
                            sales_order = SalesOrder.objects.create(
                                session=session,
                                market=market,
                                bike=bike,
                                sale_month=session.current_month,
                                sale_year=session.current_year,
                                sale_price=bike_data['price'],
                                transport_cost=bike_data['transport_cost']
                            )

                            # Calculate net revenue (sale price minus transport cost)
                            net_revenue = bike_data['price'] - bike_data['transport_cost']
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

    return render(request, 'sales/sales.html', {
        'session': session,
        'markets': markets,
        'available_bikes': available_bikes
    })
