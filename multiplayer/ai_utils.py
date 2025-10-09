"""
Utility functions and helpers for the multiplayer AI system.
This module provides common functionality used across the AI system.
"""

import random
import math
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Any, Union
from django.utils import timezone
from datetime import timedelta

from .models import PlayerSession, MultiplayerGame, GameEvent


class AIPerformanceAnalyzer:
    """Analyzes AI performance and provides insights for optimization"""
    
    def __init__(self, multiplayer_game: MultiplayerGame):
        self.game = multiplayer_game
    
    def analyze_player_performance(self, player: PlayerSession, 
                                 timeframe_months: int = 6) -> Dict:
        """Analyze performance of a specific player over timeframe"""
        
        performance_data = {
            'financial_health': self._analyze_financial_health(player),
            'market_position': self._analyze_market_position(player),
            'operational_efficiency': self._analyze_operational_efficiency(player),
            'growth_trajectory': self._analyze_growth_trajectory(player, timeframe_months),
            'competitive_standing': self._analyze_competitive_standing(player),
            'risk_profile': self._analyze_risk_profile(player)
        }
        
        # Calculate overall performance score
        performance_data['overall_score'] = self._calculate_overall_score(performance_data)
        performance_data['performance_category'] = self._categorize_performance(
            performance_data['overall_score']
        )
        
        return performance_data
    
    def compare_ai_vs_human_performance(self) -> Dict:
        """Compare AI vs human player performance"""
        
        ai_players = PlayerSession.objects.filter(
            multiplayer_game=self.game,
            player_type='ai',
            is_active=True
        )
        
        human_players = PlayerSession.objects.filter(
            multiplayer_game=self.game,
            player_type='human',
            is_active=True
        )
        
        ai_metrics = self._calculate_group_metrics(ai_players)
        human_metrics = self._calculate_group_metrics(human_players)
        
        return {
            'ai_performance': ai_metrics,
            'human_performance': human_metrics,
            'balance_ratio': self._calculate_balance_ratio(ai_metrics, human_metrics),
            'recommendations': self._generate_balance_recommendations(ai_metrics, human_metrics)
        }
    
    def identify_dominant_strategies(self) -> Dict:
        """Identify which AI strategies are performing best"""
        
        ai_players = PlayerSession.objects.filter(
            multiplayer_game=self.game,
            player_type='ai',
            is_active=True
        )
        
        strategy_performance = {}
        
        for player in ai_players:
            strategy = player.ai_strategy or 'unknown'
            
            if strategy not in strategy_performance:
                strategy_performance[strategy] = {
                    'players': [],
                    'avg_revenue': 0,
                    'avg_profit': 0,
                    'avg_market_share': 0,
                    'success_rate': 0
                }
            
            strategy_performance[strategy]['players'].append({
                'company': player.company_name,
                'revenue': float(player.total_revenue),
                'profit': float(player.total_profit),
                'market_share': player.market_share,
                'balance': float(player.balance)
            })
        
        # Calculate averages
        for strategy, data in strategy_performance.items():
            players = data['players']
            if players:
                data['avg_revenue'] = sum(p['revenue'] for p in players) / len(players)
                data['avg_profit'] = sum(p['profit'] for p in players) / len(players)
                data['avg_market_share'] = sum(p['market_share'] for p in players) / len(players)
                data['success_rate'] = len([p for p in players if p['balance'] > 0]) / len(players)
        
        # Rank strategies
        ranked_strategies = sorted(
            strategy_performance.items(),
            key=lambda x: x[1]['avg_revenue'],
            reverse=True
        )
        
        return {
            'strategy_rankings': ranked_strategies,
            'dominant_strategy': ranked_strategies[0][0] if ranked_strategies else None,
            'strategy_diversity': len(strategy_performance),
            'performance_spread': self._calculate_performance_spread(strategy_performance)
        }
    
    def _analyze_financial_health(self, player: PlayerSession) -> Dict:
        """Analyze financial health metrics"""
        
        balance = float(player.balance)
        total_revenue = float(player.total_revenue)
        total_profit = float(player.total_profit)
        
        # Calculate metrics
        profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
        
        # Determine financial health category
        if balance > 50000:
            health_category = 'excellent'
        elif balance > 20000:
            health_category = 'good'
        elif balance > 0:
            health_category = 'fair'
        elif balance > -20000:
            health_category = 'poor'
        else:
            health_category = 'critical'
        
        return {
            'balance': balance,
            'profit_margin': profit_margin,
            'health_category': health_category,
            'liquidity_ratio': max(0, balance / 50000),  # Normalized liquidity
            'debt_risk': max(0, -balance / 100000) if balance < 0 else 0
        }
    
    def _analyze_market_position(self, player: PlayerSession) -> Dict:
        """Analyze market position relative to competitors"""
        
        all_players = PlayerSession.objects.filter(
            multiplayer_game=self.game,
            is_active=True
        ).order_by('-total_revenue')
        
        try:
            rank = list(all_players).index(player) + 1
        except ValueError:
            rank = len(all_players)
        
        percentile = ((len(all_players) - rank + 1) / len(all_players)) * 100
        
        return {
            'rank': rank,
            'total_players': len(all_players),
            'percentile': percentile,
            'market_share': player.market_share,
            'position_category': self._categorize_market_position(percentile)
        }
    
    def _analyze_operational_efficiency(self, player: PlayerSession) -> Dict:
        """Analyze operational efficiency metrics"""
        
        bikes_produced = player.bikes_produced
        bikes_sold = player.bikes_sold
        total_revenue = float(player.total_revenue)
        
        # Calculate efficiency metrics
        production_efficiency = (bikes_sold / bikes_produced * 100) if bikes_produced > 0 else 0
        revenue_per_bike = (total_revenue / bikes_sold) if bikes_sold > 0 else 0
        
        return {
            'production_efficiency': production_efficiency,
            'sales_conversion': production_efficiency,
            'revenue_per_bike': revenue_per_bike,
            'total_output': bikes_produced,
            'efficiency_category': self._categorize_efficiency(production_efficiency)
        }
    
    def _analyze_growth_trajectory(self, player: PlayerSession, months: int) -> Dict:
        """Analyze growth trajectory over specified months"""
        
        # This would analyze historical data if available
        # For now, provide simplified growth analysis
        
        current_revenue = float(player.total_revenue)
        
        # Simulate growth rate calculation
        # In practice, this would use historical turn data
        growth_rate = random.uniform(-0.1, 0.3)  # -10% to +30%
        
        return {
            'revenue_growth_rate': growth_rate * 100,
            'growth_category': self._categorize_growth(growth_rate),
            'projected_revenue': current_revenue * (1 + growth_rate),
            'momentum': 'positive' if growth_rate > 0.05 else 'negative' if growth_rate < -0.05 else 'stable'
        }
    
    def _analyze_competitive_standing(self, player: PlayerSession) -> Dict:
        """Analyze competitive standing and threats"""
        
        competitors = PlayerSession.objects.filter(
            multiplayer_game=self.game,
            is_active=True
        ).exclude(id=player.id)
        
        stronger_competitors = competitors.filter(
            total_revenue__gt=player.total_revenue
        ).count()
        
        weaker_competitors = competitors.filter(
            total_revenue__lt=player.total_revenue
        ).count()
        
        # Identify closest competitors
        closest_above = competitors.filter(
            total_revenue__gt=player.total_revenue
        ).order_by('total_revenue').first()
        
        closest_below = competitors.filter(
            total_revenue__lt=player.total_revenue
        ).order_by('-total_revenue').first()
        
        return {
            'stronger_competitors': stronger_competitors,
            'weaker_competitors': weaker_competitors,
            'closest_threat': closest_above.company_name if closest_above else None,
            'next_target': closest_below.company_name if closest_below else None,
            'competitive_pressure': stronger_competitors / max(1, len(competitors))
        }
    
    def _analyze_risk_profile(self, player: PlayerSession) -> Dict:
        """Analyze risk profile of player"""
        
        balance = float(player.balance)
        total_revenue = float(player.total_revenue)
        
        # Calculate risk indicators
        financial_risk = 'high' if balance < 0 else 'medium' if balance < 20000 else 'low'
        
        market_risk = 'high' if player.market_share < 5 else 'medium' if player.market_share < 15 else 'low'
        
        operational_risk = 'high' if player.bikes_produced == 0 else 'medium' if player.bikes_sold / max(1, player.bikes_produced) < 0.5 else 'low'
        
        return {
            'financial_risk': financial_risk,
            'market_risk': market_risk,
            'operational_risk': operational_risk,
            'overall_risk': self._calculate_overall_risk(financial_risk, market_risk, operational_risk),
            'bankruptcy_risk': 'high' if balance < -30000 else 'medium' if balance < 0 else 'low'
        }
    
    def _calculate_overall_score(self, performance_data: Dict) -> float:
        """Calculate overall performance score (0-100)"""
        
        # Weight different aspects
        weights = {
            'financial_health': 0.3,
            'market_position': 0.25,
            'operational_efficiency': 0.2,
            'growth_trajectory': 0.15,
            'competitive_standing': 0.1
        }
        
        score = 0.0
        
        # Financial health score
        balance = performance_data['financial_health']['balance']
        financial_score = min(100, max(0, (balance + 50000) / 1000))  # 0-100 scale
        score += financial_score * weights['financial_health']
        
        # Market position score
        percentile = performance_data['market_position']['percentile']
        score += percentile * weights['market_position']
        
        # Operational efficiency score
        efficiency = performance_data['operational_efficiency']['production_efficiency']
        score += efficiency * weights['operational_efficiency']
        
        # Growth trajectory score
        growth_rate = performance_data['growth_trajectory']['revenue_growth_rate']
        growth_score = min(100, max(0, (growth_rate + 10) * 5))  # Normalize -10% to +10% growth
        score += growth_score * weights['growth_trajectory']
        
        # Competitive standing score (inverse of competitive pressure)
        pressure = performance_data['competitive_standing']['competitive_pressure']
        competitive_score = (1 - pressure) * 100
        score += competitive_score * weights['competitive_standing']
        
        return min(100, max(0, score))
    
    def _categorize_performance(self, score: float) -> str:
        """Categorize overall performance score"""
        if score >= 80:
            return 'excellent'
        elif score >= 60:
            return 'good'
        elif score >= 40:
            return 'fair'
        elif score >= 20:
            return 'poor'
        else:
            return 'critical'
    
    def _categorize_market_position(self, percentile: float) -> str:
        """Categorize market position based on percentile"""
        if percentile >= 80:
            return 'market_leader'
        elif percentile >= 60:
            return 'strong_competitor'
        elif percentile >= 40:
            return 'middle_pack'
        elif percentile >= 20:
            return 'struggling'
        else:
            return 'lagging'
    
    def _categorize_efficiency(self, efficiency: float) -> str:
        """Categorize operational efficiency"""
        if efficiency >= 90:
            return 'highly_efficient'
        elif efficiency >= 75:
            return 'efficient'
        elif efficiency >= 60:
            return 'moderate'
        elif efficiency >= 40:
            return 'inefficient'
        else:
            return 'very_inefficient'
    
    def _categorize_growth(self, growth_rate: float) -> str:
        """Categorize growth trajectory"""
        if growth_rate >= 0.2:
            return 'rapid_growth'
        elif growth_rate >= 0.1:
            return 'strong_growth'
        elif growth_rate >= 0.05:
            return 'moderate_growth'
        elif growth_rate >= 0:
            return 'slow_growth'
        elif growth_rate >= -0.05:
            return 'stagnant'
        else:
            return 'declining'
    
    def _calculate_overall_risk(self, financial: str, market: str, operational: str) -> str:
        """Calculate overall risk level"""
        risk_scores = {'low': 1, 'medium': 2, 'high': 3}
        
        total_risk = (risk_scores[financial] + risk_scores[market] + risk_scores[operational]) / 3
        
        if total_risk >= 2.5:
            return 'high'
        elif total_risk >= 1.5:
            return 'medium'
        else:
            return 'low'
    
    def _calculate_group_metrics(self, players) -> Dict:
        """Calculate aggregate metrics for a group of players"""
        if not players.exists():
            return {}
        
        total_revenue = sum(float(p.total_revenue) for p in players)
        total_profit = sum(float(p.total_profit) for p in players)
        avg_balance = sum(float(p.balance) for p in players) / players.count()
        avg_market_share = sum(p.market_share for p in players) / players.count()
        
        return {
            'player_count': players.count(),
            'total_revenue': total_revenue,
            'avg_revenue': total_revenue / players.count(),
            'total_profit': total_profit,
            'avg_profit': total_profit / players.count(),
            'avg_balance': avg_balance,
            'avg_market_share': avg_market_share,
            'active_players': players.filter(is_active=True).count(),
            'bankrupt_players': players.filter(is_bankrupt=True).count()
        }
    
    def _calculate_balance_ratio(self, ai_metrics: Dict, human_metrics: Dict) -> float:
        """Calculate balance ratio between AI and human performance"""
        if not ai_metrics or not human_metrics:
            return 1.0
        
        ai_avg = ai_metrics.get('avg_revenue', 0)
        human_avg = human_metrics.get('avg_revenue', 0)
        
        if human_avg == 0:
            return 2.0 if ai_avg > 0 else 1.0
        
        return ai_avg / human_avg
    
    def _generate_balance_recommendations(self, ai_metrics: Dict, human_metrics: Dict) -> List[str]:
        """Generate recommendations for game balance"""
        recommendations = []
        
        balance_ratio = self._calculate_balance_ratio(ai_metrics, human_metrics)
        
        if balance_ratio > 1.3:  # AI significantly outperforming
            recommendations.append("Consider reducing AI difficulty or aggressiveness")
            recommendations.append("Implement dynamic difficulty adjustment")
            recommendations.append("Provide additional guidance to human players")
        elif balance_ratio < 0.7:  # AI significantly underperforming
            recommendations.append("Consider increasing AI difficulty or capabilities")
            recommendations.append("Review AI decision-making algorithms")
            recommendations.append("Add more sophisticated AI strategies")
        else:
            recommendations.append("Game balance appears healthy")
            recommendations.append("Continue monitoring for sustained balance")
        
        # Bankruptcy recommendations
        ai_bankruptcy_rate = (ai_metrics.get('bankrupt_players', 0) / 
                             max(1, ai_metrics.get('player_count', 1)))
        human_bankruptcy_rate = (human_metrics.get('bankrupt_players', 0) / 
                                max(1, human_metrics.get('player_count', 1)))
        
        if ai_bankruptcy_rate > 0.3:
            recommendations.append("High AI bankruptcy rate - review AI financial management")
        if human_bankruptcy_rate > 0.3:
            recommendations.append("High human bankruptcy rate - consider easier difficulty")
        
        return recommendations
    
    def _calculate_performance_spread(self, strategy_performance: Dict) -> float:
        """Calculate performance spread across strategies"""
        if not strategy_performance:
            return 0.0
        
        revenues = [data['avg_revenue'] for data in strategy_performance.values()]
        
        if len(revenues) < 2:
            return 0.0
        
        max_revenue = max(revenues)
        min_revenue = min(revenues)
        
        if max_revenue == 0:
            return 0.0
        
        return (max_revenue - min_revenue) / max_revenue


