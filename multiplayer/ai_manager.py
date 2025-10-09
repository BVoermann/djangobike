import random
import math
from decimal import Decimal
from typing import Dict, List, Tuple, Optional, Any
from django.db import transaction, models
from django.utils import timezone
from abc import ABC, abstractmethod

from bikeshop.models import GameSession, BikeType, Component, BikePrice
from sales.models import Market, MarketDemand, SalesOrder
from production.models import ProductionPlan, ProducedBike
from procurement.models import ProcurementOrder, Supplier
from warehouse.models import ComponentStock, Warehouse
from finance.models import Credit, Transaction, MonthlyReport
from workers.models import Worker

from .models import PlayerSession, TurnState, MultiplayerGame, GameEvent
from competitors.models import (
    AICompetitor, CompetitorProduction, CompetitorSale, 
    MarketCompetition, CompetitorStrategy
)


class AIPersonality(ABC):
    """Abstract base class for AI personalities"""
    
    def __init__(self, player_session: PlayerSession):
        self.player_session = player_session
        self.difficulty = player_session.ai_difficulty
        self.aggressiveness = player_session.ai_aggressiveness
        self.risk_tolerance = player_session.ai_risk_tolerance
        
    @abstractmethod
    def get_production_strategy(self, market_data: Dict) -> Dict:
        """Returns production decisions for this personality"""
        pass
        
    @abstractmethod
    def get_pricing_strategy(self, competition_data: Dict) -> Dict:
        """Returns pricing decisions for this personality"""
        pass
        
    @abstractmethod
    def get_procurement_strategy(self, inventory_data: Dict) -> Dict:
        """Returns procurement decisions for this personality"""
        pass
        
    @abstractmethod
    def get_market_strategy(self, market_analysis: Dict) -> Dict:
        """Returns market selection and positioning strategy"""
        pass
        
    @abstractmethod
    def get_financial_strategy(self, financial_state: Dict) -> Dict:
        """Returns financial management decisions"""
        pass


class AggressivePersonality(AIPersonality):
    """Aggressive AI that focuses on market dominance and rapid growth"""
    
    def get_production_strategy(self, market_data: Dict) -> Dict:
        # Aggressive strategy: produce at high capacity, focus on volume
        production_capacity = self._calculate_production_capacity()
        
        # Prioritize high-demand bike types
        bike_priorities = self._get_aggressive_bike_priorities(market_data)
        
        # Favor higher production volumes
        volume_multiplier = 1.2 + (self.aggressiveness * 0.3)
        
        return {
            'target_volume': int(production_capacity * volume_multiplier),
            'bike_priorities': bike_priorities,
            'quality_vs_speed': 'speed',  # Prioritize quantity over quality
            'segment_focus': ['standard', 'cheap'],  # Volume segments
            'risk_factor': 0.8  # High risk tolerance
        }
    
    def get_pricing_strategy(self, competition_data: Dict) -> Dict:
        # Aggressive pricing: undercut competitors to gain market share
        base_pricing = self._get_base_pricing()
        
        competitive_discount = 0.05 + (self.aggressiveness * 0.1)  # 5-15% discount
        price_elasticity = 0.8  # Responsive to price changes
        
        return {
            'pricing_method': 'competitive_undercut',
            'discount_factor': competitive_discount,
            'price_elasticity': price_elasticity,
            'market_penetration': True,
            'response_speed': 'fast'  # Quick price adjustments
        }
    
    def get_procurement_strategy(self, inventory_data: Dict) -> Dict:
        # Aggressive procurement: bulk buying, multiple suppliers
        return {
            'ordering_strategy': 'bulk_advantage',
            'supplier_diversification': True,
            'inventory_target': 'high',  # Keep high inventory for production
            'cost_optimization': 'moderate',
            'lead_time_buffer': 'minimal'  # Risk tolerance for shorter lead times
        }
    
    def get_market_strategy(self, market_analysis: Dict) -> Dict:
        # Aggressive market strategy: enter all profitable markets
        return {
            'market_entry': 'expansive',  # Enter multiple markets
            'geographic_spread': 'wide',
            'market_share_target': 'dominance',
            'competitive_response': 'aggressive',
            'investment_approach': 'high_risk_high_reward'
        }
    
    def get_financial_strategy(self, financial_state: Dict) -> Dict:
        # Aggressive financial strategy: leverage debt for growth
        return {
            'debt_tolerance': 'high',
            'growth_investment': 'aggressive',
            'cash_reserve': 'minimal',  # Use cash for expansion
            'credit_utilization': 'maximum',
            'roi_requirements': 'moderate'  # Accept lower ROI for market share
        }
    
    def _calculate_production_capacity(self) -> int:
        # Simplified capacity calculation
        return int(self.player_session.balance / 1000) + 50
    
    def _get_aggressive_bike_priorities(self, market_data: Dict) -> Dict:
        # Prioritize bikes with high demand and growth potential
        priorities = {}
        for bike_type, data in market_data.get('bike_demand', {}).items():
            # High priority for high-demand, growing markets
            priority = data.get('demand_score', 0.5) * data.get('growth_rate', 1.0)
            priorities[bike_type] = min(1.0, priority)
        return priorities
    
    def _get_base_pricing(self) -> Dict:
        # Base pricing strategy for aggressive personality
        return {
            'margin_target': 0.15,  # Lower margins for competitiveness
            'cost_plus_factor': 1.15
        }


