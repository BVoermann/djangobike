from django.db import transaction, models
from bikeshop.models import GameSession, BikeType, BikePrice
from sales.models import Market, MarketDemand, MarketPriceSensitivity
from .models import (
    AICompetitor, CompetitorProduction, CompetitorSale, 
    MarketCompetition, CompetitorStrategy
)
from decimal import Decimal
import random
import math


class CompetitorAIEngine:
    """AI-Engine für Konkurrentenverhalten"""
    
    def __init__(self, session):
        self.session = session
    
    def process_competitor_month(self):
        """Verarbeitet einen Monat für alle Konkurrenten"""
        with transaction.atomic():
            # 1. Update inventory ages
            self._update_competitor_inventory_ages()
            
            # 2. Alle Konkurrenten planen Produktion
            self._plan_competitor_production()
            
            # 3. Handle excess inventory (clearance sales, etc.)
            self._handle_excess_inventory()
            
            # 4. Alle 3 Monate: Verkäufe verarbeiten
            if self.session.current_month % 3 == 0:
                self._process_competitor_sales()
                self._update_market_competition()
    
    def _update_competitor_inventory_ages(self):
        """Update inventory ages for all competitor productions"""
        productions = CompetitorProduction.objects.filter(
            competitor__session=self.session,
            quantity_in_inventory__gt=0
        )
        
        for production in productions:
            production.update_inventory_age(self.session.current_month, self.session.current_year)
    
    def _handle_excess_inventory(self):
        """Handle aged inventory with clearance strategies"""
        old_productions = CompetitorProduction.objects.filter(
            competitor__session=self.session,
            quantity_in_inventory__gt=0,
            months_in_inventory__gte=6  # 6+ months old
        )
        
        for production in old_productions:
            competitor = production.competitor
            
            # Aggressive competitors liquidate old inventory
            if competitor.aggressiveness > 0.6:
                liquidation_rate = random.uniform(0.6, 0.9)
                liquidated_quantity = int(production.quantity_in_inventory * liquidation_rate)
                
                if liquidated_quantity > 0:
                    production.quantity_in_inventory -= liquidated_quantity
                    production.save()
                    
                    # Record as lost inventory (no revenue, just clear it)
                    competitor.financial_resources -= production.production_cost_per_unit * liquidated_quantity * Decimal('0.3')
                    competitor.save()
            
            # Conservative competitors keep inventory longer but mark down prices more
            elif competitor.aggressiveness < 0.4:
                # They will rely on the age penalty system to gradually reduce prices
                pass
    
    def _plan_competitor_production(self):
        """Plant Produktion für alle Konkurrenten"""
        competitors = AICompetitor.objects.filter(session=self.session)
        bike_types = BikeType.objects.filter(session=self.session)
        
        for competitor in competitors:
            self._plan_production_for_competitor(competitor, bike_types)
    
    def _plan_production_for_competitor(self, competitor, bike_types):
        """Plant Produktion für einen einzelnen Konkurrenten"""
        capacity = competitor.get_production_capacity()
        
        # Strategie-spezifische Präferenzen
        type_preferences = CompetitorStrategy.get_bike_type_preferences(
            competitor.strategy, bike_types
        )
        segment_preferences = CompetitorStrategy.get_price_segment_preferences(
            competitor.strategy
        )
        
        # Verteilung der Kapazität auf verschiedene Bikes
        remaining_capacity = capacity
        
        # Sortiere Bike-Types nach Präferenz
        sorted_types = sorted(
            bike_types, 
            key=lambda bt: type_preferences.get(bt.id, 0) * random.uniform(0.8, 1.2),
            reverse=True
        )
        
        for bike_type in sorted_types:
            if remaining_capacity <= 0:
                break
                
            type_preference = type_preferences.get(bike_type.id, 0.5)
            if random.random() > type_preference:
                continue
            
            # Kapazität für diesen Bike-Type
            type_capacity = min(
                remaining_capacity,
                int(capacity * type_preference * random.uniform(0.3, 0.8))
            )
            
            if type_capacity < 1:
                continue
            
            # Verteilung auf Preissegmente
            self._distribute_production_by_segments(
                competitor, bike_type, type_capacity, segment_preferences
            )
            
            remaining_capacity -= type_capacity
    
    def _distribute_production_by_segments(self, competitor, bike_type, capacity, segment_preferences):
        """Verteilt Produktionskapazität auf Preissegmente"""
        segments = ['cheap', 'standard', 'premium']
        
        for segment in segments:
            segment_preference = segment_preferences.get(segment, 0.3)
            
            if random.random() > segment_preference:
                continue
            
            segment_capacity = int(capacity * segment_preference * random.uniform(0.5, 1.5))
            segment_capacity = min(segment_capacity, capacity)
            
            if segment_capacity < 1:
                continue
            
            production_cost = CompetitorStrategy.calculate_production_cost(
                bike_type, competitor.strategy, competitor.efficiency
            )
            
            # Erstelle Produktionsplan
            production, created = CompetitorProduction.objects.get_or_create(
                competitor=competitor,
                bike_type=bike_type,
                price_segment=segment,
                month=self.session.current_month,
                year=self.session.current_year,
                defaults={
                    'quantity_planned': segment_capacity,
                    'production_cost_per_unit': production_cost
                }
            )
            
            if not created:
                production.quantity_planned += segment_capacity
                production.save()
            
            # Simuliere erfolgreiche Produktion
            success_rate = competitor.efficiency * random.uniform(0.8, 1.0)
            actual_production = int(segment_capacity * success_rate)
            production.quantity_produced = actual_production
            
            # Initialize inventory with produced quantity
            production.quantity_in_inventory = actual_production
            production.months_in_inventory = 0
            production.save()
            
            # Update Competitor Stats
            competitor.total_bikes_produced += actual_production
            competitor.save()
    
    def _process_competitor_sales(self):
        """Verarbeitet Verkäufe aller Konkurrenten"""
        competitors = AICompetitor.objects.filter(session=self.session)
        markets = Market.objects.filter(session=self.session)
        
        # Bereite Marktdaten vor
        self._prepare_market_demand_data(markets)
        
        for competitor in competitors:
            self._process_sales_for_competitor(competitor, markets)
    
    def _prepare_market_demand_data(self, markets):
        """Berechnet geschätzte Nachfrage für alle Märkte"""
        bike_types = BikeType.objects.filter(session=self.session)
        segments = ['cheap', 'standard', 'premium']
        
        for market in markets:
            for bike_type in bike_types:
                for segment in segments:
                    # Basis-Nachfrage (vereinfacht)
                    base_demand = self._calculate_base_demand(market, bike_type, segment)
                    
                    competition, created = MarketCompetition.objects.get_or_create(
                        session=self.session,
                        market=market,
                        bike_type=bike_type,
                        price_segment=segment,
                        month=self.session.current_month,
                        year=self.session.current_year,
                        defaults={'estimated_demand': base_demand}
                    )
    
    def _calculate_base_demand(self, market, bike_type, segment):
        """Berechnet Basis-Nachfrage für Markt/Bike/Segment"""
        # Saisonale Faktoren
        seasonal_factor = self._get_seasonal_demand_factor(bike_type.name)
        
        # Segment-Faktoren
        segment_factors = {'cheap': 0.5, 'standard': 0.3, 'premium': 0.2}
        segment_factor = segment_factors.get(segment, 0.3)
        
        # Basis-Nachfrage (vereinfacht, könnte aus MarketDemand kommen)
        base = random.randint(20, 80)
        
        return int(base * seasonal_factor * segment_factor)
    
    def _get_seasonal_demand_factor(self, bike_type_name):
        """Gibt saisonale Nachfrage-Faktoren zurück"""
        month = self.session.current_month
        name = bike_type_name.lower()
        
        # Mountainbikes im Sommer
        if 'mountain' in name and month in [5, 6, 7, 8]:
            return 1.5
        
        # E-Bikes im Herbst/Frühling
        if 'e-' in name and month in [3, 4, 9, 10]:
            return 1.3
        
        # City-Bikes ganzjährig stabil
        if 'city' in name:
            return 1.1
        
        # Winter-Flaute für die meisten Bikes
        if month in [12, 1, 2]:
            return 0.7
        
        return 1.0
    
    def _process_sales_for_competitor(self, competitor, markets):
        """Verarbeitet Verkäufe für einen Konkurrenten"""
        # Hole alle Produktionen der letzten 3 Monate
        productions = CompetitorProduction.objects.filter(
            competitor=competitor,
            month__in=self._get_last_three_months(),
            year=self.session.current_year,
            quantity_produced__gt=0
        )
        
        for production in productions:
            for market in markets:
                if random.random() < 0.7:  # 70% Chance auf Marktpräsenz
                    self._attempt_sale(competitor, production, market)
    
    def _get_last_three_months(self):
        """Gibt die letzten 3 Monate zurück"""
        current = self.session.current_month
        if current >= 3:
            return [current-2, current-1, current]
        elif current == 2:
            return [12, 1, 2]  # Jahr-übergreifend
        else:  # current == 1
            return [11, 12, 1]
    
    def _attempt_sale(self, competitor, production, market):
        """Versucht Verkauf in einem Markt"""
        # Check if there's inventory to sell
        if production.quantity_in_inventory <= 0:
            return
        
        # Berechne Verkaufspreis mit erweiterten Faktoren
        base_price = self._get_base_price(production.bike_type, production.price_segment)
        
        # Strategy-based price adjustment
        strategy_factor = competitor.get_price_adjustment_factor()
        
        # Inventory aging penalty
        age_penalty = production.get_inventory_age_penalty()
        
        # Market competition adjustment
        market_factor = self._get_market_competition_factor(market, production.bike_type, production.price_segment)
        
        # Aggressive pricing if competitor is aggressive
        aggression_factor = 1.0 - (competitor.aggressiveness * 0.1)
        
        # Calculate final price
        sale_price = (base_price * 
                     Decimal(str(strategy_factor)) * 
                     Decimal(str(age_penalty)) * 
                     Decimal(str(market_factor)) * 
                     Decimal(str(aggression_factor)))
        
        # Add random variation (smaller for premium strategies)
        if competitor.strategy == 'premium_focus':
            variation_range = (0.98, 1.02)  # Less price variation for premium
        else:
            variation_range = (0.92, 1.08)  # More variation for other strategies
        
        sale_price = sale_price * Decimal(str(random.uniform(*variation_range)))
        
        # Bestimme Angebotsmenge based on inventory and strategy
        max_inventory_offer = production.quantity_in_inventory
        
        # Strategy-based quantity decisions
        if competitor.strategy == 'cheap_only':
            # Cheap strategy: offer more to move inventory quickly
            quantity_factor = random.uniform(0.6, 1.0)
        elif competitor.strategy == 'premium_focus':
            # Premium strategy: offer less to maintain exclusivity
            quantity_factor = random.uniform(0.3, 0.7)
        else:
            # Balanced strategies
            quantity_factor = random.uniform(0.4, 0.8)
        
        # Increase offer if inventory is aging
        if production.months_in_inventory > 3:
            quantity_factor = min(1.0, quantity_factor * 1.5)  # More aggressive with old inventory
        
        max_offer = max(1, int(max_inventory_offer * quantity_factor))
        max_offer = min(max_offer, max_inventory_offer)
        
        if max_offer < 1:
            return
        
        # Hole oder erstelle Market Competition
        competition = MarketCompetition.objects.filter(
            session=self.session,
            market=market,
            bike_type=production.bike_type,
            price_segment=production.price_segment,
            month=self.session.current_month,
            year=self.session.current_year
        ).first()
        
        if not competition:
            return
        
        # Berechne Verkaufserfolg
        success_rate = self._calculate_sale_success_rate(
            competitor, production, market, competition, sale_price
        )
        
        actual_sold = int(max_offer * success_rate)
        actual_sold = min(actual_sold, competition.estimated_demand)
        
        if actual_sold > 0:
            # Erstelle Verkauf
            CompetitorSale.objects.create(
                competitor=competitor,
                market=market,
                bike_type=production.bike_type,
                price_segment=production.price_segment,
                month=self.session.current_month,
                year=self.session.current_year,
                quantity_offered=max_offer,
                quantity_sold=actual_sold,
                sale_price=sale_price,
                total_revenue=sale_price * actual_sold
            )
            
            # Update Competitor Stats
            competitor.total_bikes_sold += actual_sold
            competitor.total_revenue += sale_price * actual_sold
            competitor.save()
            
            # Update Production inventory
            production.quantity_in_inventory -= actual_sold
            production.save()
    
    def _get_base_price(self, bike_type, price_segment):
        """Holt Basis-Verkaufspreis"""
        try:
            bike_price = BikePrice.objects.get(
                session=self.session,
                bike_type=bike_type,
                price_segment=price_segment
            )
            return bike_price.price
        except BikePrice.DoesNotExist:
            # Fallback: Schätze Preis basierend auf Produktionskosten
            base_cost = CompetitorStrategy.calculate_production_cost(
                bike_type, 'balanced', 0.7
            )
            multipliers = {'cheap': 1.3, 'standard': 1.6, 'premium': 2.2}
            return base_cost * Decimal(str(multipliers.get(price_segment, 1.5)))
    
    def _calculate_sale_success_rate(self, competitor, production, market, competition, sale_price):
        """Berechnet Verkaufserfolgsrate"""
        # Basis-Rate
        base_rate = 0.6
        
        # Marktpräsenz-Bonus
        presence_bonus = competitor.market_presence / 100 * 0.3
        
        # Aggressivitäts-Bonus
        aggression_bonus = competitor.aggressiveness * 0.2
        
        # Preis-Faktor (vereinfacht)
        base_price = self._get_base_price(production.bike_type, production.price_segment)
        if base_price > 0:
            price_factor = float(base_price / sale_price) - 1.0
            price_factor = max(-0.3, min(0.3, price_factor))  # Begrenze auf ±30%
        else:
            price_factor = 0
        
        # Sättigungs-Malus
        saturation_penalty = competition.saturation_level * 0.4
        
        total_rate = base_rate + presence_bonus + aggression_bonus + price_factor - saturation_penalty
        return max(0.1, min(0.9, total_rate))  # Zwischen 10% und 90%
    
    def _get_market_competition_factor(self, market, bike_type, price_segment):
        """Calculate pricing adjustment based on market competition"""
        try:
            competition = MarketCompetition.objects.get(
                session=self.session,
                market=market,
                bike_type=bike_type,
                price_segment=price_segment,
                month=self.session.current_month,
                year=self.session.current_year
            )
            
            # If market is oversaturated, reduce prices
            if competition.saturation_level > 1.0:
                # More competition = lower prices
                saturation_penalty = min(0.25, (competition.saturation_level - 1.0) * 0.2)
                return 1.0 - saturation_penalty
            
            # If market is undersaturated, can charge premium
            elif competition.saturation_level < 0.8:
                undersaturation_bonus = min(0.15, (0.8 - competition.saturation_level) * 0.3)
                return 1.0 + undersaturation_bonus
            
            return 1.0  # Normal market conditions
            
        except MarketCompetition.DoesNotExist:
            return 1.0  # No competition data available
    
    def _update_market_competition(self):
        """Aktualisiert Markt-Wettbewerbsdaten"""
        competitions = MarketCompetition.objects.filter(
            session=self.session,
            month=self.session.current_month,
            year=self.session.current_year
        )
        
        for competition in competitions:
            # Berechne Gesamtangebot (Konkurrenten + Spieler)
            competitor_supply = CompetitorSale.objects.filter(
                competitor__session=self.session,
                market=competition.market,
                bike_type=competition.bike_type,
                price_segment=competition.price_segment,
                month=self.session.current_month,
                year=self.session.current_year
            ).aggregate(
                total=models.Sum('quantity_offered')
            )['total'] or 0
            
            # Player supply würde hier auch addiert werden
            # TODO: Integration mit Player Sales
            
            competition.total_supply = competitor_supply
            
            # Berechne Sättigung
            if competition.estimated_demand > 0:
                competition.saturation_level = competition.total_supply / competition.estimated_demand
            else:
                competition.saturation_level = 1.0
            
            # Berechne Preisdruck
            if competition.saturation_level > 1.0:
                competition.price_pressure = -min(0.5, (competition.saturation_level - 1.0))
            else:
                competition.price_pressure = (1.0 - competition.saturation_level) * 0.3
            
            competition.save()


def initialize_competitors_for_session(session):
    """Initialisiert Standard-Konkurrenten für eine neue Session"""
    default_competitors = [
        {
            'name': 'BilligRad GmbH',
            'strategy': 'cheap_only',
            'financial_resources': Decimal('40000.00'),
            'market_presence': 12.0,
            'aggressiveness': 0.8,
            'efficiency': 0.6
        },
        {
            'name': 'QualitätsBikes AG',
            'strategy': 'premium_focus',
            'financial_resources': Decimal('75000.00'),
            'market_presence': 18.0,
            'aggressiveness': 0.4,
            'efficiency': 0.9
        },
        {
            'name': 'E-Power Cycles',
            'strategy': 'e_bike_specialist',
            'financial_resources': Decimal('60000.00'),
            'market_presence': 15.0,
            'aggressiveness': 0.6,
            'efficiency': 0.8
        },
        {
            'name': 'AllRound Bikes',
            'strategy': 'balanced',
            'financial_resources': Decimal('55000.00'),
            'market_presence': 20.0,
            'aggressiveness': 0.5,
            'efficiency': 0.7
        }
    ]
    
    for competitor_data in default_competitors:
        AICompetitor.objects.create(
            session=session,
            **competitor_data
        )