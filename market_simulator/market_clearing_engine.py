import math
import random
from decimal import Decimal
from typing import Dict, List, Tuple, Optional
from statistics import mean, stdev

from django.db import transaction
from django.db.models import Q, Sum, Avg, Count

from .models import (
    PlayerMarketSubmission, MarketClearingResult, PriceDemandFunction,
    CustomerDemographics, BikeMarketSegment, EconomicCondition, MarketFactors,
    MarketConfiguration, CustomerSegment
)
from bikeshop.models import BikeType
from multiplayer.models import MultiplayerGame, PlayerSession


class MarketClearingEngine:
    """Engine for processing market clearing and determining sales allocation"""
    
    def __init__(self, multiplayer_game: MultiplayerGame):
        self.game = multiplayer_game
        self.market_config = None
        
    def initialize_market_configuration(self) -> MarketConfiguration:
        """Initialize market configuration for the game"""
        
        config, created = MarketConfiguration.objects.get_or_create(
            multiplayer_game=self.game,
            defaults={
                'market_structure': 'monopolistic',  # Monopolistic competition
                'total_market_size': 5000000,
                'market_concentration_ratio': 0.4,
                'price_competition_intensity': 1.0,
                'quality_competition_intensity': 1.0,
                'innovation_competition_intensity': 1.0,
                'entry_barriers': 1.0,
                'exit_barriers': 1.0,
                'price_transparency': 0.8,
                'information_asymmetry': 0.2
            }
        )
        
        if created:
            self._initialize_price_demand_functions(config)
        
        self.market_config = config
        return config
    
    def process_monthly_market_clearing(self, month: int, year: int) -> Dict:
        """Process market clearing for all bike types in the given month"""
        
        if not self.market_config:
            self.initialize_market_configuration()
        
        # Get market conditions
        economic_condition = self._get_economic_condition(month, year)
        market_factors = self._get_market_factors(month, year)
        customer_demographics = self._get_customer_demographics(month, year)
        
        # Get all submissions for this month
        submissions = PlayerMarketSubmission.objects.filter(
            multiplayer_game=self.game,
            month=month,
            year=year,
            processed=False
        )
        
        if not submissions.exists():
            return {'processed_bike_types': 0, 'total_sales': 0, 'message': 'No submissions to process'}
        
        # Group submissions by bike type
        bike_types = set(submission.bike_type for submission in submissions)
        results = {}
        
        with transaction.atomic():
            for bike_type in bike_types:
                bike_submissions = submissions.filter(bike_type=bike_type)
                result = self._process_bike_type_market(
                    bike_type, bike_submissions, month, year,
                    economic_condition, market_factors, customer_demographics
                )
                results[bike_type.name] = result
        
        # Mark all submissions as processed
        submissions.update(processed=True)
        
        return {
            'processed_bike_types': len(bike_types),
            'total_sales': sum(r.get('total_sales', 0) for r in results.values()),
            'bike_type_results': results
        }
    
    def _process_bike_type_market(self, bike_type: BikeType, submissions, month: int, year: int,
                                economic_condition: EconomicCondition, market_factors: MarketFactors,
                                customer_demographics: CustomerDemographics) -> Dict:
        """Process market clearing for a specific bike type"""
        
        # Calculate total demand for this bike type
        total_demand = self._calculate_total_demand(
            bike_type, submissions, economic_condition, market_factors, customer_demographics
        )
        
        # Calculate total supply
        total_supply = sum(submission.quantity_offered for submission in submissions)
        
        # Determine market clearing mechanism based on market structure
        if self.market_config.market_structure == 'perfect':
            allocation_result = self._perfect_competition_clearing(submissions, total_demand)
        elif self.market_config.market_structure == 'monopolistic':
            allocation_result = self._monopolistic_competition_clearing(submissions, total_demand)
        elif self.market_config.market_structure == 'oligopoly':
            allocation_result = self._oligopoly_clearing(submissions, total_demand)
        else:
            allocation_result = self._duopoly_clearing(submissions, total_demand)
        
        # Calculate market metrics
        market_metrics = self._calculate_market_metrics(submissions, allocation_result)
        
        # Create market clearing result
        clearing_result = MarketClearingResult.objects.create(
            multiplayer_game=self.game,
            month=month,
            year=year,
            bike_type=bike_type,
            total_quantity_supplied=total_supply,
            total_quantity_demanded=total_demand,
            total_quantity_sold=allocation_result['total_sold'],
            market_clearing_price=allocation_result['clearing_price'],
            average_price_offered=allocation_result['average_price'],
            price_dispersion=market_metrics['price_dispersion'],
            excess_supply=max(0, total_supply - total_demand),
            excess_demand=max(0, total_demand - total_supply),
            market_efficiency=market_metrics['efficiency'],
            herfindahl_index=market_metrics['herfindahl_index'],
            number_of_competitors=submissions.count(),
            economic_multiplier=self._calculate_economic_multiplier(economic_condition),
            market_factors_multiplier=self._calculate_market_factors_multiplier(market_factors, bike_type),
            seasonal_adjustment=market_factors.seasonal_factor
        )
        
        # Update individual submissions with results
        self._update_submission_results(submissions, allocation_result)
        
        return {
            'total_demand': total_demand,
            'total_supply': total_supply,
            'total_sales': allocation_result['total_sold'],
            'clearing_price': float(allocation_result['clearing_price']),
            'market_efficiency': market_metrics['efficiency'],
            'number_of_competitors': submissions.count()
        }
    
    def _calculate_total_demand(self, bike_type: BikeType, submissions, 
                              economic_condition: EconomicCondition, market_factors: MarketFactors,
                              customer_demographics: CustomerDemographics) -> int:
        """Calculate total market demand for a bike type"""
        
        # Get bike market segment data
        try:
            bike_segment = BikeMarketSegment.objects.get(
                customer_demographics=customer_demographics,
                bike_type=bike_type
            )
        except BikeMarketSegment.DoesNotExist:
            # Fallback if segment doesn't exist
            return 1000
        
        # Start with base demand
        base_demand = bike_segment.base_monthly_demand
        
        # Apply economic multiplier
        economic_multiplier = self._calculate_economic_multiplier(economic_condition)
        
        # Apply market factors multiplier
        market_multiplier = self._calculate_market_factors_multiplier(market_factors, bike_type)
        
        # Calculate price-demand effects for each customer segment
        segment_demands = []
        
        for segment in CustomerSegment.choices:
            segment_key = segment[0]
            segment_demand = self._calculate_segment_demand(
                bike_type, segment_key, submissions, economic_condition, 
                market_factors, customer_demographics
            )
            segment_demands.append(segment_demand)
        
        # Aggregate demand from all segments
        total_segment_demand = sum(segment_demands)
        
        # Combine base demand with segment-specific calculations
        final_demand = int((base_demand * 0.3) + (total_segment_demand * 0.7))
        
        # Apply multipliers
        final_demand = int(final_demand * economic_multiplier * market_multiplier)
        
        # Add some randomness (market uncertainty)
        randomness = random.gauss(1.0, 0.1)  # 10% standard deviation
        final_demand = int(final_demand * randomness)
        
        return max(0, final_demand)
    
    def _calculate_segment_demand(self, bike_type: BikeType, segment: str, submissions,
                                economic_condition: EconomicCondition, market_factors: MarketFactors,
                                customer_demographics: CustomerDemographics) -> float:
        """Calculate demand from a specific customer segment"""
        
        try:
            # Get price-demand function for this segment
            pdf = PriceDemandFunction.objects.get(
                market_config=self.market_config,
                bike_type=bike_type,
                customer_segment=segment
            )
        except PriceDemandFunction.DoesNotExist:
            return 0.0
        
        # Calculate weighted average price and quality from all submissions
        if not submissions:
            return 0.0
        
        total_quantity = sum(s.quantity_offered for s in submissions)
        if total_quantity == 0:
            return 0.0
        
        weighted_price = sum(
            float(s.price_per_unit) * s.quantity_offered for s in submissions
        ) / total_quantity
        
        weighted_quality = sum(
            s.quality_rating * s.quantity_offered for s in submissions
        ) / total_quantity
        
        weighted_innovation = sum(
            s.innovation_level * s.quantity_offered for s in submissions
        ) / total_quantity
        
        weighted_brand = sum(
            s.brand_strength * s.quantity_offered for s in submissions
        ) / total_quantity
        
        # Calculate demand using price-demand function
        player_attributes = {
            'quality_rating': weighted_quality,
            'innovation_level': weighted_innovation,
            'brand_strength': weighted_brand
        }
        
        segment_demand = pdf.calculate_demand(
            weighted_price, economic_condition, market_factors, player_attributes
        )
        
        # Apply segment size (what percentage of market this segment represents)
        segment_percentage = self._get_segment_percentage(segment, customer_demographics)
        total_market_customers = customer_demographics.total_potential_customers
        
        segment_size = (segment_percentage / 100) * total_market_customers
        monthly_purchase_rate = 0.01 / 12  # 1% annual purchase rate
        
        segment_monthly_customers = segment_size * monthly_purchase_rate
        
        # Scale demand to realistic levels
        final_segment_demand = min(segment_demand, segment_monthly_customers)
        
        return max(0, final_segment_demand)
    
    def _perfect_competition_clearing(self, submissions, total_demand: int) -> Dict:
        """Market clearing under perfect competition (price = marginal cost)"""
        
        # Sort submissions by price (lowest first)
        sorted_submissions = sorted(submissions, key=lambda s: s.price_per_unit)
        
        allocations = {}
        remaining_demand = total_demand
        total_sold = 0
        total_revenue = Decimal('0.00')
        
        for submission in sorted_submissions:
            if remaining_demand <= 0:
                allocations[submission.id] = 0
                continue
            
            # In perfect competition, all units sell at the same price (marginal price)
            units_to_sell = min(submission.quantity_offered, remaining_demand)
            allocations[submission.id] = units_to_sell
            
            remaining_demand -= units_to_sell
            total_sold += units_to_sell
            total_revenue += submission.price_per_unit * units_to_sell
        
        # Market clearing price is the price of the last unit sold
        clearing_price = sorted_submissions[-1].price_per_unit if sorted_submissions else Decimal('0.00')
        average_price = total_revenue / total_sold if total_sold > 0 else Decimal('0.00')
        
        return {
            'allocations': allocations,
            'total_sold': total_sold,
            'clearing_price': clearing_price,
            'average_price': average_price
        }
    
    def _monopolistic_competition_clearing(self, submissions, total_demand: int) -> Dict:
        """Market clearing under monopolistic competition (product differentiation)"""
        
        allocations = {}
        total_sold = 0
        total_revenue = Decimal('0.00')
        
        # Calculate each submission's market attractiveness
        submission_scores = []
        for submission in submissions:
            attractiveness = self._calculate_product_attractiveness(submission)
            submission_scores.append((submission, attractiveness))
        
        # Normalize attractiveness scores to get market shares
        total_attractiveness = sum(score for _, score in submission_scores)
        
        if total_attractiveness == 0:
            # Fallback: equal distribution
            for submission in submissions:
                allocation = total_demand // len(submissions)
                allocations[submission.id] = min(allocation, submission.quantity_offered)
                total_sold += allocations[submission.id]
                total_revenue += submission.price_per_unit * allocations[submission.id]
        else:
            for submission, attractiveness in submission_scores:
                market_share = attractiveness / total_attractiveness
                target_sales = int(total_demand * market_share)
                
                # Apply supply constraint
                actual_sales = min(target_sales, submission.quantity_offered)
                allocations[submission.id] = actual_sales
                
                total_sold += actual_sales
                total_revenue += submission.price_per_unit * actual_sales
        
        # Calculate prices
        clearing_price = total_revenue / total_sold if total_sold > 0 else Decimal('0.00')
        average_price = clearing_price  # Same in this case
        
        return {
            'allocations': allocations,
            'total_sold': total_sold,
            'clearing_price': clearing_price,
            'average_price': average_price
        }
    
    def _oligopoly_clearing(self, submissions, total_demand: int) -> Dict:
        """Market clearing under oligopoly (strategic interaction)"""
        
        # In oligopoly, players have market power and react to each other
        # Implement a simplified Cournot competition model
        
        n_firms = submissions.count()
        if n_firms == 0:
            return {'allocations': {}, 'total_sold': 0, 'clearing_price': Decimal('0.00'), 'average_price': Decimal('0.00')}
        
        # Calculate Nash equilibrium quantities (simplified)
        # In Cournot: qi = (a - c) / (b * (n + 1)) where a=demand intercept, b=slope, c=marginal cost, n=number of firms
        
        allocations = {}
        total_sold = 0
        total_revenue = Decimal('0.00')
        
        # Simplified: each firm gets demand / (n + 1) adjusted for their capacity
        base_quantity = total_demand // (n_firms + 1)
        
        for submission in submissions:
            # Strategic quantity considering competition
            strategic_quantity = min(base_quantity, submission.quantity_offered)
            
            # Adjust based on relative price competitiveness
            avg_price = sum(s.price_per_unit for s in submissions) / n_firms
            price_advantage = 1.0 - (float(submission.price_per_unit - avg_price) / float(avg_price))
            price_advantage = max(0.5, min(1.5, price_advantage))
            
            final_quantity = int(strategic_quantity * price_advantage)
            allocations[submission.id] = min(final_quantity, submission.quantity_offered)
            
            total_sold += allocations[submission.id]
            total_revenue += submission.price_per_unit * allocations[submission.id]
        
        clearing_price = total_revenue / total_sold if total_sold > 0 else Decimal('0.00')
        average_price = clearing_price
        
        return {
            'allocations': allocations,
            'total_sold': total_sold,
            'clearing_price': clearing_price,
            'average_price': average_price
        }
    
    def _duopoly_clearing(self, submissions, total_demand: int) -> Dict:
        """Market clearing under duopoly (two-firm competition)"""
        
        # Similar to oligopoly but with specific two-firm dynamics
        return self._oligopoly_clearing(submissions, total_demand)
    
    def _calculate_product_attractiveness(self, submission: PlayerMarketSubmission) -> float:
        """Calculate product attractiveness score for market share allocation"""
        
        # Attractiveness based on price, quality, innovation, brand, and marketing
        price_score = 1.0 / (1.0 + float(submission.price_per_unit) / 1000)  # Lower price = higher score
        quality_score = submission.quality_rating / 10.0
        innovation_score = submission.innovation_level / 10.0
        brand_score = submission.brand_strength / 10.0
        marketing_score = min(1.0, float(submission.marketing_spend) / 10000)  # Diminishing returns
        
        # Weighted combination
        attractiveness = (
            price_score * 0.4 +       # Price is most important
            quality_score * 0.25 +    # Quality matters
            innovation_score * 0.15 + # Innovation helps
            brand_score * 0.15 +      # Brand recognition
            marketing_score * 0.05    # Marketing boost
        )
        
        return max(0.1, attractiveness)  # Minimum attractiveness
    
    def _calculate_market_metrics(self, submissions, allocation_result: Dict) -> Dict:
        """Calculate market structure and efficiency metrics"""
        
        total_sold = allocation_result['total_sold']
        allocations = allocation_result['allocations']
        
        if total_sold == 0:
            return {
                'price_dispersion': 0.0,
                'efficiency': 0.0,
                'herfindahl_index': 0.0
            }
        
        # Price dispersion (coefficient of variation)
        prices = [float(s.price_per_unit) for s in submissions]
        if len(prices) > 1:
            price_dispersion = stdev(prices) / mean(prices) if mean(prices) > 0 else 0.0
        else:
            price_dispersion = 0.0
        
        # Market efficiency (how much of potential demand was satisfied)
        total_supply = sum(s.quantity_offered for s in submissions)
        efficiency = total_sold / min(total_supply, allocation_result.get('total_demand', total_sold))
        
        # Herfindahl-Hirschman Index (market concentration)
        market_shares = []
        for submission in submissions:
            allocation = allocations.get(submission.id, 0)
            market_share = allocation / total_sold if total_sold > 0 else 0
            market_shares.append(market_share)
        
        herfindahl_index = sum(share ** 2 for share in market_shares)
        
        return {
            'price_dispersion': price_dispersion,
            'efficiency': efficiency,
            'herfindahl_index': herfindahl_index
        }
    
    def _update_submission_results(self, submissions, allocation_result: Dict):
        """Update individual submission results with sales data"""
        
        allocations = allocation_result['allocations']
        total_sold = allocation_result['total_sold']
        
        for submission in submissions:
            units_sold = allocations.get(submission.id, 0)
            revenue = submission.price_per_unit * units_sold
            market_share = (units_sold / total_sold * 100) if total_sold > 0 else 0.0
            
            submission.units_sold = units_sold
            submission.market_share_percentage = market_share
            submission.revenue_generated = revenue
            submission.save()
    
    def _calculate_economic_multiplier(self, economic_condition: EconomicCondition) -> float:
        """Calculate economic multiplier effect on demand"""
        
        # Base multiplier from economic strength
        base_multiplier = 0.5 + economic_condition.economic_strength
        
        # Additional factors
        confidence_effect = economic_condition.consumer_confidence_index / 100
        income_effect = economic_condition.disposable_income_index / 100
        
        return base_multiplier * confidence_effect * income_effect
    
    def _calculate_market_factors_multiplier(self, market_factors: MarketFactors, bike_type: BikeType) -> float:
        """Calculate market factors multiplier for specific bike type"""
        
        bike_name = bike_type.name.lower()
        multiplier = market_factors.overall_demand_multiplier
        
        # Bike-specific adjustments
        if 'electric' in bike_name or 'e-bike' in bike_name:
            multiplier *= market_factors.electric_bike_trend
        
        if 'vintage' in bike_name or 'retro' in bike_name:
            multiplier *= market_factors.retro_trend_strength
        
        return max(0.1, min(3.0, multiplier))
    
    def _get_segment_percentage(self, segment: str, demographics: CustomerDemographics) -> float:
        """Get percentage of market represented by customer segment"""
        
        segment_map = {
            'commuters': demographics.commuters_percentage,
            'recreational': demographics.recreational_percentage,
            'sports': demographics.sports_percentage,
            'families': demographics.families_percentage,
            'eco_conscious': demographics.eco_conscious_percentage,
            'luxury': demographics.luxury_percentage,
            'budget': demographics.budget_percentage
        }
        
        return segment_map.get(segment, 0.0)
    
    def _get_economic_condition(self, month: int, year: int) -> EconomicCondition:
        """Get economic condition for the given month/year"""
        try:
            return EconomicCondition.objects.get(
                multiplayer_game=self.game,
                month=month,
                year=year
            )
        except EconomicCondition.DoesNotExist:
            # Create default if not exists
            return EconomicCondition.objects.create(
                multiplayer_game=self.game,
                month=month,
                year=year
            )
    
    def _get_market_factors(self, month: int, year: int) -> MarketFactors:
        """Get market factors for the given month/year"""
        try:
            return MarketFactors.objects.get(
                multiplayer_game=self.game,
                month=month,
                year=year
            )
        except MarketFactors.DoesNotExist:
            # Create default if not exists
            return MarketFactors.objects.create(
                multiplayer_game=self.game,
                month=month,
                year=year
            )
    
    def _get_customer_demographics(self, month: int, year: int) -> CustomerDemographics:
        """Get customer demographics for the given month/year"""
        try:
            return CustomerDemographics.objects.get(
                multiplayer_game=self.game,
                month=month,
                year=year
            )
        except CustomerDemographics.DoesNotExist:
            # Create default if not exists
            return CustomerDemographics.objects.create(
                multiplayer_game=self.game,
                month=month,
                year=year
            )
    
    def _initialize_price_demand_functions(self, market_config: MarketConfiguration):
        """Initialize price-demand functions for all bike types and customer segments"""
        
        bike_types = BikeType.objects.all()
        customer_segments = CustomerSegment.choices
        
        for bike_type in bike_types:
            for segment_choice in customer_segments:
                segment = segment_choice[0]
                
                # Create customized PDF parameters based on bike type and segment
                pdf_params = self._get_pdf_parameters(bike_type, segment)
                
                PriceDemandFunction.objects.create(
                    market_config=market_config,
                    bike_type=bike_type,
                    customer_segment=segment,
                    **pdf_params
                )
    
    def _get_pdf_parameters(self, bike_type: BikeType, segment: str) -> Dict:
        """Get price-demand function parameters for bike type and segment combination"""
        
        bike_name = bike_type.name.lower()
        
        # Base parameters
        params = {
            'demand_intercept': 1000.0,
            'price_coefficient': -0.5,
            'income_coefficient': 0.3,
            'substitute_coefficient': -0.2,
            'trend_coefficient': 0.1,
            'price_elasticity': -1.5,
            'saturation_point': 10000,
            'quality_sensitivity': 0.2,
            'innovation_sensitivity': 0.15,
            'brand_loyalty': 0.1
        }
        
        # Adjust based on bike type
        if 'electric' in bike_name or 'e-bike' in bike_name:
            params['demand_intercept'] = 800.0
            params['price_elasticity'] = -1.2  # Less price sensitive (newer technology)
            params['innovation_sensitivity'] = 0.3
            params['income_coefficient'] = 0.5  # Higher income dependence
        
        elif 'luxury' in bike_name or 'premium' in bike_name:
            params['demand_intercept'] = 200.0
            params['price_elasticity'] = -0.8  # Luxury goods less price sensitive
            params['quality_sensitivity'] = 0.4
            params['brand_loyalty'] = 0.3
            params['income_coefficient'] = 0.7
        
        elif 'budget' in bike_name or 'basic' in bike_name:
            params['demand_intercept'] = 1500.0
            params['price_elasticity'] = -2.5  # Very price sensitive
            params['quality_sensitivity'] = 0.1
            params['brand_loyalty'] = 0.05
            params['income_coefficient'] = -0.2  # Counter-cyclical
        
        elif 'children' in bike_name or 'kinder' in bike_name:
            params['demand_intercept'] = 500.0
            params['price_elasticity'] = -2.0  # Family purchases price sensitive
            params['saturation_point'] = 5000
        
        # Adjust based on customer segment
        if segment == 'luxury':
            params['price_elasticity'] *= 0.5  # Less price sensitive
            params['quality_sensitivity'] *= 2.0
            params['brand_loyalty'] *= 3.0
        elif segment == 'budget':
            params['price_elasticity'] *= 1.5  # More price sensitive
            params['quality_sensitivity'] *= 0.5
        elif segment == 'sports':
            params['innovation_sensitivity'] *= 2.0
            params['quality_sensitivity'] *= 1.5
        elif segment == 'eco_conscious':
            params['trend_coefficient'] *= 2.0
            params['innovation_sensitivity'] *= 1.5
        
        return params