class ConservativePersonality(AIPersonality):
    """Conservative AI that focuses on stability and risk management"""
    
    def get_production_strategy(self, market_data: Dict) -> Dict:
        production_capacity = self._calculate_production_capacity()
        
        # Conservative: produce based on confirmed demand
        safety_factor = 0.8 - (self.risk_tolerance * 0.2)
        
        return {
            'target_volume': int(production_capacity * safety_factor),
            'bike_priorities': self._get_conservative_bike_priorities(market_data),
            'quality_vs_speed': 'quality',  # Focus on quality
            'segment_focus': ['premium', 'standard'],  # Higher margin segments
            'risk_factor': 0.3  # Low risk tolerance
        }
    
    def get_pricing_strategy(self, competition_data: Dict) -> Dict:
        return {
            'pricing_method': 'cost_plus_premium',
            'margin_target': 0.25,  # Higher margins
            'price_stability': True,  # Stable pricing
            'market_penetration': False,
            'response_speed': 'slow'  # Gradual price adjustments
        }
    
    def get_procurement_strategy(self, inventory_data: Dict) -> Dict:
        return {
            'ordering_strategy': 'safety_stock',
            'supplier_diversification': True,
            'inventory_target': 'high',  # High safety stock
            'cost_optimization': 'high',  # Focus on cost control
            'lead_time_buffer': 'generous'  # Longer lead time buffers
        }
    
    def get_market_strategy(self, market_analysis: Dict) -> Dict:
        return {
            'market_entry': 'selective',  # Enter only proven markets
            'geographic_spread': 'focused',
            'market_share_target': 'sustainable',
            'competitive_response': 'defensive',
            'investment_approach': 'low_risk_steady_return'
        }
    
    def get_financial_strategy(self, financial_state: Dict) -> Dict:
        return {
            'debt_tolerance': 'low',
            'growth_investment': 'conservative',
            'cash_reserve': 'high',  # Maintain high cash reserves
            'credit_utilization': 'minimal',
            'roi_requirements': 'high'  # Require higher ROI
        }
    
    def _calculate_production_capacity(self) -> int:
        return int(self.player_session.balance / 1500) + 30  # More conservative capacity
    
    def _get_conservative_bike_priorities(self, market_data: Dict) -> Dict:
        priorities = {}
        for bike_type, data in market_data.get('bike_demand', {}).items():
            # Priority based on stability and profitability
            stability_score = data.get('volatility', 1.0)
            profit_score = data.get('profit_margin', 0.5)
            priority = (profit_score * 0.7) + ((1 - stability_score) * 0.3)
            priorities[bike_type] = priority
        return priorities


class InnovativePersonality(AIPersonality):
    """Innovative AI that focuses on new technologies and market disruption"""
    
    def get_production_strategy(self, market_data: Dict) -> Dict:
        production_capacity = self._calculate_production_capacity()
        
        # Focus on innovative bike types (e-bikes, high-tech models)
        innovation_factor = 0.9 + (self.risk_tolerance * 0.3)
        
        return {
            'target_volume': int(production_capacity * innovation_factor),
            'bike_priorities': self._get_innovative_bike_priorities(market_data),
            'quality_vs_speed': 'innovation',  # Focus on new features
            'segment_focus': ['premium', 'specialty'],
            'risk_factor': 0.7  # High risk for innovation
        }
    
    def get_pricing_strategy(self, competition_data: Dict) -> Dict:
        return {
            'pricing_method': 'value_based',
            'innovation_premium': 0.15,  # 15% premium for innovation
            'early_adopter_pricing': True,
            'market_penetration': False,
            'response_speed': 'adaptive'
        }
    
    def get_procurement_strategy(self, inventory_data: Dict) -> Dict:
        return {
            'ordering_strategy': 'technology_focus',
            'supplier_diversification': True,
            'inventory_target': 'lean',  # Lean inventory for agility
            'cost_optimization': 'moderate',
            'innovation_components': True  # Prioritize advanced components
        }
    
    def get_market_strategy(self, market_analysis: Dict) -> Dict:
        return {
            'market_entry': 'first_mover',  # Enter new markets early
            'geographic_spread': 'strategic',
            'market_share_target': 'niche_dominance',
            'competitive_response': 'differentiation',
            'investment_approach': 'innovation_focused'
        }
    
    def get_financial_strategy(self, financial_state: Dict) -> Dict:
        return {
            'debt_tolerance': 'moderate',
            'growth_investment': 'innovation_heavy',
            'cash_reserve': 'moderate',
            'credit_utilization': 'strategic',
            'roi_requirements': 'patient_capital'  # Accept longer payback periods
        }
    
    def _calculate_production_capacity(self) -> int:
        return int(self.player_session.balance / 1200) + 40
    
    def _get_innovative_bike_priorities(self, market_data: Dict) -> Dict:
        priorities = {}
        for bike_type, data in market_data.get('bike_demand', {}).items():
            # High priority for e-bikes and tech-forward bikes
            innovation_score = 0.5
            if 'e-' in bike_type.lower() or 'electric' in bike_type.lower():
                innovation_score = 0.9
            elif any(tech in bike_type.lower() for tech in ['smart', 'digital', 'carbon']):
                innovation_score = 0.8
            elif 'mountain' in bike_type.lower() or 'racing' in bike_type.lower():
                innovation_score = 0.7
            
            priorities[bike_type] = innovation_score
        return priorities


class BalancedPersonality(AIPersonality):
    """Balanced AI that adapts strategy based on market conditions"""
    
    def get_production_strategy(self, market_data: Dict) -> Dict:
        production_capacity = self._calculate_production_capacity()
        
        # Adaptive production based on market conditions
        market_confidence = self._assess_market_confidence(market_data)
        production_factor = 0.85 + (market_confidence * 0.3)
        
        return {
            'target_volume': int(production_capacity * production_factor),
            'bike_priorities': self._get_balanced_bike_priorities(market_data),
            'quality_vs_speed': 'balanced',
            'segment_focus': ['standard', 'premium', 'cheap'],  # Diversified
            'risk_factor': 0.5  # Moderate risk
        }
    
    def get_pricing_strategy(self, competition_data: Dict) -> Dict:
        return {
            'pricing_method': 'market_adaptive',
            'margin_target': 0.20,  # Balanced margins
            'competitive_responsiveness': True,
            'market_penetration': 'conditional',
            'response_speed': 'moderate'
        }
    
    def get_procurement_strategy(self, inventory_data: Dict) -> Dict:
        return {
            'ordering_strategy': 'optimized_balance',
            'supplier_diversification': True,
            'inventory_target': 'optimal',
            'cost_optimization': 'high',
            'flexibility': True  # Adapt to changing conditions
        }
    
    def get_market_strategy(self, market_analysis: Dict) -> Dict:
        return {
            'market_entry': 'opportunistic',
            'geographic_spread': 'balanced',
            'market_share_target': 'profitable_growth',
            'competitive_response': 'strategic',
            'investment_approach': 'balanced_portfolio'
        }
    
    def get_financial_strategy(self, financial_state: Dict) -> Dict:
        return {
            'debt_tolerance': 'moderate',
            'growth_investment': 'balanced',
            'cash_reserve': 'optimal',
            'credit_utilization': 'strategic',
            'roi_requirements': 'market_competitive'
        }
    
    def _calculate_production_capacity(self) -> int:
        return int(self.player_session.balance / 1100) + 45
    
    def _assess_market_confidence(self, market_data: Dict) -> float:
        # Assess overall market conditions to inform strategy
        confidence_factors = []
        
        for market, data in market_data.get('markets', {}).items():
            growth_rate = data.get('growth_rate', 1.0)
            competition_level = data.get('competition_intensity', 0.5)
            demand_stability = data.get('demand_stability', 0.5)
            
            market_confidence = (growth_rate + demand_stability - competition_level) / 2
            confidence_factors.append(market_confidence)
        
        return sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.5
    
    def _get_balanced_bike_priorities(self, market_data: Dict) -> Dict:
        priorities = {}
        for bike_type, data in market_data.get('bike_demand', {}).items():
            # Balanced approach considering multiple factors
            demand_score = data.get('demand_score', 0.5)
            profit_score = data.get('profit_margin', 0.5)
            competition_score = 1 - data.get('competition_intensity', 0.5)
            
            priority = (demand_score * 0.4) + (profit_score * 0.4) + (competition_score * 0.2)
            priorities[bike_type] = priority
        return priorities


