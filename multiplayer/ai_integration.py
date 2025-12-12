"""
Integration layer between multiplayer AI system and existing game components.
This module bridges the new AI system with existing models and game logic.
"""

from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Any
from django.db import transaction, models
from django.utils import timezone

from bikeshop.models import GameSession, BikeType, Component, BikePrice
from sales.models import Market, MarketDemand, SalesOrder
from production.models import ProductionPlan, ProductionOrder, ProducedBike
from procurement.models import ProcurementOrder, ProcurementOrderItem, Supplier
from warehouse.models import ComponentStock, Warehouse
from finance.models import Credit, Transaction, MonthlyReport
from workers.models import Worker

from .models import PlayerSession, TurnState, MultiplayerGame
from competitors.models import (
    AICompetitor, CompetitorProduction, CompetitorSale, 
    MarketCompetition, CompetitorStrategy
)
from competitors.ai_engine import CompetitorAIEngine


class MultiplayerIntegrationManager:
    """Manages integration between multiplayer system and existing game logic"""
    
    def __init__(self, multiplayer_game: MultiplayerGame):
        self.game = multiplayer_game
        self.session_cache = {}
    
    def create_ai_competitor_bridge(self, ai_player: PlayerSession) -> Optional[AICompetitor]:
        """Create or get AI competitor representation for multiplayer AI player"""
        
        # Check if AI competitor already exists
        game_session = self.get_or_create_game_session(ai_player)
        if not game_session:
            return None
        
        try:
            ai_competitor = AICompetitor.objects.get(
                session=game_session,
                name=ai_player.company_name
            )
        except AICompetitor.DoesNotExist:
            # Create new AI competitor - apply game parameter multipliers
            from multiplayer.parameter_utils import (
                apply_competitor_financial_resources_multiplier,
                apply_competitor_market_presence_multiplier,
                apply_competitor_aggressiveness,
                apply_competitor_efficiency_multiplier
            )

            financial_resources = apply_competitor_financial_resources_multiplier(
                ai_player.balance, game_session
            )
            market_presence = apply_competitor_market_presence_multiplier(
                self._calculate_market_presence(ai_player), game_session
            )
            aggressiveness = apply_competitor_aggressiveness(
                ai_player.ai_aggressiveness, game_session
            )
            efficiency = apply_competitor_efficiency_multiplier(
                self._calculate_efficiency(ai_player), game_session
            )

            ai_competitor = AICompetitor.objects.create(
                session=game_session,
                name=ai_player.company_name,
                strategy=ai_player.ai_strategy or 'balanced',
                financial_resources=financial_resources,
                market_presence=market_presence,
                aggressiveness=aggressiveness,
                efficiency=efficiency
            )
        
        return ai_competitor
    
    def sync_ai_player_state(self, ai_player: PlayerSession, ai_competitor: AICompetitor) -> None:
        """Synchronize state between AI player and AI competitor"""
        
        # Update AI competitor with current player state
        ai_competitor.financial_resources = ai_player.balance
        ai_competitor.market_presence = self._calculate_market_presence(ai_player)
        ai_competitor.total_bikes_produced = ai_player.bikes_produced
        ai_competitor.total_bikes_sold = ai_player.bikes_sold
        ai_competitor.total_revenue = ai_player.total_revenue
        ai_competitor.save()
        
        # Update player with competitor performance
        ai_player.market_share = self._calculate_market_share(ai_competitor)
        ai_player.save()
    
    def get_or_create_game_session(self, ai_player: PlayerSession) -> Optional[GameSession]:
        """Get or create GameSession for AI player integration"""
        
        # Check cache first
        cache_key = f"session_{ai_player.id}"
        if cache_key in self.session_cache:
            return self.session_cache[cache_key]
        
        # Try to find existing session
        try:
            # Look for a session associated with this multiplayer game
            session = GameSession.objects.filter(
                name__icontains=self.game.name,
                is_active=True
            ).first()
            
            if not session:
                # Create new session for multiplayer game
                session = GameSession.objects.create(
                    name=f"Multiplayer_{self.game.name}_{self.game.id}",
                    current_month=self.game.current_month,
                    current_year=self.game.current_year,
                    starting_balance=self.game.starting_balance,
                    is_active=True
                )
            
            self.session_cache[cache_key] = session
            return session
            
        except Exception as e:
            print(f"Error creating/getting game session: {e}")
            return None
    
    def execute_ai_production_decisions(self, ai_player: PlayerSession, 
                                       decisions: Dict, game_session: GameSession) -> Dict:
        """Execute AI production decisions in the game system"""
        
        results = {
            'success': False,
            'bikes_planned': 0,
            'bikes_produced': 0,
            'total_cost': Decimal('0'),
            'errors': []
        }
        
        try:
            with transaction.atomic():
                # Get or create production plan
                production_plan, created = ProductionPlan.objects.get_or_create(
                    session=game_session,
                    month=self.game.current_month,
                    year=self.game.current_year,
                    defaults={'total_bikes_planned': 0}
                )
                
                target_volume = decisions.get('target_volume', 0)
                bike_priorities = decisions.get('bike_priorities', {})
                segment_focus = decisions.get('segment_focus', ['standard'])
                
                # Get available bike types
                bike_types = BikeType.objects.filter(session=game_session)
                
                bikes_planned = 0
                total_cost = Decimal('0')
                
                for bike_type in bike_types:
                    if bikes_planned >= target_volume:
                        break
                    
                    # Get priority for this bike type
                    priority = bike_priorities.get(bike_type.name, 0.5)
                    if priority < 0.3:  # Skip low priority bikes
                        continue
                    
                    # Calculate quantity for this bike type
                    remaining_capacity = target_volume - bikes_planned
                    type_quantity = min(
                        remaining_capacity,
                        int(target_volume * priority * 0.4)  # Max 40% per type
                    )
                    
                    if type_quantity < 1:
                        continue
                    
                    # Create production orders for different segments
                    for segment in segment_focus:
                        if type_quantity <= 0:
                            break
                        
                        segment_quantity = max(1, type_quantity // len(segment_focus))
                        
                        # Check if we can afford production
                        production_cost = self._calculate_production_cost(
                            bike_type, segment, game_session
                        )
                        
                        total_segment_cost = production_cost * segment_quantity
                        
                        if ai_player.balance >= total_segment_cost:
                            # Create production order
                            production_order = ProductionOrder.objects.create(
                                session=game_session,
                                bike_type=bike_type,
                                price_segment=segment,
                                quantity=segment_quantity,
                                month=self.game.current_month,
                                year=self.game.current_year,
                                estimated_cost=total_segment_cost
                            )
                            
                            bikes_planned += segment_quantity
                            total_cost += total_segment_cost
                            type_quantity -= segment_quantity
                            
                            # Simulate production success
                            success_rate = self._calculate_production_success_rate(ai_player)
                            actual_production = int(segment_quantity * success_rate)
                            
                            if actual_production > 0:
                                # Create produced bikes
                                for _ in range(actual_production):
                                    ProducedBike.objects.create(
                                        session=game_session,
                                        bike_type=bike_type,
                                        price_segment=segment,
                                        production_order=production_order,
                                        production_cost=production_cost,
                                        quality_level=self._determine_quality_level(ai_player),
                                        month_produced=self.game.current_month,
                                        year_produced=self.game.current_year
                                    )
                                
                                results['bikes_produced'] += actual_production
                
                # Update production plan
                production_plan.total_bikes_planned += bikes_planned
                production_plan.save()
                
                # Update AI player balance
                ai_player.balance -= total_cost
                ai_player.bikes_produced += results['bikes_produced']
                ai_player.save()
                
                results.update({
                    'success': True,
                    'bikes_planned': bikes_planned,
                    'total_cost': total_cost
                })
                
        except Exception as e:
            results['errors'].append(str(e))
        
        return results
    
    def execute_ai_procurement_decisions(self, ai_player: PlayerSession,
                                        decisions: Dict, game_session: GameSession) -> Dict:
        """Execute AI procurement decisions"""
        
        results = {
            'success': False,
            'orders_created': 0,
            'total_cost': Decimal('0'),
            'errors': []
        }
        
        try:
            with transaction.atomic():
                strategy = decisions.get('ordering_strategy', 'balanced')
                inventory_target = decisions.get('inventory_target', 'medium')
                
                # Get suppliers
                suppliers = Supplier.objects.filter(session=game_session)
                components = Component.objects.filter(session=game_session)
                
                # Calculate procurement needs
                procurement_needs = self._calculate_procurement_needs(
                    ai_player, game_session, inventory_target
                )
                
                total_cost = Decimal('0')
                orders_created = 0
                
                for component, needed_quantity in procurement_needs.items():
                    if needed_quantity <= 0:
                        continue
                    
                    # Select supplier based on strategy
                    supplier = self._select_supplier(suppliers, strategy)
                    if not supplier:
                        continue
                    
                    # Calculate cost
                    component_cost = self._get_component_cost(component, supplier)
                    order_cost = component_cost * needed_quantity
                    
                    if ai_player.balance >= order_cost:
                        # Create procurement order
                        procurement_order = ProcurementOrder.objects.create(
                            session=game_session,
                            supplier=supplier,
                            month=self.game.current_month,
                            year=self.game.current_year,
                            is_delivered=False
                        )
                        
                        # Create order item
                        ProcurementOrderItem.objects.create(
                            order=procurement_order,
                            component=component,
                            quantity_ordered=needed_quantity,
                            price_per_unit=component_cost
                        )
                        
                        total_cost += order_cost
                        orders_created += 1
                        
                        # Update balance
                        ai_player.balance -= order_cost
                
                ai_player.save()
                
                results.update({
                    'success': True,
                    'orders_created': orders_created,
                    'total_cost': total_cost
                })
                
        except Exception as e:
            results['errors'].append(str(e))
        
        return results
    
    def execute_ai_sales_decisions(self, ai_player: PlayerSession,
                                  decisions: Dict, game_session: GameSession) -> Dict:
        """Execute AI sales decisions"""
        
        results = {
            'success': False,
            'orders_created': 0,
            'total_revenue': Decimal('0'),
            'bikes_sold': 0,
            'errors': []
        }
        
        try:
            with transaction.atomic():
                pricing_method = decisions.get('pricing_method', 'market_adaptive')
                
                # Get available bikes to sell
                available_bikes = ProducedBike.objects.filter(
                    session=game_session,
                    is_sold=False
                )
                
                # Get markets
                markets = Market.objects.filter(session=game_session)
                
                total_revenue = Decimal('0')
                bikes_sold = 0
                orders_created = 0
                
                for market in markets:
                    market_bikes = available_bikes.filter(
                        bike_type__in=market.bike_types.all()
                    )[:10]  # Limit per market
                    
                    for bike in market_bikes:
                        # Calculate selling price
                        selling_price = self._calculate_selling_price(
                            bike, market, pricing_method, decisions
                        )
                        
                        # Simulate sale success
                        sale_probability = self._calculate_sale_probability(
                            bike, market, selling_price, ai_player
                        )
                        
                        if sale_probability > 0.5:  # 50% threshold for sale
                            # Create sales order
                            sales_order = SalesOrder.objects.create(
                                session=game_session,
                                market=market,
                                bike_type=bike.bike_type,
                                price_segment=bike.price_segment,
                                quantity=1,
                                selling_price=selling_price,
                                month=self.game.current_month,
                                year=self.game.current_year
                            )
                            
                            # Mark bike as sold
                            bike.is_sold = True
                            bike.selling_price = selling_price
                            bike.sales_order = sales_order
                            bike.save()
                            
                            total_revenue += selling_price
                            bikes_sold += 1
                            orders_created += 1
                
                # Update AI player stats
                ai_player.balance += total_revenue
                ai_player.total_revenue += total_revenue
                ai_player.bikes_sold += bikes_sold
                ai_player.save()
                
                results.update({
                    'success': True,
                    'orders_created': orders_created,
                    'total_revenue': total_revenue,
                    'bikes_sold': bikes_sold
                })
                
        except Exception as e:
            results['errors'].append(str(e))
        
        return results
    
    def execute_ai_financial_decisions(self, ai_player: PlayerSession,
                                      decisions: Dict, game_session: GameSession) -> Dict:
        """Execute AI financial decisions"""
        
        results = {
            'success': False,
            'actions_taken': [],
            'errors': []
        }
        
        try:
            with transaction.atomic():
                debt_tolerance = decisions.get('debt_tolerance', 'moderate')
                cash_reserve = decisions.get('cash_reserve', 'optimal')
                credit_utilization = decisions.get('credit_utilization', 'strategic')
                
                actions_taken = []
                
                # Handle credit decisions
                if ai_player.balance < 20000 and debt_tolerance in ['moderate', 'high']:
                    credit_amount = self._calculate_optimal_credit_amount(
                        ai_player, debt_tolerance
                    )
                    
                    if credit_amount > 0:
                        # Create credit transaction
                        from multiplayer.parameter_utils import get_interest_rate
                        base_rate = get_interest_rate(game_session)

                        credit = Credit.objects.create(
                            session=game_session,
                            amount=credit_amount,
                            interest_rate=Decimal(str(base_rate * 1.2)),  # Use game parameter with 1.2x multiplier for long-term credit
                            duration_months=12,
                            remaining_amount=credit_amount,
                            month_taken=self.game.current_month,
                            year_taken=self.game.current_year
                        )
                        
                        # Update player balance
                        ai_player.balance += credit_amount
                        ai_player.save()
                        
                        actions_taken.append(f"Took credit of {credit_amount}")
                
                # Handle cash reserve management
                if cash_reserve == 'high' and ai_player.balance > 80000:
                    # Conservative financial management
                    actions_taken.append("Maintaining high cash reserves")
                elif cash_reserve == 'minimal' and ai_player.balance > 50000:
                    # Aggressive reinvestment (could be handled by increasing production budget)
                    actions_taken.append("Optimizing cash utilization")
                
                # Handle existing credit payments
                existing_credits = Credit.objects.filter(
                    session=game_session,
                    remaining_amount__gt=0
                )
                
                for credit in existing_credits:
                    monthly_payment = credit.amount / credit.duration_months
                    if ai_player.balance >= monthly_payment:
                        # Make payment
                        ai_player.balance -= monthly_payment
                        credit.remaining_amount -= monthly_payment
                        
                        if credit.remaining_amount <= 0:
                            credit.remaining_amount = Decimal('0')
                        
                        credit.save()
                        actions_taken.append(f"Made credit payment of {monthly_payment}")
                
                ai_player.save()
                
                results.update({
                    'success': True,
                    'actions_taken': actions_taken
                })
                
        except Exception as e:
            results['errors'].append(str(e))
        
        return results
    
    def _calculate_market_presence(self, ai_player: PlayerSession) -> float:
        """Calculate market presence based on player performance"""
        # Base presence on revenue and market share
        base_presence = 15.0  # Default market presence
        
        if ai_player.total_revenue > 0:
            # Scale based on revenue (simplified)
            revenue_factor = min(2.0, float(ai_player.total_revenue) / 100000)
            base_presence *= revenue_factor
        
        return min(30.0, max(5.0, base_presence))  # Clamp between 5-30%
    
    def _calculate_efficiency(self, ai_player: PlayerSession) -> float:
        """Calculate production efficiency based on AI difficulty and performance"""
        base_efficiency = 0.7
        
        # Adjust for difficulty
        difficulty_bonus = ai_player.ai_difficulty * 0.2
        
        # Adjust for experience (simplified)
        if ai_player.bikes_produced > 100:
            experience_bonus = 0.1
        else:
            experience_bonus = 0.0
        
        efficiency = base_efficiency + difficulty_bonus + experience_bonus
        return min(1.0, max(0.3, efficiency))
    
    def _calculate_market_share(self, ai_competitor: AICompetitor) -> float:
        """Calculate market share for AI competitor"""
        # Simplified market share calculation
        if ai_competitor.total_revenue > 0:
            return min(25.0, float(ai_competitor.total_revenue) / 10000)
        return 0.0
    
    def _calculate_production_cost(self, bike_type: BikeType, 
                                  segment: str, session: GameSession) -> Decimal:
        """Calculate production cost for bike type and segment"""
        # Base component costs
        base_cost = Decimal('200')  # Simplified base cost
        
        # Labor costs
        labor_cost = Decimal(str(
            bike_type.skilled_worker_hours * 15 + 
            bike_type.unskilled_worker_hours * 10
        ))
        
        # Segment adjustments
        segment_multipliers = {
            'cheap': Decimal('0.8'),
            'standard': Decimal('1.0'),
            'premium': Decimal('1.3')
        }
        
        segment_multiplier = segment_multipliers.get(segment, Decimal('1.0'))
        
        total_cost = (base_cost + labor_cost) * segment_multiplier
        return total_cost
    
    def _calculate_production_success_rate(self, ai_player: PlayerSession) -> float:
        """Calculate production success rate based on AI capabilities"""
        base_rate = 0.8
        difficulty_bonus = ai_player.ai_difficulty * 0.15
        
        return min(0.95, base_rate + difficulty_bonus)
    
    def _determine_quality_level(self, ai_player: PlayerSession) -> str:
        """Determine quality level based on AI strategy"""
        strategy = ai_player.ai_strategy
        
        if strategy == 'premium_focus':
            return 'high'
        elif strategy == 'cheap_only':
            return 'standard'
        else:
            return 'standard'
    
    def _calculate_procurement_needs(self, ai_player: PlayerSession,
                                   session: GameSession, inventory_target: str) -> Dict:
        """Calculate procurement needs based on inventory target"""
        # Get current inventory
        warehouses = Warehouse.objects.filter(session=session)
        if not warehouses.exists():
            return {}
        
        warehouse = warehouses.first()
        components = Component.objects.filter(session=session)
        
        procurement_needs = {}
        
        # Define target inventory levels
        target_multipliers = {
            'minimal': 0.5,
            'low': 0.8,
            'medium': 1.0,
            'optimal': 1.2,
            'high': 1.5
        }
        
        multiplier = target_multipliers.get(inventory_target, 1.0)
        
        for component in components:
            try:
                stock = ComponentStock.objects.get(
                    session=session,
                    warehouse=warehouse,
                    component=component
                )
                current_quantity = stock.quantity
            except ComponentStock.DoesNotExist:
                current_quantity = 0
            
            # Calculate target quantity (simplified)
            target_quantity = int(50 * multiplier)  # Base target of 50 units
            
            if current_quantity < target_quantity:
                procurement_needs[component] = target_quantity - current_quantity
        
        return procurement_needs
    
    def _select_supplier(self, suppliers, strategy: str) -> Optional[Supplier]:
        """Select supplier based on procurement strategy"""
        if not suppliers.exists():
            return None
        
        if strategy == 'cost_optimization':
            # Select cheapest supplier (simplified)
            return suppliers.order_by('name').first()  # Would be by price
        elif strategy == 'quality_focus':
            # Select highest quality supplier
            return suppliers.order_by('-name').first()  # Would be by quality rating
        else:
            # Balanced approach - select random good supplier
            return suppliers.order_by('?').first()
    
    def _get_component_cost(self, component: Component, supplier: Supplier) -> Decimal:
        """Get component cost from supplier"""
        # Simplified cost calculation
        # In practice, this would look up actual supplier pricing
        base_cost = Decimal('10.00')
        
        # Add some variation based on component type
        if 'frame' in component.name.lower():
            base_cost *= 3
        elif 'wheel' in component.name.lower():
            base_cost *= 2
        elif 'brake' in component.name.lower():
            base_cost *= 1.5
        
        return base_cost
    
    def _calculate_selling_price(self, bike: ProducedBike, market: Market,
                               pricing_method: str, decisions: Dict) -> Decimal:
        """Calculate selling price for bike"""
        base_price = bike.production_cost * Decimal('1.5')  # 50% markup base
        
        # Apply pricing strategy
        if pricing_method == 'competitive_undercut':
            discount = decisions.get('discount_factor', 0.05)
            base_price *= (1 - Decimal(str(discount)))
        elif pricing_method == 'cost_plus_premium':
            margin = decisions.get('margin_target', 0.25)
            base_price = bike.production_cost * (1 + Decimal(str(margin)))
        elif pricing_method == 'value_based':
            premium = decisions.get('innovation_premium', 0.15)
            base_price *= (1 + Decimal(str(premium)))
        
        # Segment adjustments
        segment_multipliers = {
            'cheap': Decimal('0.9'),
            'standard': Decimal('1.0'),
            'premium': Decimal('1.2')
        }
        
        segment_multiplier = segment_multipliers.get(bike.price_segment, Decimal('1.0'))
        final_price = base_price * segment_multiplier
        
        return final_price
    
    def _calculate_sale_probability(self, bike: ProducedBike, market: Market,
                                   price: Decimal, ai_player: PlayerSession) -> float:
        """Calculate probability of successful sale"""
        base_probability = 0.6
        
        # Price competitiveness (simplified)
        # In practice, this would compare to market prices
        price_factor = 0.1  # Assume reasonable pricing
        
        # Market presence factor
        market_presence_factor = ai_player.market_share / 100 * 0.2
        
        # Quality factor
        quality_factor = 0.1 if bike.quality_level == 'high' else 0.0
        
        total_probability = (base_probability + price_factor + 
                           market_presence_factor + quality_factor)
        
        return min(0.9, max(0.1, total_probability))
    
    def _calculate_optimal_credit_amount(self, ai_player: PlayerSession,
                                       debt_tolerance: str) -> Decimal:
        """Calculate optimal credit amount based on debt tolerance"""
        max_amounts = {
            'low': Decimal('20000'),
            'moderate': Decimal('40000'),
            'high': Decimal('60000')
        }
        
        max_amount = max_amounts.get(debt_tolerance, Decimal('30000'))
        
        # Adjust based on current financial state
        if ai_player.balance < -10000:  # Already in debt
            return max_amount * Decimal('0.5')
        elif ai_player.total_revenue > 50000:  # Good revenue
            return max_amount
        else:
            return max_amount * Decimal('0.7')


class DifficultyScalingEngine:
    """Advanced difficulty scaling system for AI players"""
    
    DIFFICULTY_PROFILES = {
        'easy': {
            'name': 'Novice',
            'decision_accuracy': 0.60,
            'reaction_speed': 0.40,
            'market_analysis_depth': 0.50,
            'strategic_planning': 0.30,
            'risk_assessment': 0.40,
            'adaptation_rate': 0.30,
            'optimization_level': 0.35,
            'error_rate': 0.25,
            'learning_speed': 0.20
        },
        'medium': {
            'name': 'Experienced',
            'decision_accuracy': 0.80,
            'reaction_speed': 0.70,
            'market_analysis_depth': 0.75,
            'strategic_planning': 0.65,
            'risk_assessment': 0.70,
            'adaptation_rate': 0.60,
            'optimization_level': 0.65,
            'error_rate': 0.15,
            'learning_speed': 0.50
        },
        'hard': {
            'name': 'Expert',
            'decision_accuracy': 0.95,
            'reaction_speed': 0.90,
            'market_analysis_depth': 0.90,
            'strategic_planning': 0.85,
            'risk_assessment': 0.85,
            'adaptation_rate': 0.80,
            'optimization_level': 0.85,
            'error_rate': 0.08,
            'learning_speed': 0.75
        },
        'expert': {
            'name': 'Master',
            'decision_accuracy': 0.98,
            'reaction_speed': 0.95,
            'market_analysis_depth': 0.95,
            'strategic_planning': 0.95,
            'risk_assessment': 0.90,
            'adaptation_rate': 0.90,
            'optimization_level': 0.95,
            'error_rate': 0.05,
            'learning_speed': 0.85
        }
    }
    
    def __init__(self, multiplayer_game: MultiplayerGame):
        self.game = multiplayer_game
        self.base_difficulty = multiplayer_game.difficulty
    
    def get_scaled_decisions(self, ai_player: PlayerSession, 
                           base_decisions: Dict) -> Dict:
        """Apply difficulty scaling to AI decisions"""
        
        profile = self.DIFFICULTY_PROFILES.get(
            self.base_difficulty, 
            self.DIFFICULTY_PROFILES['medium']
        )
        
        # Apply individual AI player modifiers
        adjusted_profile = self._apply_individual_modifiers(ai_player, profile)
        
        # Scale each decision type
        scaled_decisions = {}
        
        for decision_type, decisions in base_decisions.items():
            scaled_decisions[decision_type] = self._scale_decision_category(
                decisions, adjusted_profile, decision_type
            )
        
        return scaled_decisions
    
    def _apply_individual_modifiers(self, ai_player: PlayerSession, 
                                   base_profile: Dict) -> Dict:
        """Apply individual AI player modifiers to base difficulty profile"""
        
        adjusted_profile = base_profile.copy()
        
        # Apply AI difficulty multiplier
        difficulty_modifier = ai_player.ai_difficulty
        for key in adjusted_profile:
            if key not in ['name', 'error_rate']:  # Don't modify name or error rate
                adjusted_profile[key] *= difficulty_modifier
                adjusted_profile[key] = min(1.0, adjusted_profile[key])
        
        # Adjust error rate (lower difficulty = higher error rate)
        if difficulty_modifier < 1.0:
            adjusted_profile['error_rate'] *= (2.0 - difficulty_modifier)
            adjusted_profile['error_rate'] = min(0.5, adjusted_profile['error_rate'])
        
        # Apply aggressiveness and risk tolerance
        aggressiveness_impact = (ai_player.ai_aggressiveness - 0.5) * 0.2
        risk_impact = (ai_player.ai_risk_tolerance - 0.5) * 0.15
        
        adjusted_profile['reaction_speed'] += aggressiveness_impact
        adjusted_profile['risk_assessment'] += risk_impact
        
        # Clamp all values between 0 and 1
        for key, value in adjusted_profile.items():
            if isinstance(value, (int, float)) and key != 'name':
                adjusted_profile[key] = max(0.0, min(1.0, value))
        
        return adjusted_profile
    
    def _scale_decision_category(self, decisions: Dict, profile: Dict, 
                               category: str) -> Dict:
        """Scale decisions for a specific category based on difficulty profile"""
        
        scaled_decisions = decisions.copy()
        
        if category == 'production':
            scaled_decisions = self._scale_production_decisions(decisions, profile)
        elif category == 'procurement':
            scaled_decisions = self._scale_procurement_decisions(decisions, profile)
        elif category == 'pricing' or category == 'sales':
            scaled_decisions = self._scale_pricing_decisions(decisions, profile)
        elif category == 'financial':
            scaled_decisions = self._scale_financial_decisions(decisions, profile)
        elif category == 'market':
            scaled_decisions = self._scale_market_decisions(decisions, profile)
        
        # Apply general decision accuracy scaling
        scaled_decisions = self._apply_accuracy_scaling(scaled_decisions, profile)
        
        return scaled_decisions
    
    def _scale_production_decisions(self, decisions: Dict, profile: Dict) -> Dict:
        """Scale production decisions based on difficulty"""
        scaled = decisions.copy()
        
        # Scale target volume based on strategic planning ability
        if 'target_volume' in scaled:
            planning_factor = profile['strategic_planning']
            accuracy_factor = profile['decision_accuracy']
            
            # Lower difficulty may over or under-produce
            if planning_factor < 0.7:
                volume_error = (1.0 - planning_factor) * 0.3
                error_direction = 1 if random.random() > 0.5 else -1
                scaled['target_volume'] = int(
                    scaled['target_volume'] * (1 + error_direction * volume_error)
                )
            
            # Apply accuracy scaling
            scaled['target_volume'] = max(1, int(
                scaled['target_volume'] * accuracy_factor
            ))
        
        # Scale bike priorities based on market analysis depth
        if 'bike_priorities' in scaled:
            analysis_depth = profile['market_analysis_depth']
            
            # Lower analysis depth = less accurate priorities
            if analysis_depth < 0.8:
                for bike_type in scaled['bike_priorities']:
                    noise_factor = (1 - analysis_depth) * 0.3
                    noise = random.uniform(-noise_factor, noise_factor)
                    scaled['bike_priorities'][bike_type] = max(0.1, min(1.0,
                        scaled['bike_priorities'][bike_type] + noise
                    ))
        
        return scaled
    
    def _scale_procurement_decisions(self, decisions: Dict, profile: Dict) -> Dict:
        """Scale procurement decisions based on difficulty"""
        scaled = decisions.copy()
        
        optimization_level = profile['optimization_level']
        
        # Adjust inventory target based on optimization level
        if 'inventory_target' in scaled:
            if optimization_level < 0.6:
                # Lower optimization might choose suboptimal inventory levels
                targets = ['minimal', 'low', 'medium', 'high', 'optimal']
                current_idx = targets.index(scaled['inventory_target']) if scaled['inventory_target'] in targets else 2
                
                # Add some randomness for lower difficulty
                noise = random.randint(-1, 1)
                new_idx = max(0, min(len(targets) - 1, current_idx + noise))
                scaled['inventory_target'] = targets[new_idx]
        
        return scaled
    
    def _scale_pricing_decisions(self, decisions: Dict, profile: Dict) -> Dict:
        """Scale pricing decisions based on difficulty"""
        scaled = decisions.copy()
        
        market_analysis = profile['market_analysis_depth']
        decision_accuracy = profile['decision_accuracy']
        
        # Scale pricing accuracy
        if 'margin_target' in scaled:
            if market_analysis < 0.8:
                # Less accurate market analysis = less optimal pricing
                error_range = (1 - market_analysis) * 0.1  # Up to 10% error
                error = random.uniform(-error_range, error_range)
                scaled['margin_target'] = max(0.05, min(0.5,
                    scaled['margin_target'] + error
                ))
        
        # Scale discount factor for competitive pricing
        if 'discount_factor' in scaled:
            if decision_accuracy < 0.7:
                # Lower accuracy might over-discount or under-discount
                error_range = (1 - decision_accuracy) * 0.05  # Up to 5% error
                error = random.uniform(-error_range, error_range)
                scaled['discount_factor'] = max(0.0, min(0.3,
                    scaled['discount_factor'] + error
                ))
        
        return scaled
    
    def _scale_financial_decisions(self, decisions: Dict, profile: Dict) -> Dict:
        """Scale financial decisions based on difficulty"""
        scaled = decisions.copy()
        
        risk_assessment = profile['risk_assessment']
        strategic_planning = profile['strategic_planning']
        
        # Adjust debt tolerance based on risk assessment
        if 'debt_tolerance' in scaled and risk_assessment < 0.7:
            tolerance_levels = ['low', 'moderate', 'high']
            
            if scaled['debt_tolerance'] in tolerance_levels:
                current_idx = tolerance_levels.index(scaled['debt_tolerance'])
                
                # Lower risk assessment might make suboptimal debt decisions
                if random.random() > risk_assessment:
                    # Make a suboptimal choice
                    new_idx = random.choice([i for i in range(len(tolerance_levels)) if i != current_idx])
                    scaled['debt_tolerance'] = tolerance_levels[new_idx]
        
        return scaled
    
    def _scale_market_decisions(self, decisions: Dict, profile: Dict) -> Dict:
        """Scale market strategy decisions based on difficulty"""
        scaled = decisions.copy()
        
        strategic_planning = profile['strategic_planning']
        market_analysis = profile['market_analysis_depth']
        
        # Scale market entry strategy
        if 'market_entry' in scaled and strategic_planning < 0.8:
            strategies = ['conservative', 'selective', 'opportunistic', 'expansive', 'aggressive']
            
            if scaled['market_entry'] in strategies:
                current_idx = strategies.index(scaled['market_entry'])
                
                # Lower strategic planning might choose less optimal strategies
                planning_error = 1 - strategic_planning
                if random.random() < planning_error:
                    noise = random.randint(-1, 1)
                    new_idx = max(0, min(len(strategies) - 1, current_idx + noise))
                    scaled['market_entry'] = strategies[new_idx]
        
        return scaled
    
    def _apply_accuracy_scaling(self, decisions: Dict, profile: Dict) -> Dict:
        """Apply general accuracy scaling to all decisions"""
        
        error_rate = profile['error_rate']
        
        # Randomly introduce errors based on error rate
        if random.random() < error_rate:
            # Introduce a random error in decision
            decision_keys = list(decisions.keys())
            if decision_keys:
                error_key = random.choice(decision_keys)
                
                # Apply error based on decision type
                if isinstance(decisions[error_key], (int, float)):
                    # Numerical error
                    error_magnitude = random.uniform(0.8, 1.2)
                    decisions[error_key] = decisions[error_key] * error_magnitude
                elif isinstance(decisions[error_key], str):
                    # Strategy error - might choose suboptimal option
                    # This would need specific handling per decision type
                    pass
        
        return decisions
    
    def adjust_ai_performance_dynamically(self, ai_player: PlayerSession,
                                        performance_metrics: Dict) -> None:
        """Dynamically adjust AI performance based on game balance"""
        
        # Get current performance relative to human players
        relative_performance = performance_metrics.get('relative_performance', 1.0)
        
        # If AI is significantly outperforming humans, reduce difficulty
        if relative_performance > 1.3:  # AI is 30% better than humans
            adjustment = -0.05
        elif relative_performance < 0.7:  # AI is 30% worse than humans
            adjustment = 0.05
        else:
            adjustment = 0.0
        
        # Apply adjustment
        if adjustment != 0.0:
            ai_player.ai_difficulty = max(0.3, min(1.5, 
                ai_player.ai_difficulty + adjustment
            ))
            ai_player.save()
    
    def get_difficulty_description(self, ai_player: PlayerSession) -> str:
        """Get human-readable description of AI difficulty"""
        
        base_profile = self.DIFFICULTY_PROFILES.get(
            self.base_difficulty,
            self.DIFFICULTY_PROFILES['medium']
        )
        
        adjusted_profile = self._apply_individual_modifiers(ai_player, base_profile)
        
        difficulty_level = adjusted_profile['decision_accuracy']
        
        if difficulty_level < 0.4:
            return "Beginner - Makes basic mistakes, slow to adapt"
        elif difficulty_level < 0.6:
            return "Novice - Learning the ropes, some poor decisions"
        elif difficulty_level < 0.8:
            return "Experienced - Solid competitor, makes good decisions"
        elif difficulty_level < 0.9:
            return "Expert - Strong strategic thinking, quick adaptation"
        else:
            return "Master - Near-optimal play, formidable opponent"