class AIBehaviorLogger:
    """Logs and tracks AI behavior for analysis and debugging"""
    
    def __init__(self, multiplayer_game: MultiplayerGame):
        self.game = multiplayer_game
    
    def log_decision(self, ai_player: PlayerSession, decision_type: str, 
                    decision_data: Dict, context: Dict = None) -> None:
        """Log an AI decision with context"""
        
        GameEvent.objects.create(
            multiplayer_game=self.game,
            event_type='ai_action',
            message=f"{ai_player.company_name} made {decision_type} decision",
            data={
                'player_id': str(ai_player.id),
                'decision_type': decision_type,
                'decision_data': decision_data,
                'context': context or {},
                'timestamp': timezone.now().isoformat(),
                'ai_strategy': ai_player.ai_strategy,
                'ai_difficulty': ai_player.ai_difficulty
            },
            visible_to_all=False  # Internal logging
        )
    
    def log_performance_change(self, ai_player: PlayerSession, 
                             old_metrics: Dict, new_metrics: Dict) -> None:
        """Log significant performance changes"""
        
        # Calculate significant changes
        changes = {}
        for key in ['balance', 'total_revenue', 'market_share']:
            old_val = old_metrics.get(key, 0)
            new_val = new_metrics.get(key, 0)
            
            if old_val != 0:
                change_pct = ((new_val - old_val) / old_val) * 100
                if abs(change_pct) > 10:  # Significant change threshold
                    changes[key] = {
                        'old': old_val,
                        'new': new_val,
                        'change_pct': change_pct
                    }
        
        if changes:
            GameEvent.objects.create(
                multiplayer_game=self.game,
                event_type='ai_action',
                message=f"{ai_player.company_name} performance changed significantly",
                data={
                    'player_id': str(ai_player.id),
                    'changes': changes,
                    'timestamp': timezone.now().isoformat()
                },
                visible_to_all=False
            )
    
    def log_strategy_adaptation(self, ai_player: PlayerSession, 
                              adaptation_reason: str, changes: Dict) -> None:
        """Log AI strategy adaptations"""
        
        GameEvent.objects.create(
            multiplayer_game=self.game,
            event_type='ai_action',
            message=f"{ai_player.company_name} adapted strategy: {adaptation_reason}",
            data={
                'player_id': str(ai_player.id),
                'adaptation_reason': adaptation_reason,
                'changes': changes,
                'timestamp': timezone.now().isoformat()
            },
            visible_to_all=False
        )
    
    def get_behavior_summary(self, ai_player: PlayerSession, 
                           days_back: int = 30) -> Dict:
        """Get behavior summary for AI player"""
        
        cutoff_date = timezone.now() - timedelta(days=days_back)
        
        ai_events = GameEvent.objects.filter(
            multiplayer_game=self.game,
            event_type='ai_action',
            timestamp__gte=cutoff_date,
            data__player_id=str(ai_player.id)
        )
        
        # Analyze decision patterns
        decision_types = {}
        adaptations = 0
        performance_changes = 0
        
        for event in ai_events:
            event_data = event.data
            
            if 'decision_type' in event_data:
                decision_type = event_data['decision_type']
                decision_types[decision_type] = decision_types.get(decision_type, 0) + 1
            
            if 'adaptation_reason' in event_data:
                adaptations += 1
            
            if 'changes' in event_data:
                performance_changes += 1
        
        return {
            'total_decisions': ai_events.count(),
            'decision_breakdown': decision_types,
            'adaptations': adaptations,
            'performance_changes': performance_changes,
            'most_common_decision': max(decision_types.items(), key=lambda x: x[1])[0] if decision_types else None,
            'adaptation_rate': adaptations / max(1, ai_events.count()),
            'activity_level': 'high' if ai_events.count() > 20 else 'medium' if ai_events.count() > 10 else 'low'
        }