class MultiplayerAIManager:
    """Advanced AI manager for multiplayer bike shop simulation"""
    
    PERSONALITY_CLASSES = {
        'aggressive': AggressivePersonality,
        'conservative': ConservativePersonality,
        'innovative': InnovativePersonality,
        'balanced': BalancedPersonality,
        'cheap_only': ConservativePersonality,  # Map existing strategies
        'premium_focus': InnovativePersonality,
        'e_bike_specialist': InnovativePersonality,
    }
    
    DIFFICULTY_MULTIPLIERS = {
        'easy': {
            'decision_quality': 0.6,
            'adaptation_speed': 0.4,
            'market_analysis': 0.5,
            'optimization_level': 0.3
        },
        'medium': {
            'decision_quality': 0.8,
            'adaptation_speed': 0.7,
            'market_analysis': 0.8,
            'optimization_level': 0.6
        },
        'hard': {
            'decision_quality': 0.95,
            'adaptation_speed': 0.9,
            'market_analysis': 0.95,
            'optimization_level': 0.85
        },
        'expert': {
            'decision_quality': 1.0,
            'adaptation_speed': 1.0,
            'market_analysis': 1.0,
            'optimization_level': 1.0
        }
    }
    
    def __init__(self, multiplayer_game: MultiplayerGame):
        self.game = multiplayer_game
        self.ai_players = PlayerSession.objects.filter(
            multiplayer_game=multiplayer_game,
            player_type='ai',
            is_active=True,
            is_bankrupt=False
        )
        self.market_intelligence = MarketIntelligence(multiplayer_game)
        self.learning_system = AILearningSystem(multiplayer_game)
    
    def initialize_ai_player(self, ai_player: PlayerSession) -> None:
        """Initialize an AI player with default settings and strategies"""
        try:
            # Set AI-specific attributes based on strategy
            strategy_config = {
                'aggressive': {
                    'aggressiveness': 0.8,
                    'risk_tolerance': 0.7,
                    'description': 'Focuses on rapid growth and market domination'
                },
                'conservative': {
                    'aggressiveness': 0.3,
                    'risk_tolerance': 0.2,
                    'description': 'Emphasizes stability and risk management'
                },
                'innovative': {
                    'aggressiveness': 0.6,
                    'risk_tolerance': 0.8,
                    'description': 'Concentrates on new technologies and market disruption'
                },
                'balanced': {
                    'aggressiveness': 0.5,
                    'risk_tolerance': 0.5,
                    'description': 'Adapts strategy based on market conditions'
                }
            }
            
            config = strategy_config.get(ai_player.ai_strategy, strategy_config['balanced'])
            
            # Update AI player attributes
            ai_player.ai_aggressiveness = config['aggressiveness']
            ai_player.ai_risk_tolerance = config['risk_tolerance']
            ai_player.save()
            
            # Create initialization event
            GameEvent.objects.create(
                multiplayer_game=self.game,
                event_type='ai_action',
                message=f"AI player {ai_player.company_name} initialized with {ai_player.ai_strategy} strategy",
                data={
                    'player_id': str(ai_player.id),
                    'strategy': ai_player.ai_strategy,
                    'aggressiveness': ai_player.ai_aggressiveness,
                    'risk_tolerance': ai_player.ai_risk_tolerance,
                    'description': config['description']
                }
            )
            
        except Exception as e:
            # Log error but don't fail completely
            print(f"Warning: Failed to initialize AI player {ai_player.company_name}: {str(e)}")
    
    def make_ai_decisions(self, ai_player: PlayerSession) -> Dict:
        """Make decisions for an AI player and return them as a dictionary"""
        try:
            # Get AI personality
            personality = self._get_ai_personality(ai_player)
            
            # Get market and competition data
            market_data = self.market_intelligence.get_market_analysis(ai_player)
            competition_data = self.market_intelligence.get_competition_analysis(ai_player)
            financial_data = self._get_financial_state(ai_player)
            inventory_data = self._get_inventory_state(ai_player)
            
            # Make strategic decisions
            decisions = {
                'production': personality.get_production_strategy(market_data),
                'procurement': personality.get_procurement_strategy(inventory_data),
                'sales': personality.get_pricing_strategy(competition_data),
                'hr': {'action': 'maintain_current'},  # Simplified
                'finance': personality.get_financial_strategy(financial_data)
            }
            
            return decisions
            
        except Exception as e:
            print(f"Warning: Failed to make AI decisions for {ai_player.company_name}: {str(e)}")
            # Return default decisions
            return {
                'production': {'action': 'continue_current'},
                'procurement': {'action': 'maintain_inventory'},
                'sales': {'action': 'current_prices'},
                'hr': {'action': 'no_changes'},
                'finance': {'action': 'conservative'}
            }
        
    def process_ai_turn(self, month: int, year: int) -> None:
        """Process AI decisions for all AI players in the current turn"""
        
        with transaction.atomic():
            # Update market intelligence and learning
            self.market_intelligence.update_market_data(month, year)
            self.learning_system.update_learning_data()
            
            # Process each AI player
            for ai_player in self.ai_players:
                if ai_player.is_bankrupt or not ai_player.is_active:
                    continue
                    
                try:
                    self._process_ai_player_turn(ai_player, month, year)
                except Exception as e:
                    # Log error but continue with other AI players
                    self._log_ai_error(ai_player, str(e))
                    continue
            
            # Update dynamic difficulty if enabled
            self._update_dynamic_difficulty()
    
    def _process_ai_player_turn(self, ai_player: PlayerSession, month: int, year: int) -> None:
        """Process a single AI player's turn"""
        
        # Get AI personality
        personality = self._get_ai_personality(ai_player)
        
        # Gather intelligence data
        market_data = self.market_intelligence.get_market_analysis(ai_player)
        competition_data = self.market_intelligence.get_competition_analysis(ai_player)
        financial_data = self._get_financial_state(ai_player)
        inventory_data = self._get_inventory_state(ai_player)
        
        # Make strategic decisions
        production_decisions = personality.get_production_strategy(market_data)
        pricing_decisions = personality.get_pricing_strategy(competition_data)
        procurement_decisions = personality.get_procurement_strategy(inventory_data)
        market_decisions = personality.get_market_strategy(market_data)
        financial_decisions = personality.get_financial_strategy(financial_data)
        
        # Apply difficulty scaling
        difficulty_multiplier = self.DIFFICULTY_MULTIPLIERS.get(
            self.game.difficulty, self.DIFFICULTY_MULTIPLIERS['medium']
        )
        
        # Execute decisions with difficulty scaling
        self._execute_production_decisions(ai_player, production_decisions, difficulty_multiplier)
        self._execute_procurement_decisions(ai_player, procurement_decisions, difficulty_multiplier)
        self._execute_pricing_decisions(ai_player, pricing_decisions, difficulty_multiplier)
        self._execute_financial_decisions(ai_player, financial_decisions, difficulty_multiplier)
        
        # Update turn state
        self._update_turn_state(ai_player, month, year, {
            'production': production_decisions,
            'procurement': procurement_decisions,
            'sales': pricing_decisions,
            'finance': financial_decisions
        })
        
        # Learn from decisions
        self.learning_system.record_ai_decisions(ai_player, {
            'production': production_decisions,
            'procurement': procurement_decisions,
            'pricing': pricing_decisions,
            'market': market_decisions,
            'financial': financial_decisions
        })
    
    def _get_ai_personality(self, ai_player: PlayerSession) -> AIPersonality:
        """Get appropriate AI personality for the player"""
        strategy = ai_player.ai_strategy or 'balanced'
        personality_class = self.PERSONALITY_CLASSES.get(strategy, BalancedPersonality)
        return personality_class(ai_player)
    
    def _execute_production_decisions(self, ai_player: PlayerSession, decisions: Dict, difficulty: Dict) -> None:
        """Execute AI production decisions"""
        
        # Apply difficulty scaling to decision quality
        decision_quality = difficulty['decision_quality']
        target_volume = int(decisions['target_volume'] * decision_quality)
        
        # Get bike priorities and scale them
        bike_priorities = decisions.get('bike_priorities', {})
        
        # Create production plan
        try:
            session = self._get_ai_session(ai_player)
            if not session:
                return
                
            # For multiplayer, we need to create decisions in the AI competitor system
            # This is a simplified implementation - in practice you'd integrate more deeply
            
            # Scale production based on difficulty
            if decision_quality < 0.7:
                # Easy/Medium AI makes some suboptimal choices
                target_volume = int(target_volume * random.uniform(0.8, 1.2))
            
            # Log AI production decision
            self._log_ai_action(ai_player, f"Planning production of {target_volume} bikes")
            
        except Exception as e:
            self._log_ai_error(ai_player, f"Production planning error: {str(e)}")
    
    def _execute_procurement_decisions(self, ai_player: PlayerSession, decisions: Dict, difficulty: Dict) -> None:
        """Execute AI procurement decisions"""
        
        try:
            session = self._get_ai_session(ai_player)
            if not session:
                return
                
            strategy = decisions.get('ordering_strategy', 'balanced')
            optimization_level = difficulty['optimization_level']
            
            # Scale procurement efficiency based on difficulty
            if optimization_level < 0.6:
                # Lower difficulty AI may over-order or miss opportunities
                efficiency_factor = random.uniform(0.7, 1.3)
            else:
                efficiency_factor = random.uniform(0.9, 1.1)
            
            self._log_ai_action(ai_player, f"Executing {strategy} procurement strategy")
            
        except Exception as e:
            self._log_ai_error(ai_player, f"Procurement error: {str(e)}")
    
    def _execute_pricing_decisions(self, ai_player: PlayerSession, decisions: Dict, difficulty: Dict) -> None:
        """Execute AI pricing decisions"""
        
        try:
            pricing_method = decisions.get('pricing_method', 'market_adaptive')
            market_analysis_quality = difficulty['market_analysis']
            
            # Scale pricing accuracy based on difficulty
            if market_analysis_quality < 0.7:
                # Lower difficulty AI may price suboptimally
                pricing_accuracy = random.uniform(0.6, 0.9)
            else:
                pricing_accuracy = random.uniform(0.9, 1.0)
            
            self._log_ai_action(ai_player, f"Applying {pricing_method} pricing strategy")
            
        except Exception as e:
            self._log_ai_error(ai_player, f"Pricing error: {str(e)}")
    
    def _execute_financial_decisions(self, ai_player: PlayerSession, decisions: Dict, difficulty: Dict) -> None:
        """Execute AI financial decisions"""
        
        try:
            debt_tolerance = decisions.get('debt_tolerance', 'moderate')
            optimization_level = difficulty['optimization_level']
            
            # Handle credit decisions based on AI strategy
            if debt_tolerance == 'high' and ai_player.balance < 30000:
                # Consider taking credit for expansion
                self._consider_ai_credit(ai_player, optimization_level)
            
            self._log_ai_action(ai_player, f"Managing finances with {debt_tolerance} debt tolerance")
            
        except Exception as e:
            self._log_ai_error(ai_player, f"Financial management error: {str(e)}")
    
    def _consider_ai_credit(self, ai_player: PlayerSession, optimization_level: float) -> None:
        """AI considers taking credit based on optimization level"""
        
        # Higher optimization level means better credit decisions
        if optimization_level > 0.8:
            # Smart AI evaluates creditworthiness and ROI
            if ai_player.balance > -20000:  # Not too deep in debt
                credit_amount = min(50000, abs(ai_player.balance) + 30000)
                self._log_ai_action(ai_player, f"Considering credit of {credit_amount}")
        else:
            # Lower optimization AI may make riskier credit decisions
            if random.random() < 0.3:  # 30% chance of risky credit
                credit_amount = random.randint(20000, 40000)
                self._log_ai_action(ai_player, f"Taking risky credit of {credit_amount}")
    
    def _get_financial_state(self, ai_player: PlayerSession) -> Dict:
        """Get financial state information for AI decision making"""
        return {
            'balance': float(ai_player.balance),
            'total_revenue': float(ai_player.total_revenue),
            'total_profit': float(ai_player.total_profit),
            'debt_ratio': self._calculate_debt_ratio(ai_player),
            'cash_flow_trend': self._calculate_cash_flow_trend(ai_player),
            'liquidity_score': self._calculate_liquidity_score(ai_player)
        }
    
    def _get_inventory_state(self, ai_player: PlayerSession) -> Dict:
        """Get inventory state information for AI decision making"""
        # This would integrate with warehouse system
        return {
            'inventory_level': 'medium',  # Simplified
            'stock_aging': 'normal',
            'turnover_rate': 0.8,
            'stockout_risk': 'low'
        }
    
    def _calculate_debt_ratio(self, ai_player: PlayerSession) -> float:
        """Calculate debt-to-equity ratio for AI player"""
        # Simplified calculation
        if ai_player.balance < 0:
            return abs(float(ai_player.balance)) / max(1000, float(ai_player.total_revenue))
        return 0.0
    
    def _calculate_cash_flow_trend(self, ai_player: PlayerSession) -> str:
        """Calculate cash flow trend for AI player"""
        # This would analyze recent transactions
        return 'stable'  # Simplified
    
    def _calculate_liquidity_score(self, ai_player: PlayerSession) -> float:
        """Calculate liquidity score for AI player"""
        # Simplified liquidity assessment
        if ai_player.balance > 50000:
            return 1.0
        elif ai_player.balance > 20000:
            return 0.8
        elif ai_player.balance > 0:
            return 0.6
        else:
            return 0.3
    
    def _get_ai_session(self, ai_player: PlayerSession) -> Optional[GameSession]:
        """Get game session for AI player - bridge to existing system"""
        # This would need to be implemented based on how multiplayer integrates
        # with the existing GameSession system
        return None
    
    def _update_turn_state(self, ai_player: PlayerSession, month: int, year: int, decisions: Dict) -> None:
        """Update turn state with AI decisions"""
        
        turn_state, created = TurnState.objects.get_or_create(
            multiplayer_game=self.game,
            player_session=ai_player,
            month=month,
            year=year,
            defaults={
                'decisions_submitted': True,
                'auto_submitted': True,
                'submitted_at': timezone.now()
            }
        )
        
        # Store decisions
        turn_state.production_decisions = decisions.get('production', {})
        turn_state.procurement_decisions = decisions.get('procurement', {})
        turn_state.sales_decisions = decisions.get('sales', {})
        turn_state.finance_decisions = decisions.get('finance', {})
        turn_state.save()
    
    def _update_dynamic_difficulty(self) -> None:
        """Update AI difficulty based on game balance"""
        
        if not hasattr(self.game, 'enable_dynamic_difficulty') or not self.game.enable_dynamic_difficulty:
            return
        
        # Analyze human vs AI performance
        human_players = PlayerSession.objects.filter(
            multiplayer_game=self.game,
            player_type='human',
            is_active=True
        )
        
        if not human_players.exists():
            return
        
        # Calculate performance metrics
        human_avg_score = self._calculate_average_performance(human_players)
        ai_avg_score = self._calculate_average_performance(self.ai_players)
        
        # Adjust AI difficulty if imbalance detected
        if human_avg_score < ai_avg_score * 0.7:  # Humans struggling
            self._reduce_ai_difficulty()
        elif human_avg_score > ai_avg_score * 1.3:  # AI too weak
            self._increase_ai_difficulty()
    
    def _calculate_average_performance(self, players) -> float:
        """Calculate average performance score for a group of players"""
        if not players.exists():
            return 0.0
        
        total_score = 0
        for player in players:
            # Simple performance metric: balance + revenue
            score = float(player.balance) + float(player.total_revenue) * 0.1
            total_score += score
        
        return total_score / players.count()
    
    def _reduce_ai_difficulty(self) -> None:
        """Reduce AI difficulty to help struggling human players"""
        for ai_player in self.ai_players:
            if ai_player.ai_difficulty > 0.3:
                ai_player.ai_difficulty *= 0.9
                ai_player.save()
        
        self._log_system_event("AI difficulty reduced to balance gameplay")
    
    def _increase_ai_difficulty(self) -> None:
        """Increase AI difficulty to challenge dominant human players"""
        for ai_player in self.ai_players:
            if ai_player.ai_difficulty < 1.8:
                ai_player.ai_difficulty *= 1.1
                ai_player.save()
        
        self._log_system_event("AI difficulty increased to maintain challenge")
    
    def _log_ai_action(self, ai_player: PlayerSession, message: str) -> None:
        """Log AI action for transparency and debugging"""
        GameEvent.objects.create(
            multiplayer_game=self.game,
            event_type='ai_action',
            message=f"{ai_player.company_name}: {message}",
            data={'player_id': str(ai_player.id), 'ai_strategy': ai_player.ai_strategy}
        )
    
    def _log_ai_error(self, ai_player: PlayerSession, error_message: str) -> None:
        """Log AI errors for debugging"""
        GameEvent.objects.create(
            multiplayer_game=self.game,
            event_type='system_message',
            message=f"AI Error - {ai_player.company_name}: {error_message}",
            data={'player_id': str(ai_player.id), 'error': error_message},
            visible_to_all=False  # Internal logging
        )
    
    def _log_system_event(self, message: str) -> None:
        """Log system events"""
        GameEvent.objects.create(
            multiplayer_game=self.game,
            event_type='system_message',
            message=message,
            data={},
            visible_to_all=False
        )


