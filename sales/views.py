from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from bikeshop.models import GameSession
from .models import Market, MarketDemand, SalesOrder
from production.models import ProducedBike
import json


@login_required
def sales_view(request, session_id):
    """Verkaufsansicht"""
    session = get_object_or_404(GameSession, id=session_id, user=request.user)
    markets = Market.objects.filter(session=session)

    # Verfügbare Fahrräder
    available_bikes = ProducedBike.objects.filter(session=session, is_sold=False)

    if request.method == 'POST':
        try:
            sales_data = json.loads(request.body)

            for item in sales_data:
                market = get_object_or_404(Market, id=item['market_id'], session=session)
                bikes_to_sell = item['bikes']

                for bike_data in bikes_to_sell:
                    bike = get_object_or_404(ProducedBike, id=bike_data['bike_id'], session=session)

                    if not bike.is_sold:
                        SalesOrder.objects.create(
                            session=session,
                            market=market,
                            bike=bike,
                            sale_month=session.current_month,
                            sale_year=session.current_year,
                            sale_price=bike_data['price'],
                            transport_cost=bike_data['transport_cost']
                        )

                        bike.is_sold = True
                        bike.save()

            return JsonResponse({'success': True, 'message': 'Verkaufsaufträge erstellt!'})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return render(request, 'sales/sales.html', {
        'session': session,
        'markets': markets,
        'available_bikes': available_bikes
    })
