from decimal import Decimal
from django.utils import timezone
from django.db.models import Sum, Avg, Q
from datetime import timedelta
import logging

from .models import PlayerSession, MultiplayerGame, GameEvent, TurnState
from finance.models import MonthlyReport, Transaction
from production.models import ProducedBike
from sales.models import SalesOrder

logger = logging.getLogger(__name__)


class BankruptcyManager:
    """Manages bankruptcy detection, procedures, and elimination mechanics for multiplayer games."""
    
    # Bankruptcy thresholds and criteria
    SEVERE_DEBT_RATIO = 0.8  # 80% debt to assets ratio
    CONSECUTIVE_LOSS_MONTHS = 6  # 6 months of consecutive losses
    MINIMUM_PRODUCTION_CAPACITY = 0.1  # 10% of average competitor production
    CASH_FLOW_CRITICAL_MONTHS = 3  # 3 months of negative cash flow
    
    def __init__(self, multiplayer_game):
        self.game = multiplayer_game
        
    def check_all_players_bankruptcy(self):
        """Check bankruptcy conditions for all active players in the game."""
        active_players = self.game.players.filter(is_active=True, is_bankrupt=False)
        bankruptcy_results = []
        
        for player in active_players:
            bankruptcy_status = self.evaluate_player_bankruptcy(player)
            if bankruptcy_status['is_bankrupt']:
                bankruptcy_results.append({
                    'player': player,
                    'status': bankruptcy_status,
                    'triggered': self.trigger_bankruptcy_procedure(player, bankruptcy_status)
                })
        
        return bankruptcy_results
    
    def evaluate_player_bankruptcy(self, player):
        """Comprehensive evaluation of player's bankruptcy risk and status."""
        current_balance = player.balance
        game_threshold = self.game.bankruptcy_threshold
        
        # Get recent financial data
        recent_reports = self._get_recent_monthly_reports(player, 6)
        recent_transactions = self._get_recent_transactions(player, 90)  # Last 90 days
        
        # Multiple bankruptcy criteria
        criteria = {
            'balance_threshold': current_balance <= game_threshold,
            'severe_debt': self._check_debt_ratio(player, recent_reports),
            'consecutive_losses': self._check_consecutive_losses(recent_reports),
            'no_production_capacity': self._check_production_capacity(player),
            'negative_cash_flow': self._check_cash_flow_pattern(recent_reports),
            'asset_liquidation': self._check_asset_liquidation(player),
            'market_exclusion': self._check_market_exclusion(player)
        }
        
        # Calculate bankruptcy score (weighted criteria)
        bankruptcy_score = self._calculate_bankruptcy_score(criteria)
        
        # Risk levels
        risk_level = self._determine_risk_level(bankruptcy_score, criteria)
        
        # Determine if bankruptcy should be triggered
        is_bankrupt = (
            criteria['balance_threshold'] or 
            bankruptcy_score >= 75 or 
            (criteria['consecutive_losses'] and criteria['negative_cash_flow'])
        )
        
        return {
            'is_bankrupt': is_bankrupt,
            'bankruptcy_score': bankruptcy_score,
            'risk_level': risk_level,
            'criteria': criteria,
            'balance': current_balance,
            'threshold': game_threshold,
            'recommendations': self._generate_recovery_recommendations(criteria, player) if not is_bankrupt else None
        }
    
    def trigger_bankruptcy_procedure(self, player, bankruptcy_status):
        """Execute bankruptcy procedure for a player."""
        try:
            # Mark player as bankrupt
            player.is_bankrupt = True
            player.bankruptcy_month = self.game.current_month
            player.bankruptcy_year = self.game.current_year
            player.is_active = False
            player.save()
            
            # Record bankruptcy event
            event = GameEvent.objects.create(
                multiplayer_game=self.game,
                event_type='player_bankruptcy',
                message=f"{player.company_name} has filed for bankruptcy",
                data={
                    'player_id': str(player.id),
                    'company_name': player.company_name,
                    'bankruptcy_score': bankruptcy_status['bankruptcy_score'],
                    'final_balance': float(player.balance),
                    'criteria_met': bankruptcy_status['criteria'],
                    'month': self.game.current_month,
                    'year': self.game.current_year
                }
            )
            
            # Handle bankruptcy consequences
            self._handle_bankruptcy_consequences(player)
            
            # Check if game should end
            self._check_game_end_conditions()
            
            logger.info(f"Player {player.company_name} bankruptcy processed successfully")
            
            return {
                'success': True,
                'event_id': event.id,
                'consequences': self._get_bankruptcy_consequences(player)
            }
            
        except Exception as e:
            logger.error(f"Error processing bankruptcy for {player.company_name}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _handle_bankruptcy_consequences(self, player):
        """Handle various consequences of player bankruptcy."""
        consequences = []
        
        # 1. Asset liquidation
        liquidation_value = self._liquidate_player_assets(player)
        consequences.append(f"Assets liquidated for {liquidation_value}")
        
        # 2. Market share redistribution
        redistributed_share = self._redistribute_market_share(player)
        consequences.append(f"Market share {redistributed_share}% redistributed")
        
        # 3. Supplier impact
        supplier_impact = self._handle_supplier_relationships(player)
        consequences.extend(supplier_impact)
        
        # 4. Employee impact
        employee_impact = self._handle_employee_consequences(player)
        consequences.extend(employee_impact)
        
        # 5. Competitive effects
        competitive_effects = self._apply_competitive_effects(player)
        consequences.extend(competitive_effects)
        
        # Record consequences in game event
        GameEvent.objects.create(
            multiplayer_game=self.game,
            event_type='system_message',
            message=f"Bankruptcy consequences for {player.company_name}",
            data={
                'player_id': str(player.id),
                'consequences': consequences,
                'liquidation_value': float(liquidation_value)
            }
        )
        
        return consequences
    
    def _liquidate_player_assets(self, player):
        """Calculate and apply asset liquidation value."""
        # Get player's inventory value
        from warehouse.models import ComponentStock
        from production.models import ProducedBike
        
        total_value = Decimal('0.00')
        
        # Liquidate finished bikes (at 60% of cost)
        bikes = ProducedBike.objects.filter(
            session_id=player.id,  # Assuming this maps to player session
            sold=False
        )
        for bike in bikes:
            liquidation_value = bike.total_cost * Decimal('0.6')
            total_value += liquidation_value
        
        # Liquidate component inventory (at 40% of cost)
        components = ComponentStock.objects.filter(
            session_id=player.id,
            quantity__gt=0
        )
        for component in components:
            liquidation_value = (component.component.cost * component.quantity) * Decimal('0.4')
            total_value += liquidation_value
        
        # Add liquidation value to player balance (partial debt recovery)
        player.balance += total_value
        player.save()
        
        return total_value
    
    def _redistribute_market_share(self, player):
        """Redistribute bankrupt player's market share among remaining players."""
        active_players = self.game.players.filter(is_active=True, is_bankrupt=False).exclude(id=player.id)
        
        if not active_players:
            return 0
        
        # Calculate player's market share
        player_market_share = player.market_share
        
        # Redistribute proportionally among remaining players
        redistribution_per_player = player_market_share / len(active_players)
        
        for active_player in active_players:
            active_player.market_share += redistribution_per_player
            active_player.save()
        
        # Reset bankrupt player's market share
        player.market_share = 0
        player.save()
        
        return player_market_share
    
    def _handle_supplier_relationships(self, player):
        """Handle supplier relationship consequences of bankruptcy."""
        consequences = []
        
        # In a real implementation, this would:
        # - Cancel pending orders
        # - Apply supplier penalties to other players
        # - Affect supplier reliability scores
        # - Impact component availability
        
        consequences.append("Pending supplier orders cancelled")
        consequences.append("Supplier trust ratings affected industry-wide")
        
        return consequences
    
    def _handle_employee_consequences(self, player):
        """Handle employee-related consequences of bankruptcy."""
        consequences = []
        
        # In a real implementation, this would:
        # - Release employees to market (affecting hiring costs for others)
        # - Apply morale penalties to industry
        # - Affect local market conditions
        
        consequences.append("Employees released to job market")
        consequences.append("Industry morale impact applied")
        
        return consequences
    
    def _apply_competitive_effects(self, player):
        """Apply competitive market effects of player elimination."""
        effects = []
        
        # Reduce overall market competition
        # Increase pricing power for remaining players
        # Affect market dynamics
        
        effects.append("Market competition intensity reduced")
        effects.append("Remaining players gain pricing power")
        
        return effects
    
    def _check_game_end_conditions(self):
        """Check if game should end due to too few players."""
        active_players = self.game.players.filter(is_active=True, is_bankrupt=False)
        
        if active_players.count() <= 1:
            self.game.status = 'completed'
            self.game.ended_at = timezone.now()
            self.game.save()
            
            winner = active_players.first() if active_players.exists() else None
            
            GameEvent.objects.create(
                multiplayer_game=self.game,
                event_type='game_ended',
                message=f"Game ended - Winner: {winner.company_name if winner else 'No survivors'}",
                data={
                    'winner_id': str(winner.id) if winner else None,
                    'winner_company': winner.company_name if winner else None,
                    'reason': 'bankruptcy_elimination'
                }
            )
    
    def _get_recent_monthly_reports(self, player, months=6):
        """Get recent monthly reports for analysis."""
        # This would need to be adapted based on how monthly reports are linked to players
        # For now, return empty list - implementation depends on your MonthlyReport model structure
        return []
    
    def _get_recent_transactions(self, player, days=90):
        """Get recent transactions for cash flow analysis."""
        cutoff_date = timezone.now() - timedelta(days=days)
        # This would need to be adapted based on how transactions are linked to players
        return []
    
    def _check_debt_ratio(self, player, reports):
        """Check if player has excessive debt ratio."""
        # Simplified calculation - would need access to debt/asset data
        return player.balance < Decimal('-20000.00')
    
    def _check_consecutive_losses(self, reports):
        """Check for consecutive months of losses."""
        if len(reports) < self.CONSECUTIVE_LOSS_MONTHS:
            return False
        
        recent_reports = reports[:self.CONSECUTIVE_LOSS_MONTHS]
        return all(report.profit < 0 for report in recent_reports)
    
    def _check_production_capacity(self, player):
        """Check if player has lost production capacity."""
        # Get recent production data
        recent_production = ProducedBike.objects.filter(
            session_id=player.id,
            production_month__gte=self.game.current_month - 3,
            production_year=self.game.current_year
        ).count()
        
        # Compare with average competitor production
        active_competitors = self.game.players.filter(
            is_active=True, 
            is_bankrupt=False
        ).exclude(id=player.id)
        
        if not active_competitors:
            return False
        
        # Simplified check - in reality would calculate average production
        return recent_production == 0
    
    def _check_cash_flow_pattern(self, reports):
        """Check for sustained negative cash flow."""
        if len(reports) < self.CASH_FLOW_CRITICAL_MONTHS:
            return False
        
        recent_reports = reports[:self.CASH_FLOW_CRITICAL_MONTHS]
        return all(report.cash_flow < 0 for report in recent_reports if hasattr(report, 'cash_flow'))
    
    def _check_asset_liquidation(self, player):
        """Check if player is desperately liquidating assets."""
        # Would check for unusual asset sale patterns
        return False
    
    def _check_market_exclusion(self, player):
        """Check if player is being excluded from markets."""
        # Would check if player can no longer compete effectively in any market
        return False
    
    def _calculate_bankruptcy_score(self, criteria):
        """Calculate weighted bankruptcy score from criteria."""
        weights = {
            'balance_threshold': 30,
            'severe_debt': 20,
            'consecutive_losses': 15,
            'no_production_capacity': 15,
            'negative_cash_flow': 10,
            'asset_liquidation': 5,
            'market_exclusion': 5
        }
        
        score = sum(weights[criterion] for criterion, met in criteria.items() if met)
        return min(100, score)
    
    def _determine_risk_level(self, score, criteria):
        """Determine risk level based on bankruptcy score."""
        if score >= 75:
            return 'critical'
        elif score >= 50:
            return 'high'
        elif score >= 25:
            return 'medium'
        else:
            return 'low'
    
    def _generate_recovery_recommendations(self, criteria, player):
        """Generate recommendations for avoiding bankruptcy."""
        recommendations = []
        
        if criteria['balance_threshold']:
            recommendations.append("Secure emergency financing or consider asset liquidation")
        
        if criteria['consecutive_losses']:
            recommendations.append("Review pricing strategy and cost structure")
        
        if criteria['no_production_capacity']:
            recommendations.append("Invest in production capabilities or consider partnerships")
        
        if criteria['negative_cash_flow']:
            recommendations.append("Improve cash flow management and collection processes")
        
        if criteria['severe_debt']:
            recommendations.append("Restructure debt and reduce leverage")
        
        return recommendations
    
    def _get_bankruptcy_consequences(self, player):
        """Get summary of bankruptcy consequences."""
        return {
            'player_eliminated': True,
            'assets_liquidated': True,
            'market_share_redistributed': True,
            'competitive_effects': True,
            'industry_impact': True
        }


class BankruptcyPreventionSystem:
    """System to help players avoid bankruptcy through warnings and assistance."""
    
    def __init__(self, multiplayer_game):
        self.game = multiplayer_game
        self.bankruptcy_manager = BankruptcyManager(multiplayer_game)
    
    def monitor_player_financial_health(self, player):
        """Monitor and provide warnings about player financial health."""
        bankruptcy_status = self.bankruptcy_manager.evaluate_player_bankruptcy(player)
        
        # Generate warnings based on risk level
        if bankruptcy_status['risk_level'] in ['high', 'critical']:
            self._send_bankruptcy_warning(player, bankruptcy_status)
        
        return bankruptcy_status
    
    def _send_bankruptcy_warning(self, player, status):
        """Send bankruptcy warning to player."""
        risk_level = status['risk_level']
        recommendations = status.get('recommendations', [])
        
        warning_message = f"⚠️ FINANCIAL WARNING: {player.company_name} is at {risk_level} bankruptcy risk"
        
        GameEvent.objects.create(
            multiplayer_game=self.game,
            event_type='system_notification',
            message=warning_message,
            data={
                'player_id': str(player.id),
                'risk_level': risk_level,
                'bankruptcy_score': status['bankruptcy_score'],
                'recommendations': recommendations,
                'criteria_met': status['criteria']
            },
            visible_to_all=False
        )
        
        # Make visible only to the specific player
        event = GameEvent.objects.filter(multiplayer_game=self.game).latest('timestamp')
        event.visible_to.add(player)
    
    def get_financial_health_dashboard(self, player):
        """Get comprehensive financial health dashboard for player."""
        status = self.bankruptcy_manager.evaluate_player_bankruptcy(player)
        
        # Calculate additional metrics
        industry_rank = self._calculate_industry_rank(player)
        trend_analysis = self._analyze_financial_trends(player)
        competitive_position = self._analyze_competitive_position(player)
        
        return {
            'bankruptcy_risk': status,
            'industry_rank': industry_rank,
            'trends': trend_analysis,
            'competitive_position': competitive_position,
            'improvement_actions': self._suggest_improvement_actions(player, status)
        }
    
    def _calculate_industry_rank(self, player):
        """Calculate player's rank among all players."""
        active_players = self.game.players.filter(is_active=True, is_bankrupt=False)
        player_balance = player.balance
        
        better_players = active_players.filter(balance__gt=player_balance).count()
        total_players = active_players.count()
        
        rank = better_players + 1
        percentile = ((total_players - rank + 1) / total_players) * 100 if total_players > 0 else 0
        
        return {
            'rank': rank,
            'total_players': total_players,
            'percentile': round(percentile, 1)
        }
    
    def _analyze_financial_trends(self, player):
        """Analyze financial trends for the player."""
        # Simplified trend analysis - would use actual historical data
        return {
            'revenue_trend': 'stable',
            'profit_trend': 'declining',
            'balance_trend': 'declining',
            'momentum': 'negative'
        }
    
    def _analyze_competitive_position(self, player):
        """Analyze player's competitive position."""
        return {
            'market_share': player.market_share,
            'market_position': 'follower',
            'competitive_strength': 'moderate',
            'differentiation': 'low'
        }
    
    def _suggest_improvement_actions(self, player, status):
        """Suggest specific improvement actions based on analysis."""
        actions = []
        
        if status['risk_level'] in ['high', 'critical']:
            actions.extend(status.get('recommendations', []))
        
        # Add general improvement suggestions
        actions.extend([
            "Consider expanding into profitable market segments",
            "Optimize production efficiency and reduce costs",
            "Improve product quality and customer satisfaction",
            "Develop strategic partnerships with suppliers"
        ])
        
        return actions[:5]  # Return top 5 suggestions