class MarketIntelligence:
    """Market analysis and intelligence system for AI decision making"""
    
    def __init__(self, multiplayer_game: MultiplayerGame):
        self.game = multiplayer_game
        self.market_data_cache = {}
        self.competition_data_cache = {}
    
    def update_market_data(self, month: int, year: int) -> None:
        """Update market intelligence data"""
        
        # Gather market demand data
        markets = Market.objects.filter(session__isnull=True)  # Adjust based on your model structure
        
        market_analysis = {}
        for market in markets:
            market_analysis[market.name] = {
                'demand_trend': self._calculate_demand_trend(market, month, year),
                'competition_intensity': self._calculate_competition_intensity(market),
                'growth_rate': self._calculate_growth_rate(market),
                'profit_potential': self._calculate_profit_potential(market),
                'volatility': self._calculate_market_volatility(market)
            }
        
        self.market_data_cache = {
            'markets': market_analysis,
            'bike_demand': self._analyze_bike_demand(month, year),
            'last_updated': timezone.now()
        }
    
    def get_market_analysis(self, ai_player: PlayerSession) -> Dict:
        """Get market analysis tailored for specific AI player"""
        base_data = self.market_data_cache.copy()
        
        # Add player-specific analysis
        base_data['player_position'] = self._analyze_player_position(ai_player)
        base_data['opportunities'] = self._identify_opportunities(ai_player)
        base_data['threats'] = self._identify_threats(ai_player)
        
        return base_data
    
    def get_competition_analysis(self, ai_player: PlayerSession) -> Dict:
        """Get competitive analysis for AI player"""
        competitors = PlayerSession.objects.filter(
            multiplayer_game=self.game,
            is_active=True
        ).exclude(id=ai_player.id)
        
        analysis = {
            'competitor_count': competitors.count(),
            'market_leaders': self._identify_market_leaders(competitors),
            'competitive_threats': self._identify_competitive_threats(ai_player, competitors),
            'pricing_pressure': self._calculate_pricing_pressure(),
            'market_concentration': self._calculate_market_concentration(competitors)
        }
        
        return analysis
    
    def _calculate_demand_trend(self, market, month: int, year: int) -> float:
        """Calculate demand trend for a market"""
        # Seasonal and cyclical factors
        seasonal_factor = 1.0
        if month in [3, 4, 5, 6]:  # Spring/Summer boost
            seasonal_factor = 1.2
        elif month in [11, 12, 1, 2]:  # Winter decline
            seasonal_factor = 0.8
        
        # Economic cycle (simplified)
        year_factor = 1.0 + ((year % 5) - 2) * 0.1  # 5-year cycle
        
        return seasonal_factor * year_factor
    
    def _calculate_competition_intensity(self, market) -> float:
        """Calculate competition intensity in market"""
        # Count active competitors in market
        active_players = PlayerSession.objects.filter(
            multiplayer_game=self.game,
            is_active=True,
            is_bankrupt=False
        ).count()
        
        # Normalize to 0-1 scale
        return min(1.0, active_players / 8.0)  # 8+ players = maximum competition
    
    def _calculate_growth_rate(self, market) -> float:
        """Calculate market growth rate"""
        # This would analyze historical data
        # For now, return a simulated growth rate
        return random.uniform(0.95, 1.15)  # -5% to +15% growth
    
    def _calculate_profit_potential(self, market) -> float:
        """Calculate profit potential for market"""
        # Factors: competition, growth, margins
        competition_intensity = self._calculate_competition_intensity(market)
        growth_rate = self._calculate_growth_rate(market)
        
        # Lower competition and higher growth = higher profit potential
        profit_potential = (1 - competition_intensity) * growth_rate
        return min(1.0, profit_potential)
    
    def _calculate_market_volatility(self, market) -> float:
        """Calculate market volatility/stability"""
        # Simplified volatility calculation
        # Higher volatility for newer markets, lower for established ones
        return random.uniform(0.2, 0.8)
    
    def _analyze_bike_demand(self, month: int, year: int) -> Dict:
        """Analyze demand for different bike types"""
        bike_types = BikeType.objects.all()[:10]  # Limit for performance
        
        demand_analysis = {}
        for bike_type in bike_types:
            demand_analysis[bike_type.name] = {
                'demand_score': self._calculate_bike_demand_score(bike_type, month),
                'profit_margin': self._estimate_profit_margin(bike_type),
                'competition_intensity': random.uniform(0.3, 0.9),
                'growth_rate': random.uniform(0.9, 1.2),
                'volatility': random.uniform(0.2, 0.8)
            }
        
        return demand_analysis
    
    def _calculate_bike_demand_score(self, bike_type, month: int) -> float:
        """Calculate demand score for bike type"""
        base_score = 0.5
        
        # Seasonal adjustments
        name = bike_type.name.lower()
        if month in [3, 4, 5, 6, 7, 8]:  # Spring/Summer
            if 'mountain' in name or 'racing' in name:
                base_score += 0.3
            elif 'city' in name or 'e-' in name:
                base_score += 0.2
        
        # Winter adjustments
        if month in [11, 12, 1, 2]:
            if 'indoor' in name or 'trainer' in name:
                base_score += 0.2
            else:
                base_score -= 0.2
        
        return max(0.1, min(1.0, base_score))
    
    def _estimate_profit_margin(self, bike_type) -> float:
        """Estimate profit margin for bike type"""
        # Simplified margin estimation
        name = bike_type.name.lower()
        
        if 'premium' in name or 'carbon' in name:
            return random.uniform(0.4, 0.6)  # High margin
        elif 'e-' in name:
            return random.uniform(0.3, 0.5)  # Good margin
        elif 'basic' in name or 'entry' in name:
            return random.uniform(0.1, 0.3)  # Low margin
        else:
            return random.uniform(0.2, 0.4)  # Standard margin
    
    def _analyze_player_position(self, ai_player: PlayerSession) -> Dict:
        """Analyze AI player's current market position"""
        competitors = PlayerSession.objects.filter(
            multiplayer_game=self.game,
            is_active=True
        )
        
        if not competitors.exists():
            return {'rank': 1, 'percentile': 100}
        
        # Sort by total revenue (simplified ranking)
        sorted_players = sorted(competitors, key=lambda p: p.total_revenue, reverse=True)
        
        try:
            rank = next(i for i, p in enumerate(sorted_players, 1) if p.id == ai_player.id)
            percentile = ((len(sorted_players) - rank + 1) / len(sorted_players)) * 100
        except StopIteration:
            rank = len(sorted_players)
            percentile = 0
        
        return {
            'rank': rank,
            'percentile': percentile,
            'total_players': len(sorted_players),
            'performance_category': self._categorize_performance(percentile)
        }
    
    def _categorize_performance(self, percentile: float) -> str:
        """Categorize performance based on percentile"""
        if percentile >= 80:
            return 'leading'
        elif percentile >= 60:
            return 'strong'
        elif percentile >= 40:
            return 'average'
        elif percentile >= 20:
            return 'struggling'
        else:
            return 'critical'
    
    def _identify_opportunities(self, ai_player: PlayerSession) -> List[Dict]:
        """Identify market opportunities for AI player"""
        opportunities = []
        
        # Market expansion opportunities
        for market_name, data in self.market_data_cache.get('markets', {}).items():
            if data['competition_intensity'] < 0.6 and data['growth_rate'] > 1.05:
                opportunities.append({
                    'type': 'market_expansion',
                    'target': market_name,
                    'potential': data['profit_potential'],
                    'risk': 'low'
                })
        
        # Product opportunities
        for bike_type, data in self.market_data_cache.get('bike_demand', {}).items():
            if data['demand_score'] > 0.7 and data['competition_intensity'] < 0.5:
                opportunities.append({
                    'type': 'product_opportunity',
                    'target': bike_type,
                    'potential': data['demand_score'],
                    'risk': 'medium'
                })
        
        return opportunities[:5]  # Limit to top 5 opportunities
    
    def _identify_threats(self, ai_player: PlayerSession) -> List[Dict]:
        """Identify threats for AI player"""
        threats = []
        
        # Competitive threats
        strong_competitors = PlayerSession.objects.filter(
            multiplayer_game=self.game,
            is_active=True,
            total_revenue__gt=ai_player.total_revenue * 1.5
        )
        
        for competitor in strong_competitors:
            threats.append({
                'type': 'competitive_threat',
                'source': competitor.company_name,
                'severity': 'high' if competitor.total_revenue > ai_player.total_revenue * 2 else 'medium'
            })
        
        # Market saturation threats
        for market_name, data in self.market_data_cache.get('markets', {}).items():
            if data['competition_intensity'] > 0.8:
                threats.append({
                    'type': 'market_saturation',
                    'target': market_name,
                    'severity': 'high' if data['competition_intensity'] > 0.9 else 'medium'
                })
        
        return threats[:5]  # Limit to top 5 threats
    
    def _identify_market_leaders(self, competitors) -> List[Dict]:
        """Identify market leaders"""
        leaders = []
        
        # Sort by revenue and take top performers
        top_performers = sorted(
            competitors, 
            key=lambda p: p.total_revenue, 
            reverse=True
        )[:3]
        
        for i, competitor in enumerate(top_performers, 1):
            leaders.append({
                'rank': i,
                'company': competitor.company_name,
                'revenue': float(competitor.total_revenue),
                'market_share': self._estimate_market_share(competitor, competitors)
            })
        
        return leaders
    
    def _estimate_market_share(self, player: PlayerSession, all_competitors) -> float:
        """Estimate market share for a player"""
        total_revenue = sum(p.total_revenue for p in all_competitors)
        if total_revenue > 0:
            return (float(player.total_revenue) / float(total_revenue)) * 100
        return 0.0
    
    def _identify_competitive_threats(self, ai_player: PlayerSession, competitors) -> List[Dict]:
        """Identify specific competitive threats"""
        threats = []
        
        for competitor in competitors:
            if competitor.total_revenue > ai_player.total_revenue:
                threat_level = 'high' if competitor.total_revenue > ai_player.total_revenue * 1.5 else 'medium'
                threats.append({
                    'company': competitor.company_name,
                    'threat_level': threat_level,
                    'advantage': 'revenue_leader' if competitor.total_revenue > ai_player.total_revenue * 2 else 'revenue_advantage'
                })
        
        return threats
    
    def _calculate_pricing_pressure(self) -> float:
        """Calculate overall pricing pressure in the market"""
        # Simplified calculation based on competition intensity
        avg_competition = 0.6  # This would be calculated from actual data
        return avg_competition
    
    def _calculate_market_concentration(self, competitors) -> float:
        """Calculate market concentration (HHI-like metric)"""
        if not competitors.exists():
            return 0.0
        
        total_revenue = sum(float(p.total_revenue) for p in competitors)
        if total_revenue == 0:
            return 0.0
        
        # Calculate concentration index
        concentration = sum(
            (float(p.total_revenue) / total_revenue) ** 2 
            for p in competitors
        )
        
        return concentration


