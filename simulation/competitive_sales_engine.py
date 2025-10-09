from django.db import models, transaction
from decimal import Decimal
import random
from sales.models import Market, SalesOrder
from competitors.models import AICompetitor, CompetitorSale, CompetitorProduction, MarketCompetition
from production.models import ProducedBike
from finance.models import Transaction
from .market_volume_engine import MarketVolumeEngine


class CompetitiveSalesEngine:
    """Engine for processing competitive sales with market volume constraints"""
    
    def __init__(self, session):
        self.session = session
        self.market_engine = MarketVolumeEngine(session)
    
    def process_competitive_sales(self, month, year):
        """Process sales for all competitors and players with market competition"""
        with transaction.atomic():
            # Update market volumes for this period
            self.market_engine.calculate_market_volume_for_period(month, year)
            
            # Update inventory aging for all bikes
            self._update_all_inventory_ages(month, year)
            
            # Process competitive sales for each market/bike/segment combination
            markets = Market.objects.filter(session=self.session)
            from bikeshop.models import BikeType
            bike_types = BikeType.objects.filter(session=self.session)
            
            for market in markets:
                for bike_type in bike_types:
                    for segment in ['cheap', 'standard', 'premium']:
                        self._process_competitive_segment_sales(market, bike_type, segment, month, year)
    
    def _update_all_inventory_ages(self, month, year):
        """Update inventory ages for all unsold bikes"""
        # Update player inventory
        unsold_bikes = ProducedBike.objects.filter(
            session=self.session,
            is_sold=False
        )
        
        for bike in unsold_bikes:
            bike.update_inventory_age(month, year)
        
        # Update competitor inventory
        competitor_productions = CompetitorProduction.objects.filter(
            competitor__session=self.session,
            quantity_in_inventory__gt=0
        )
        
        for production in competitor_productions:
            production.update_inventory_age(month, year)
    
    def _process_competitive_segment_sales(self, market, bike_type, segment, month, year):
        """Process sales for a specific market/bike/segment with competitive allocation"""
        # Get market competition data
        try:
            competition = MarketCompetition.objects.get(
                session=self.session,
                market=market,
                bike_type=bike_type,
                price_segment=segment,
                month=month,
                year=year
            )
        except MarketCompetition.DoesNotExist:
            # Create if not exists
            competition = self.market_engine._calculate_segment_volume(market, bike_type, segment, month, year)
        
        # Collect all offers (player + competitors)
        offers = []
        
        # Add player offers
        player_offers = self._collect_player_offers(market, bike_type, segment, month, year)
        offers.extend(player_offers)
        
        # Add competitor offers
        competitor_offers = self._collect_competitor_offers(market, bike_type, segment, month, year)
        offers.extend(competitor_offers)
        
        if not offers:
            return
        
        # Distribute market demand among offers
        allocations = self.market_engine.distribute_market_demand(competition, offers)
        
        # Process allocations
        total_sold = 0
        for allocation in allocations:
            if allocation['quantity_allocated'] > 0:
                total_sold += allocation['quantity_allocated']
                self._execute_sale(allocation, market, bike_type, segment, month, year)
        
        # Update market competition with actual results
        competition.actual_sales_volume = total_sold
        competition.total_supply = sum(offer['quantity'] for offer in offers)
        
        # Calculate new saturation and price pressure
        if competition.maximum_market_volume > 0:
            competition.saturation_level = competition.total_supply / competition.maximum_market_volume
        else:
            competition.saturation_level = 1.0
        
        # Calculate average price
        if offers:
            total_value = sum(float(offer['price']) * offer['quantity'] for offer in offers)
            total_quantity = sum(offer['quantity'] for offer in offers)
            if total_quantity > 0:
                competition.average_price = Decimal(str(total_value / total_quantity))
        
        # Price pressure based on oversupply
        if competition.saturation_level > 1.0:
            competition.price_pressure = -min(0.5, (competition.saturation_level - 1.0) * 0.3)
        else:
            competition.price_pressure = (1.0 - competition.saturation_level) * 0.2
        
        competition.save()
    
    def _collect_player_offers(self, market, bike_type, segment, month, year):
        """Collect player sales offers for this market segment"""
        offers = []
        
        # Find player sales orders for this segment
        player_orders = SalesOrder.objects.filter(
            session=self.session,
            market=market,
            bike__bike_type=bike_type,
            bike__price_segment=segment,
            sale_month__lte=month,
            sale_year=year,
            is_completed=False
        )
        
        for order in player_orders:
            # Apply aging penalty to price
            age_penalty = order.bike.get_age_penalty_factor()
            effective_price = order.sale_price * Decimal(str(age_penalty))
            
            # Quality factor based on price segment
            quality_factor = self._get_quality_factor(order.bike.price_segment)
            
            offers.append({
                'seller': 'player',
                'seller_id': None,
                'order_id': order.id,
                'quantity': 1,  # Each order is for one bike
                'price': effective_price,
                'quality_factor': quality_factor,
                'bike_id': order.bike.id
            })
        
        return offers
    
    def _collect_competitor_offers(self, market, bike_type, segment, month, year):
        """Collect competitor sales offers for this market segment"""
        offers = []
        
        # Get all competitors with inventory for this segment
        competitor_productions = CompetitorProduction.objects.filter(
            competitor__session=self.session,
            bike_type=bike_type,
            price_segment=segment,
            quantity_in_inventory__gt=0
        )
        
        for production in competitor_productions:
            competitor = production.competitor
            
            # Calculate offering quantity (competitors may offer partial inventory)
            max_offer = min(
                production.quantity_in_inventory,
                random.randint(1, max(1, production.quantity_in_inventory // 2 + 1))
            )
            
            if max_offer <= 0:
                continue
            
            # Calculate offering price with strategy and aging adjustments
            base_price = self._calculate_competitor_base_price(production, market)
            age_penalty = production.get_inventory_age_penalty()
            strategy_adjustment = competitor.get_price_adjustment_factor()
            
            # Add some random variation
            price_variation = random.uniform(0.95, 1.05)
            
            final_price = base_price * Decimal(str(age_penalty)) * Decimal(str(strategy_adjustment)) * Decimal(str(price_variation))
            
            # Quality factor based on competitor efficiency and strategy
            quality_factor = self._get_competitor_quality_factor(competitor, segment)
            
            offers.append({
                'seller': 'competitor',
                'seller_id': competitor.id,
                'production_id': production.id,
                'quantity': max_offer,
                'price': final_price,
                'quality_factor': quality_factor,
                'competitor': competitor
            })
        
        return offers
    
    def _calculate_competitor_base_price(self, production, market):
        """Calculate base price for competitor offering"""
        # Use production cost as baseline
        base_cost = production.production_cost_per_unit
        
        # Apply markup based on segment
        segment_markups = {
            'cheap': 1.2,     # 20% markup
            'standard': 1.5,  # 50% markup
            'premium': 2.0    # 100% markup
        }
        
        markup = segment_markups.get(production.price_segment, 1.5)
        base_price = base_cost * Decimal(str(markup))
        
        # Add transport costs
        if hasattr(market, 'transport_cost_foreign'):
            transport_cost = market.transport_cost_foreign  # Assume competitors are foreign
            base_price += transport_cost
        
        return base_price
    
    def _get_quality_factor(self, price_segment):
        """Get quality factor based on price segment"""
        quality_factors = {
            'cheap': 0.8,     # Lower quality
            'standard': 1.0,  # Standard quality
            'premium': 1.3    # Higher quality
        }
        return quality_factors.get(price_segment, 1.0)
    
    def _get_competitor_quality_factor(self, competitor, segment):
        """Get quality factor for competitor based on efficiency and strategy"""
        base_quality = competitor.efficiency  # 0.7 = 0.7 quality factor
        
        # Strategy adjustments
        strategy_quality_bonus = {
            'cheap_only': 0.9,      # Focuses on low cost, lower quality
            'balanced': 1.0,        # Balanced approach
            'premium_focus': 1.2,   # Higher quality focus
            'e_bike_specialist': 1.1 # Specialized quality
        }
        
        strategy_bonus = strategy_quality_bonus.get(competitor.strategy, 1.0)
        final_quality = base_quality * strategy_bonus
        
        # Segment-specific adjustments
        if segment == 'premium' and competitor.strategy != 'premium_focus':
            final_quality *= 0.9  # Not specialized in premium
        elif segment == 'cheap' and competitor.strategy != 'cheap_only':
            final_quality *= 0.95  # Not specialized in cheap
        
        return final_quality
    
    def _execute_sale(self, allocation, market, bike_type, segment, month, year):
        """Execute a successful sale allocation"""
        if allocation['seller'] == 'player':
            self._execute_player_sale(allocation, month, year)
        elif allocation['seller'] == 'competitor':
            self._execute_competitor_sale(allocation, market, bike_type, segment, month, year)
    
    def _execute_player_sale(self, allocation, month, year):
        """Execute player sale"""
        try:
            order = SalesOrder.objects.get(id=allocation['order_id'])
            
            # Mark order as completed
            order.is_completed = True
            order.save()
            
            # Mark bike as sold
            if allocation.get('bike_id'):
                try:
                    bike = ProducedBike.objects.get(id=allocation['bike_id'])
                    bike.is_sold = True
                    bike.save()
                except ProducedBike.DoesNotExist:
                    pass
            
            # Calculate revenue (price already includes aging penalty)
            revenue = allocation['price'] - order.transport_cost
            
            # Update session balance
            self.session.balance += revenue
            self.session.save()
            
            # Create transaction record
            Transaction.objects.create(
                session=self.session,
                transaction_type='income',
                category='Verkäufe',
                amount=revenue,
                description=f'Verkauf {order.bike.bike_type.name} in {order.market.name}',
                month=month,
                year=year
            )
            
        except SalesOrder.DoesNotExist:
            pass
    
    def _execute_competitor_sale(self, allocation, market, bike_type, segment, month, year):
        """Execute competitor sale"""
        try:
            if 'production_id' not in allocation:
                print(f"Warning: No production_id in allocation: {allocation}")
                return
            
            production = CompetitorProduction.objects.get(id=allocation['production_id'])
            competitor = allocation['competitor']
            
            quantity_sold = allocation['quantity_allocated']
            sale_price = allocation['price']
            
            # Update production inventory
            production.quantity_in_inventory -= quantity_sold
            production.save()
            
            # Create competitor sale record
            CompetitorSale.objects.create(
                competitor=competitor,
                market=market,
                bike_type=bike_type,
                price_segment=segment,
                month=month,
                year=year,
                quantity_offered=allocation['quantity'],
                quantity_sold=quantity_sold,
                sale_price=sale_price,
                total_revenue=sale_price * quantity_sold
            )
            
            # Update competitor statistics
            competitor.total_bikes_sold += quantity_sold
            competitor.total_revenue += sale_price * quantity_sold
            competitor.save()
            
        except CompetitorProduction.DoesNotExist:
            pass
    
    def get_market_competition_data(self, market, bike_type, segment, month, year):
        """Get market competition data for analysis"""
        try:
            competition = MarketCompetition.objects.get(
                session=self.session,
                market=market,
                bike_type=bike_type,
                price_segment=segment,
                month=month,
                year=year
            )
            
            # Get all sales in this segment
            competitor_sales = CompetitorSale.objects.filter(
                competitor__session=self.session,
                market=market,
                bike_type=bike_type,
                price_segment=segment,
                month=month,
                year=year
            )
            
            player_sales = SalesOrder.objects.filter(
                session=self.session,
                market=market,
                bike__bike_type=bike_type,
                bike__price_segment=segment,
                sale_month=month,
                sale_year=year,
                is_completed=True
            )
            
            return {
                'competition': competition,
                'competitor_sales': competitor_sales,
                'player_sales': player_sales,
                'total_competitor_sales': sum(s.quantity_sold for s in competitor_sales),
                'total_player_sales': player_sales.count(),
                'market_share_player': player_sales.count() / max(1, competition.actual_sales_volume),
                'average_competitor_price': competitor_sales.aggregate(
                    avg=models.Avg('sale_price')
                )['avg'] or 0
            }
            
        except MarketCompetition.DoesNotExist:
            return None