class AIConfigurationValidator:
    """Validates AI configuration and settings"""
    
    @staticmethod
    def validate_multiplayer_game_config(game: MultiplayerGame) -> Dict:
        """Validate multiplayer game configuration for AI compatibility"""
        
        issues = []
        warnings = []
        
        # Check AI player count
        if game.ai_players_count == 0:
            warnings.append("No AI players configured")
        elif game.ai_players_count > 8:
            warnings.append("High AI player count may impact performance")
        
        # Check difficulty setting
        if game.difficulty not in ['easy', 'medium', 'hard', 'expert']:
            issues.append(f"Invalid difficulty setting: {game.difficulty}")
        
        # Check game timing
        if game.turn_deadline_hours < 1:
            warnings.append("Very short turn deadline may not allow proper AI processing")
        elif game.turn_deadline_hours > 168:  # 1 week
            warnings.append("Very long turn deadline may reduce engagement")
        
        # Check starting balance
        if game.starting_balance < 10000:
            warnings.append("Low starting balance may cause immediate AI bankruptcies")
        elif game.starting_balance > 200000:
            warnings.append("High starting balance may reduce challenge")
        
        return {
            'is_valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'recommendation': 'Fix issues before starting game' if issues else 'Configuration acceptable'
        }
    
    @staticmethod
    def validate_ai_player_config(ai_player: PlayerSession) -> Dict:
        """Validate AI player configuration"""
        
        issues = []
        warnings = []
        
        # Check required fields
        if not ai_player.company_name:
            issues.append("Company name is required")
        
        if not ai_player.ai_strategy:
            issues.append("AI strategy is required")
        
        # Check AI parameters
        if not (0.1 <= ai_player.ai_difficulty <= 2.0):
            issues.append(f"AI difficulty {ai_player.ai_difficulty} outside valid range (0.1-2.0)")
        
        if not (0.0 <= ai_player.ai_aggressiveness <= 1.0):
            issues.append(f"AI aggressiveness {ai_player.ai_aggressiveness} outside valid range (0.0-1.0)")
        
        if not (0.0 <= ai_player.ai_risk_tolerance <= 1.0):
            issues.append(f"AI risk tolerance {ai_player.ai_risk_tolerance} outside valid range (0.0-1.0)")
        
        # Check strategy validity
        valid_strategies = ['aggressive', 'conservative', 'innovative', 'balanced', 
                          'cheap_only', 'premium_focus', 'e_bike_specialist']
        if ai_player.ai_strategy not in valid_strategies:
            issues.append(f"Invalid AI strategy: {ai_player.ai_strategy}")
        
        # Check balance constraints
        if ai_player.balance < -100000:
            warnings.append("Very negative balance may cause immediate bankruptcy")
        
        return {
            'is_valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'recommendation': 'Fix issues before game start' if issues else 'AI player configuration valid'
        }
    
    @staticmethod
    def get_recommended_ai_mix(human_player_count: int, total_ai_count: int) -> List[Dict]:
        """Get recommended AI player mix for balanced gameplay"""
        
        if total_ai_count == 0:
            return []
        
        # Define strategy templates
        strategy_templates = {
            'aggressive': {'aggressiveness': 0.9, 'risk_tolerance': 0.8, 'difficulty_modifier': 1.1},
            'conservative': {'aggressiveness': 0.3, 'risk_tolerance': 0.3, 'difficulty_modifier': 0.9},
            'innovative': {'aggressiveness': 0.7, 'risk_tolerance': 0.8, 'difficulty_modifier': 1.0},
            'balanced': {'aggressiveness': 0.5, 'risk_tolerance': 0.5, 'difficulty_modifier': 1.0}
        }
        
        recommendations = []
        
        # Distribute strategies for balanced gameplay
        strategies = list(strategy_templates.keys())
        
        for i in range(total_ai_count):
            strategy = strategies[i % len(strategies)]
            template = strategy_templates[strategy]
            
            # Vary difficulty slightly
            base_difficulty = 0.8 + (human_player_count * 0.1)  # Scale with human count
            difficulty = base_difficulty * template['difficulty_modifier']
            difficulty += random.uniform(-0.1, 0.1)  # Small random variation
            difficulty = max(0.3, min(1.5, difficulty))  # Clamp to valid range
            
            recommendations.append({
                'company_name': f'{strategy.title()} AI Corp {i+1}',
                'ai_strategy': strategy,
                'ai_difficulty': round(difficulty, 2),
                'ai_aggressiveness': template['aggressiveness'],
                'ai_risk_tolerance': template['risk_tolerance']
            })
        
        return recommendations