class AILearningSystem:
    """Learning and adaptation system for AI players"""
    
    def __init__(self, multiplayer_game: MultiplayerGame):
        self.game = multiplayer_game
        self.learning_data = {}
    
    def update_learning_data(self) -> None:
        """Update learning data based on game history"""
        
        # Analyze human player patterns
        human_players = PlayerSession.objects.filter(
            multiplayer_game=self.game,
            player_type='human'
        )
        
        for human_player in human_players:
            self._analyze_human_patterns(human_player)
        
        # Update AI adaptation parameters
        self._update_adaptation_parameters()
    
    def record_ai_decisions(self, ai_player: PlayerSession, decisions: Dict) -> None:
        """Record AI decisions for learning analysis"""
        
        player_id = str(ai_player.id)
        if player_id not in self.learning_data:
            self.learning_data[player_id] = {
                'decisions_history': [],
                'performance_history': [],
                'adaptation_score': 1.0
            }
        
        # Store decision with timestamp and context
        self.learning_data[player_id]['decisions_history'].append({
            'timestamp': timezone.now(),
            'decisions': decisions,
            'game_state': self._capture_game_state(),
            'performance_before': self._get_player_performance(ai_player)
        })
        
        # Limit history size
        if len(self.learning_data[player_id]['decisions_history']) > 50:
            self.learning_data[player_id]['decisions_history'].pop(0)
    
    def get_adaptation_suggestions(self, ai_player: PlayerSession) -> Dict:
        """Get adaptation suggestions for AI player"""
        
        player_id = str(ai_player.id)
        if player_id not in self.learning_data:
            return {}
        
        history = self.learning_data[player_id]['decisions_history']
        if len(history) < 3:
            return {}
        
        # Analyze recent performance
        recent_decisions = history[-3:]
        performance_trend = self._analyze_performance_trend(recent_decisions)
        
        suggestions = {}
        
        if performance_trend['trend'] == 'declining':
            suggestions['strategy_adjustment'] = 'increase_risk_tolerance'
            suggestions['focus_areas'] = ['market_expansion', 'pricing_optimization']
        elif performance_trend['trend'] == 'stagnant':
            suggestions['strategy_adjustment'] = 'diversify_approach'
            suggestions['focus_areas'] = ['innovation', 'new_markets']
        elif performance_trend['trend'] == 'improving':
            suggestions['strategy_adjustment'] = 'maintain_course'
            suggestions['focus_areas'] = ['optimize_current_strategy']
        
        return suggestions
    
    def _analyze_human_patterns(self, human_player: PlayerSession) -> None:
        """Analyze human player patterns to inform AI counter-strategies"""
        
        # Get turn states for analysis
        recent_turns = TurnState.objects.filter(
            multiplayer_game=self.game,
            player_session=human_player
        ).order_by('-year', '-month')[:6]  # Last 6 months
        
        if not recent_turns.exists():
            return
        
        patterns = {
            'production_pattern': self._analyze_production_pattern(recent_turns),
            'pricing_pattern': self._analyze_pricing_pattern(recent_turns),
            'market_strategy': self._analyze_market_strategy(recent_turns),
            'risk_profile': self._analyze_risk_profile(recent_turns)
        }
        
        # Store patterns for AI adaptation
        player_id = str(human_player.id)
        self.learning_data[f'human_{player_id}'] = patterns
    
    def _analyze_production_pattern(self, turn_states) -> Dict:
        """Analyze human production patterns"""
        # Simplified pattern analysis
        return {
            'consistency': random.uniform(0.3, 0.9),
            'volume_trend': random.choice(['increasing', 'decreasing', 'stable']),
            'bike_preferences': ['standard', 'premium'],  # This would be actual analysis
            'seasonal_adjustment': True
        }
    
    def _analyze_pricing_pattern(self, turn_states) -> Dict:
        """Analyze human pricing patterns"""
        return {
            'strategy_type': random.choice(['aggressive', 'conservative', 'adaptive']),
            'price_elasticity': random.uniform(0.5, 1.5),
            'competitive_response': random.choice(['fast', 'slow', 'none']),
            'margin_target': random.uniform(0.15, 0.35)
        }
    
    def _analyze_market_strategy(self, turn_states) -> Dict:
        """Analyze human market strategy"""
        return {
            'expansion_rate': random.choice(['aggressive', 'moderate', 'conservative']),
            'market_focus': random.choice(['concentrated', 'diversified']),
            'geographic_preference': ['local', 'regional'],  # This would be actual analysis
            'timing_pattern': 'early_adopter'  # or 'follower'
        }
    
    def _analyze_risk_profile(self, turn_states) -> Dict:
        """Analyze human risk profile"""
        return {
            'risk_tolerance': random.uniform(0.2, 0.8),
            'debt_comfort': random.choice(['low', 'medium', 'high']),
            'innovation_adoption': random.choice(['early', 'mainstream', 'late']),
            'crisis_response': random.choice(['aggressive', 'defensive', 'adaptive'])
        }
    
    def _update_adaptation_parameters(self) -> None:
        """Update AI adaptation parameters based on learning"""
        
        # Analyze overall game balance
        human_performance = self._get_average_human_performance()
        ai_performance = self._get_average_ai_performance()
        
        # Adjust AI parameters if imbalance detected
        if human_performance < ai_performance * 0.8:
            self._reduce_ai_aggressiveness()
        elif human_performance > ai_performance * 1.2:
            self._increase_ai_competitiveness()
    
    def _get_average_human_performance(self) -> float:
        """Get average human performance score"""
        human_players = PlayerSession.objects.filter(
            multiplayer_game=self.game,
            player_type='human',
            is_active=True
        )
        
        if not human_players.exists():
            return 0.0
        
        total_score = sum(
            float(p.balance) + float(p.total_revenue) * 0.1 
            for p in human_players
        )
        
        return total_score / human_players.count()
    
    def _get_average_ai_performance(self) -> float:
        """Get average AI performance score"""
        ai_players = PlayerSession.objects.filter(
            multiplayer_game=self.game,
            player_type='ai',
            is_active=True
        )
        
        if not ai_players.exists():
            return 0.0
        
        total_score = sum(
            float(p.balance) + float(p.total_revenue) * 0.1 
            for p in ai_players
        )
        
        return total_score / ai_players.count()
    
    def _reduce_ai_aggressiveness(self) -> None:
        """Reduce AI aggressiveness to help struggling humans"""
        ai_players = PlayerSession.objects.filter(
            multiplayer_game=self.game,
            player_type='ai',
            is_active=True
        )
        
        for ai_player in ai_players:
            if ai_player.ai_aggressiveness > 0.2:
                ai_player.ai_aggressiveness *= 0.9
                ai_player.save()
    
    def _increase_ai_competitiveness(self) -> None:
        """Increase AI competitiveness to challenge dominant humans"""
        ai_players = PlayerSession.objects.filter(
            multiplayer_game=self.game,
            player_type='ai',
            is_active=True
        )
        
        for ai_player in ai_players:
            if ai_player.ai_aggressiveness < 0.9:
                ai_player.ai_aggressiveness *= 1.1
                ai_player.save()
    
    def _capture_game_state(self) -> Dict:
        """Capture current game state for decision context"""
        return {
            'month': self.game.current_month,
            'year': self.game.current_year,
            'active_players': self.game.active_players_count,
            'game_progress': self.game.game_progress_percentage
        }
    
    def _get_player_performance(self, player: PlayerSession) -> Dict:
        """Get player performance metrics"""
        return {
            'balance': float(player.balance),
            'revenue': float(player.total_revenue),
            'profit': float(player.total_profit),
            'market_share': player.market_share
        }
    
    def _analyze_performance_trend(self, recent_decisions: List[Dict]) -> Dict:
        """Analyze performance trend from recent decisions"""
        if len(recent_decisions) < 2:
            return {'trend': 'insufficient_data'}
        
        # Compare first and last performance
        first_performance = recent_decisions[0]['performance_before']
        last_performance = recent_decisions[-1]['performance_before']
        
        revenue_change = (
            last_performance['revenue'] - first_performance['revenue']
        ) / max(1, first_performance['revenue'])
        
        if revenue_change > 0.1:
            return {'trend': 'improving', 'change_rate': revenue_change}
        elif revenue_change < -0.1:
            return {'trend': 'declining', 'change_rate': revenue_change}
        else:
            return {'trend': 'stagnant', 'change_rate': revenue_change}