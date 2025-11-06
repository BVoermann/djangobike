"""
Market Simulator for Singleplayer Sales

This module handles the deferred sales system where player sales decisions
are stored and then executed during month processing with market simulation.
"""

from django.db import transaction, models
from decimal import Decimal
import random
import logging

from .models import Market, SalesDecision, SalesOrder
from production.models import ProducedBike
from finance.models import Transaction
from competitors.models import AICompetitor, CompetitorSale, CompetitorProduction

logger = logging.getLogger(__name__)


class MarketSimulator:
    """
    Simulates market dynamics for singleplayer sales.

    Processes player SalesDecisions alongside AI competitor sales to determine
    which bikes actually sell based on supply/demand dynamics, pricing, and
    market characteristics.
    """

    def __init__(self, session):
        self.session = session

    def process_pending_sales_decisions(self, month, year):
        """
        Main entry point: Process all pending sales decisions for the current month.

        This is called from simulation/engine.py during process_month().
        """
        logger.info(f"Processing pending sales decisions for session {self.session.id}, month {month}/{year}")

        with transaction.atomic():
            # Get all unprocessed decisions for this session
            pending_decisions = SalesDecision.objects.filter(
                session=self.session,
                is_processed=False,
                decision_month__lte=month,
                decision_year__lte=year
            ).select_related('market', 'bike_type')

            if not pending_decisions.exists():
                logger.info("No pending sales decisions to process")
                return

            # Group decisions by market and bike type/segment
            market_segments = {}
            for decision in pending_decisions:
                key = (decision.market.id, decision.bike_type.id, decision.price_segment)
                if key not in market_segments:
                    market_segments[key] = []
                market_segments[key].append(decision)

            # Process each market segment
            for (market_id, bike_type_id, price_segment), decisions in market_segments.items():
                market = Market.objects.get(id=market_id)
                from bikeshop.models import BikeType
                bike_type = BikeType.objects.get(id=bike_type_id)

                self._process_market_segment(
                    market=market,
                    bike_type=bike_type,
                    price_segment=price_segment,
                    player_decisions=decisions,
                    month=month,
                    year=year
                )

    def _process_market_segment(self, market, bike_type, price_segment, player_decisions, month, year):
        """
        Process sales for a specific market/bike_type/segment combination.

        Implements supply/demand dynamics:
        - Collect all offers (player + AI competitors)
        - Calculate market demand considering location characteristics
        - Allocate sales based on price, quality, and random factors
        """
        logger.info(f"Processing market segment: {market.name} - {bike_type.name} ({price_segment})")

        # Calculate market demand for this segment
        base_demand = self._calculate_market_demand(market, bike_type, price_segment, month)
        logger.info(f"Base demand: {base_demand} bikes")

        # Collect all offers (player + competitors)
        all_offers = []

        # Add player offers
        for decision in player_decisions:
            # Find available bikes for this decision
            available_bikes = ProducedBike.objects.filter(
                session=self.session,
                bike_type=bike_type,
                price_segment=price_segment,
                is_sold=False
            )[:decision.quantity]

            if len(available_bikes) < decision.quantity:
                logger.warning(
                    f"Decision {decision.id}: Requested {decision.quantity} bikes but only {len(available_bikes)} available"
                )

            # Create offers for each bike
            for bike in available_bikes:
                # Apply aging penalty to effective price
                age_penalty = bike.get_age_penalty_factor() if hasattr(bike, 'get_age_penalty_factor') else 1.0
                effective_price = decision.desired_price * Decimal(str(age_penalty))

                all_offers.append({
                    'type': 'player',
                    'decision': decision,
                    'bike': bike,
                    'price': effective_price,
                    'transport_cost': decision.transport_cost,
                    'quality_factor': self._get_quality_factor(price_segment),
                })

        # Add competitor offers
        competitor_offers = self._collect_competitor_offers(market, bike_type, price_segment, month, year)
        all_offers.extend(competitor_offers)

        logger.info(f"Total offers: {len(all_offers)} ({len([o for o in all_offers if o['type'] == 'player'])} player, {len(competitor_offers)} competitor)")

        # Sort offers by effective price (lower prices sell first)
        # Add small random factor for realism (10% variance)
        for offer in all_offers:
            random_factor = random.uniform(0.95, 1.05)
            offer['sort_price'] = float(offer['price']) * random_factor / offer['quality_factor']

        all_offers.sort(key=lambda x: x['sort_price'])

        # Apply price elasticity - higher average prices reduce demand
        if all_offers:
            avg_price = sum(float(offer['price']) for offer in all_offers) / len(all_offers)
            # Simple elasticity model: for each 10% price increase above base, demand drops by elasticity_factor%
            base_price = self._get_base_price_for_segment(price_segment)
            price_ratio = avg_price / base_price if base_price > 0 else 1.0
            elasticity_adjustment = 1.0 - (price_ratio - 1.0) * market.price_elasticity_factor * 0.5
            elasticity_adjustment = max(0.3, min(1.5, elasticity_adjustment))  # Clamp between 30% and 150%
            adjusted_demand = int(base_demand * elasticity_adjustment)
            logger.info(f"Demand adjusted for price elasticity: {base_demand} -> {adjusted_demand} (avg price: {avg_price:.2f}€, elasticity: {elasticity_adjustment:.2f})")
        else:
            adjusted_demand = base_demand

        # Allocate sales based on demand
        bikes_to_sell = min(len(all_offers), adjusted_demand)
        logger.info(f"Allocating {bikes_to_sell} sales out of {len(all_offers)} offers (demand: {adjusted_demand})")

        # Execute sales for the top offers
        for i, offer in enumerate(all_offers[:bikes_to_sell]):
            if offer['type'] == 'player':
                self._execute_player_sale(offer, month, year)
            else:
                self._execute_competitor_sale(offer, month, year)

        # Mark remaining offers as unsold
        oversaturated_count = len(all_offers) - bikes_to_sell
        if oversaturated_count > 0:
            logger.info(f"Market oversaturated: {oversaturated_count} bikes did not sell")

        for offer in all_offers[bikes_to_sell:]:
            if offer['type'] == 'player':
                decision = offer['decision']
                # Update decision statistics but don't mark as fully processed yet
                # We'll mark as processed after aggregating all results
                if not hasattr(decision, '_temp_sold_count'):
                    decision._temp_sold_count = 0
                if not hasattr(decision, '_temp_unsold_count'):
                    decision._temp_unsold_count = 0
                decision._temp_unsold_count += 1

        # Mark all player decisions as processed and update results
        for decision in player_decisions:
            sold_count = getattr(decision, '_temp_sold_count', 0)
            unsold_count = getattr(decision, '_temp_unsold_count', 0)

            decision.quantity_sold = sold_count
            decision.is_processed = True

            if unsold_count > 0:
                if sold_count == 0:
                    decision.unsold_reason = 'market_oversaturated'
                else:
                    decision.unsold_reason = 'partially_sold_market_oversaturated'

            decision.save()
            logger.info(
                f"Decision {decision.id} processed: {sold_count}/{decision.quantity} sold"
                + (f" ({decision.unsold_reason})" if decision.unsold_reason else "")
            )

    def _calculate_market_demand(self, market, bike_type, price_segment, month):
        """
        Calculate market demand for a specific bike type/segment.

        Considers:
        - Market's monthly_volume_capacity
        - Location characteristics (e.g., green_city_factor for e-bikes)
        - Segment-specific demand distribution
        - Seasonal factors
        """
        # Base capacity
        base_capacity = market.monthly_volume_capacity

        # Adjust for bike type based on location characteristics
        bike_type_multiplier = market.get_bike_type_demand_multiplier(bike_type.name)

        # Segment distribution (simpler segments have higher demand)
        segment_distribution = {
            'cheap': 0.4,      # 40% of market
            'standard': 0.4,   # 40% of market
            'premium': 0.2     # 20% of market
        }
        segment_factor = segment_distribution.get(price_segment, 0.33)

        # Seasonal adjustment
        seasonal_factor = self._get_seasonal_factor(bike_type.name, month)

        # Calculate final demand
        demand = int(base_capacity * bike_type_multiplier * segment_factor * seasonal_factor)

        logger.debug(
            f"Demand calculation: base={base_capacity}, bike_type_mult={bike_type_multiplier:.2f}, "
            f"segment={segment_factor:.2f}, seasonal={seasonal_factor:.2f}, final={demand}"
        )

        return max(1, demand)  # Ensure at least 1 bike can be sold

    def _get_seasonal_factor(self, bike_type_name, month):
        """Get seasonal demand adjustment factor"""
        bike_type_lower = bike_type_name.lower()

        # Mountain bikes peak in summer
        if 'mountain' in bike_type_lower or 'mtb' in bike_type_lower:
            if month in [5, 6, 7, 8]:  # May-August
                return 1.3
            elif month in [11, 12, 1, 2]:  # Winter
                return 0.7

        # Road/Racing bikes peak in spring/summer
        if 'road' in bike_type_lower or 'racing' in bike_type_lower or 'rennrad' in bike_type_lower:
            if month in [4, 5, 6, 7, 8]:  # April-August
                return 1.2
            elif month in [11, 12, 1, 2]:  # Winter
                return 0.8

        # E-bikes have steadier demand but peak in fall
        if 'e-' in bike_type_lower or 'elektro' in bike_type_lower:
            if month in [9, 10]:  # September-October
                return 1.2
            elif month in [12, 1, 2]:  # Winter
                return 0.9

        # City bikes are relatively stable year-round
        return 1.0

    def _get_base_price_for_segment(self, price_segment):
        """Get base price for a segment for elasticity calculations"""
        base_prices = {
            'cheap': 400,
            'standard': 700,
            'premium': 1200
        }
        return base_prices.get(price_segment, 700)

    def _get_quality_factor(self, price_segment):
        """Get quality factor based on price segment (higher = better quality)"""
        quality_factors = {
            'cheap': 0.8,
            'standard': 1.0,
            'premium': 1.3
        }
        return quality_factors.get(price_segment, 1.0)

    def _collect_competitor_offers(self, market, bike_type, price_segment, month, year):
        """Collect competitor sales offers for this market segment"""
        offers = []

        # Get all competitors with inventory for this segment
        competitor_productions = CompetitorProduction.objects.filter(
            competitor__session=self.session,
            bike_type=bike_type,
            price_segment=price_segment,
            quantity_in_inventory__gt=0
        ).select_related('competitor')

        for production in competitor_productions:
            competitor = production.competitor

            # Determine how many bikes competitor will offer
            max_offer = min(
                production.quantity_in_inventory,
                random.randint(1, max(1, production.quantity_in_inventory // 2 + 1))
            )

            if max_offer <= 0:
                continue

            # Calculate offering price
            base_price = self._calculate_competitor_base_price(production, market)
            age_penalty = production.get_inventory_age_penalty()
            strategy_adjustment = competitor.get_price_adjustment_factor()
            price_variation = random.uniform(0.95, 1.05)

            final_price = base_price * Decimal(str(age_penalty)) * Decimal(str(strategy_adjustment)) * Decimal(str(price_variation))

            # Quality factor
            quality_factor = self._get_competitor_quality_factor(competitor, price_segment)

            for _ in range(max_offer):
                offers.append({
                    'type': 'competitor',
                    'competitor': competitor,
                    'production': production,
                    'price': final_price,
                    'transport_cost': market.transport_cost_foreign,
                    'quality_factor': quality_factor,
                })

        return offers

    def _calculate_competitor_base_price(self, production, market):
        """Calculate base price for competitor offering"""
        base_cost = production.production_cost_per_unit

        # Apply markup based on segment
        segment_markups = {
            'cheap': 1.2,
            'standard': 1.5,
            'premium': 2.0
        }

        markup = segment_markups.get(production.price_segment, 1.5)
        base_price = base_cost * Decimal(str(markup))

        # Add transport costs
        base_price += market.transport_cost_foreign

        return base_price

    def _get_competitor_quality_factor(self, competitor, segment):
        """Get quality factor for competitor based on efficiency and strategy"""
        base_quality = competitor.efficiency

        # Strategy adjustments
        strategy_quality_bonus = {
            'cheap_only': 0.9,
            'balanced': 1.0,
            'premium_focus': 1.2,
            'e_bike_specialist': 1.1
        }

        strategy_bonus = strategy_quality_bonus.get(competitor.strategy, 1.0)
        final_quality = base_quality * strategy_bonus

        # Segment-specific adjustments
        if segment == 'premium' and competitor.strategy != 'premium_focus':
            final_quality *= 0.9
        elif segment == 'cheap' and competitor.strategy != 'cheap_only':
            final_quality *= 0.95

        return final_quality

    def _execute_player_sale(self, offer, month, year):
        """Execute a successful player sale"""
        decision = offer['decision']
        bike = offer['bike']

        # Track sold count on decision
        if not hasattr(decision, '_temp_sold_count'):
            decision._temp_sold_count = 0
        decision._temp_sold_count += 1

        # Transport cost is per shipment, not per bike
        # Only apply it on the first bike sold in this decision
        transport_cost_for_this_bike = Decimal('0')
        if decision._temp_sold_count == 1:
            # First bike sold - apply the one-time transport cost
            transport_cost_for_this_bike = offer['transport_cost']

        # Create sales order
        sales_order = SalesOrder.objects.create(
            session=self.session,
            market=decision.market,
            bike=bike,
            sale_month=month,
            sale_year=year,
            sale_price=offer['price'],
            transport_cost=transport_cost_for_this_bike,  # Only first bike has transport cost
            is_completed=True
        )

        # Mark bike as sold
        bike.is_sold = True
        bike.save()

        # Calculate revenue (only first bike pays transport)
        revenue = offer['price'] - transport_cost_for_this_bike

        # Update session balance
        self.session.balance += revenue
        self.session.save()

        # Update decision actual revenue
        decision.actual_revenue += revenue
        decision.save()

        # Create transaction record
        Transaction.objects.create(
            session=self.session,
            transaction_type='income',
            category='Verkäufe',
            amount=revenue,
            description=f'Verkauf {bike.bike_type.name} ({bike.get_price_segment_display()}) an {decision.market.name}',
            month=month,
            year=year
        )

        logger.debug(f"Player sale executed: {bike.bike_type.name} for {offer['price']}€ (net: {revenue}€)")

    def _execute_competitor_sale(self, offer, month, year):
        """Execute a successful competitor sale"""
        competitor = offer['competitor']
        production = offer['production']

        # Update production inventory
        production.quantity_in_inventory -= 1
        production.save()

        # Create competitor sale record
        from sales.models import Market
        market = Market.objects.filter(session=self.session).first()  # Simplified for now

        CompetitorSale.objects.create(
            competitor=competitor,
            market=market,
            bike_type=production.bike_type,
            price_segment=production.price_segment,
            month=month,
            year=year,
            quantity_offered=1,
            quantity_sold=1,
            sale_price=offer['price'],
            total_revenue=offer['price']
        )

        # Update competitor statistics
        competitor.total_bikes_sold += 1
        competitor.total_revenue += offer['price']
        competitor.save()

        logger.debug(f"Competitor sale executed: {competitor.name} - {production.bike_type.name} for {offer['price']}€")

    def get_pending_decisions_summary(self):
        """Get summary of pending sales decisions for UI feedback"""
        pending = SalesDecision.objects.filter(
            session=self.session,
            is_processed=False
        ).select_related('market', 'bike_type')

        summary = {
            'total_quantity': sum(d.quantity for d in pending),
            'total_expected_revenue': sum(d.quantity * (d.desired_price - d.transport_cost) for d in pending),
            'by_market': {},
        }

        for decision in pending:
            market_name = decision.market.name
            if market_name not in summary['by_market']:
                summary['by_market'][market_name] = {
                    'quantity': 0,
                    'expected_revenue': 0,
                    'bikes': []
                }

            expected_revenue = decision.quantity * (decision.desired_price - decision.transport_cost)
            summary['by_market'][market_name]['quantity'] += decision.quantity
            summary['by_market'][market_name]['expected_revenue'] += expected_revenue
            summary['by_market'][market_name]['bikes'].append({
                'bike_type': decision.bike_type.name,
                'segment': decision.get_price_segment_display(),
                'quantity': decision.quantity,
                'price': decision.desired_price,
                'expected_revenue': expected_revenue,
            })

        return summary

    def get_recent_sales_results(self, months_back=1):
        """Get results of recently processed sales decisions for feedback"""
        recent_decisions = SalesDecision.objects.filter(
            session=self.session,
            is_processed=True,
            decision_month__gte=self.session.current_month - months_back
        ).select_related('market', 'bike_type').order_by('-created_at')

        results = []
        for decision in recent_decisions:
            results.append({
                'market': decision.market.name,
                'bike_type': decision.bike_type.name,
                'segment': decision.get_price_segment_display(),
                'quantity_planned': decision.quantity,
                'quantity_sold': decision.quantity_sold,
                'desired_price': decision.desired_price,
                'actual_revenue': decision.actual_revenue,
                'unsold_reason': decision.unsold_reason,
                'success_rate': (decision.quantity_sold / decision.quantity * 100) if decision.quantity > 0 else 0,
            })

        return results
