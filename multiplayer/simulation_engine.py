from decimal import Decimal
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
import logging

from .models import MultiplayerGame, PlayerSession, TurnState, GameEvent
from .ai_manager import MultiplayerAIManager
from .bankruptcy_manager import BankruptcyManager, BankruptcyPreventionSystem
from simulation.engine import SimulationEngine
from bikeshop.models import GameSession
from competitors.models import AICompetitor
import json

logger = logging.getLogger(__name__)


class MultiplayerSimulationEngine:
    """Enhanced simulation engine for multiplayer games with AI competitors and bankruptcy management."""
    
    def __init__(self, multiplayer_game):
        self.game = multiplayer_game
        self.ai_manager = MultiplayerAIManager(multiplayer_game)
        self.bankruptcy_manager = BankruptcyManager(multiplayer_game)
        self.bankruptcy_prevention = BankruptcyPreventionSystem(multiplayer_game)
        
    def process_multiplayer_turn(self):
        """Process a complete multiplayer turn including all player decisions and AI actions."""
        logger.info(f"Processing turn {self.game.current_year}/{self.game.current_month:02d} for game {self.game.name}")
        
        try:
            with transaction.atomic():
                # 1. Check turn submission status
                turn_status = self._check_turn_submission_status()
                
                # 2. Auto-submit for timed-out players and AI players
                self._handle_auto_submissions()
                
                # 3. Process AI decisions
                self._process_ai_decisions()
                
                # 4. Execute all player decisions simultaneously
                self._execute_all_player_decisions()
                
                # 5. Process market competition and dynamics
                self._process_market_competition()
                
                # 6. Check bankruptcy conditions
                bankruptcy_results = self._check_bankruptcy_conditions()
                
                # 7. Update game state and advance turn
                self._advance_game_turn()
                
                # 8. Generate turn summary and events
                self._generate_turn_summary(bankruptcy_results)
                
                # 9. Check game end conditions
                self._check_game_end_conditions()
                
                logger.info(f"Turn processing completed successfully for game {self.game.name}")
                
                return {
                    'success': True,
                    'turn': f"{self.game.current_year}/{self.game.current_month:02d}",
                    'bankruptcy_events': len(bankruptcy_results),
                    'active_players': self.game.active_players_count
                }
                
        except Exception as e:
            logger.error(f"Error processing multiplayer turn for game {self.game.name}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _check_turn_submission_status(self):
        """Check which players have submitted their decisions for the current turn."""
        current_month = self.game.current_month
        current_year = self.game.current_year
        
        active_players = self.game.players.filter(is_active=True, is_bankrupt=False)
        
        status = {}
        for player in active_players:
            turn_state, created = TurnState.objects.get_or_create(
                multiplayer_game=self.game,
                player_session=player,
                month=current_month,
                year=current_year,
                defaults={'decisions_submitted': False}
            )
            
            status[player.id] = {
                'player': player,
                'submitted': turn_state.decisions_submitted,
                'turn_state': turn_state,
                'is_ai': player.is_ai
            }
        
        return status
    
    def _handle_auto_submissions(self):
        """Handle auto-submission for timed-out players and AI players."""
        deadline = timezone.now() - timedelta(hours=self.game.turn_deadline_hours)
        
        turn_states = TurnState.objects.filter(
            multiplayer_game=self.game,
            month=self.game.current_month,
            year=self.game.current_year,
            decisions_submitted=False
        )
        
        for turn_state in turn_states:
            player = turn_state.player_session
            
            # Auto-submit for AI players
            if player.is_ai:
                self._auto_submit_ai_decisions(turn_state)
            
            # Auto-submit for timed-out human players
            elif turn_state.created_at < deadline:
                self._auto_submit_timeout_decisions(turn_state)
    
    def _auto_submit_ai_decisions(self, turn_state):
        """Auto-submit decisions for AI players."""
        player = turn_state.player_session
        
        try:
            # Get AI decisions from AI manager
            ai_decisions = self.ai_manager.make_ai_decisions(player)
            
            # Store decisions in turn state
            turn_state.production_decisions = ai_decisions.get('production', {})
            turn_state.procurement_decisions = ai_decisions.get('procurement', {})
            turn_state.sales_decisions = ai_decisions.get('sales', {})
            turn_state.hr_decisions = ai_decisions.get('hr', {})
            turn_state.finance_decisions = ai_decisions.get('finance', {})
            
            turn_state.decisions_submitted = True
            turn_state.auto_submitted = True
            turn_state.submitted_at = timezone.now()
            turn_state.save()
            
            logger.info(f"AI decisions auto-submitted for {player.company_name}")
            
        except Exception as e:
            logger.error(f"Error auto-submitting AI decisions for {player.company_name}: {str(e)}")
    
    def _auto_submit_timeout_decisions(self, turn_state):
        """Auto-submit default decisions for timed-out human players."""
        player = turn_state.player_session
        
        # Generate conservative default decisions
        default_decisions = self._generate_default_decisions(player)
        
        turn_state.production_decisions = default_decisions.get('production', {})
        turn_state.procurement_decisions = default_decisions.get('procurement', {})
        turn_state.sales_decisions = default_decisions.get('sales', {})
        turn_state.hr_decisions = default_decisions.get('hr', {})
        turn_state.finance_decisions = default_decisions.get('finance', {})
        
        turn_state.decisions_submitted = True
        turn_state.auto_submitted = True
        turn_state.submitted_at = timezone.now()
        turn_state.save()
        
        # Create notification event
        GameEvent.objects.create(
            multiplayer_game=self.game,
            event_type='system_message',
            message=f"{player.company_name} missed turn deadline - default decisions applied",
            data={'player_id': str(player.id), 'auto_submitted': True}
        )
        
        logger.warning(f"Timeout auto-submission for {player.company_name}")
    
    def _process_ai_decisions(self):
        """Process AI-specific decision logic and strategic adjustments."""
        ai_players = self.game.players.filter(player_type='ai', is_active=True, is_bankrupt=False)
        
        for ai_player in ai_players:
            try:
                # Update AI competitive analysis
                self.ai_manager.update_competitive_analysis(ai_player)
                
                # Adjust AI strategy based on market conditions
                self.ai_manager.adapt_ai_strategy(ai_player)
                
                # Log AI actions for transparency
                self._log_ai_actions(ai_player)
                
            except Exception as e:
                logger.error(f"Error processing AI decisions for {ai_player.company_name}: {str(e)}")
    
    def _execute_all_player_decisions(self):
        """Execute decisions for all players simultaneously to maintain fairness."""
        submitted_turns = TurnState.objects.filter(
            multiplayer_game=self.game,
            month=self.game.current_month,
            year=self.game.current_year,
            decisions_submitted=True
        )
        
        execution_results = {}
        
        for turn_state in submitted_turns:
            player = turn_state.player_session
            
            try:
                # Create or update game session for this player
                game_session = self._get_or_create_game_session(player)
                
                # Execute decisions using existing simulation engine
                result = self._execute_player_decisions(game_session, turn_state)
                
                # Update player performance metrics
                self._update_player_metrics(player, result)
                
                execution_results[player.id] = result
                
                logger.info(f"Decisions executed for {player.company_name}")
                
            except Exception as e:
                logger.error(f"Error executing decisions for {player.company_name}: {str(e)}")
                execution_results[player.id] = {'error': str(e)}
        
        return execution_results
    
    def _process_market_competition(self):
        """Process market competition dynamics between all players."""
        try:
            active_players = self.game.players.filter(is_active=True, is_bankrupt=False)
            
            # Process competitive sales for each market
            from simulation.competitive_sales_engine import CompetitiveSalesEngine
            
            for player in active_players:
                game_session = self._get_or_create_game_session(player)
                
                # Create competitive sales engine with multiplayer context
                competitive_engine = CompetitiveSalesEngine(game_session)
                
                # Process competitive sales considering all players
                competitive_engine.process_competitive_sales()
                
                # Update market share calculations
                self._update_market_shares()
            
            logger.info("Market competition processing completed")
            
        except Exception as e:
            logger.error(f"Error processing market competition: {str(e)}")
    
    def _check_bankruptcy_conditions(self):
        """Check bankruptcy conditions for all players."""
        try:
            bankruptcy_results = self.bankruptcy_manager.check_all_players_bankruptcy()
            
            # Send preventive warnings to at-risk players
            active_players = self.game.players.filter(is_active=True, is_bankrupt=False)
            for player in active_players:
                self.bankruptcy_prevention.monitor_player_financial_health(player)
            
            return bankruptcy_results
            
        except Exception as e:
            logger.error(f"Error checking bankruptcy conditions: {str(e)}")
            return []
    
    def _advance_game_turn(self):
        """Advance the game to the next turn."""
        # Advance month
        if self.game.current_month == 12:
            self.game.current_month = 1
            self.game.current_year += 1
        else:
            self.game.current_month += 1
        
        self.game.save()
        
        # Create turn advancement event
        GameEvent.objects.create(
            multiplayer_game=self.game,
            event_type='turn_processed',
            message=f"Turn advanced to {self.game.current_year}/{self.game.current_month:02d}",
            data={
                'month': self.game.current_month,
                'year': self.game.current_year,
                'active_players': self.game.active_players_count
            }
        )
    
    def _generate_turn_summary(self, bankruptcy_results):
        """Generate comprehensive turn summary and events."""
        active_players = self.game.players.filter(is_active=True, is_bankrupt=False)
        
        # Calculate turn statistics
        total_revenue = sum(player.total_revenue for player in active_players)
        total_bikes_produced = sum(player.bikes_produced for player in active_players)
        total_bikes_sold = sum(player.bikes_sold for player in active_players)
        
        # Create turn summary event
        summary_data = {
            'month': self.game.current_month - 1 if self.game.current_month > 1 else 12,
            'year': self.game.current_year if self.game.current_month > 1 else self.game.current_year - 1,
            'active_players': len(active_players),
            'bankruptcies': len(bankruptcy_results),
            'total_revenue': float(total_revenue),
            'total_bikes_produced': total_bikes_produced,
            'total_bikes_sold': total_bikes_sold,
            'market_leaders': self._get_market_leaders()
        }
        
        GameEvent.objects.create(
            multiplayer_game=self.game,
            event_type='turn_processed',
            message=f"Turn summary: {len(active_players)} active players, {len(bankruptcy_results)} bankruptcies",
            data=summary_data
        )
    
    def _check_game_end_conditions(self):
        """Check if the game should end."""
        active_players = self.game.active_players_count
        
        # End game if only one player remains
        if active_players <= 1:
            self._end_game('last_player_standing')
        
        # End game if maximum turns reached
        elif self._has_reached_max_turns():
            self._end_game('max_turns_reached')
    
    def _end_game(self, reason):
        """End the multiplayer game."""
        self.game.status = 'completed'
        self.game.ended_at = timezone.now()
        self.game.save()
        
        # Determine winner(s)
        winners = self._determine_winners()
        
        GameEvent.objects.create(
            multiplayer_game=self.game,
            event_type='game_ended',
            message=f"Game ended: {reason}",
            data={
                'reason': reason,
                'winners': [{'id': str(w.id), 'company': w.company_name} for w in winners],
                'final_standings': self._get_final_standings()
            }
        )
        
        logger.info(f"Game {self.game.name} ended: {reason}")
    
    def _get_or_create_game_session(self, player):
        """Get or create a GameSession for the player to work with existing simulation engine."""
        try:
            # Try to get existing session
            game_session = GameSession.objects.get(
                user=player.user,
                # Add any other criteria to match the player's session
            )
        except GameSession.DoesNotExist:
            # Create new session for this player
            game_session = GameSession.objects.create(
                user=player.user,
                current_month=self.game.current_month,
                current_year=self.game.current_year,
                balance=player.balance,
                is_active=True
            )
        
        # Sync session state with player state
        game_session.current_month = self.game.current_month
        game_session.current_year = self.game.current_year
        game_session.balance = player.balance
        game_session.save()
        
        return game_session
    
    def _execute_player_decisions(self, game_session, turn_state):
        """Execute individual player decisions using existing simulation engine."""
        # Create traditional simulation engine
        sim_engine = SimulationEngine(game_session)
        
        # Process the month using existing engine
        result = sim_engine.process_month()
        
        # Update turn state with results
        turn_state.revenue_this_turn = getattr(result, 'revenue', 0)
        turn_state.profit_this_turn = getattr(result, 'profit', 0)
        turn_state.bikes_produced_this_turn = getattr(result, 'bikes_produced', 0)
        turn_state.bikes_sold_this_turn = getattr(result, 'bikes_sold', 0)
        turn_state.save()
        
        return result
    
    def _update_player_metrics(self, player, execution_result):
        """Update player performance metrics based on execution results."""
        # Sync balance from game session
        game_session = self._get_or_create_game_session(player)
        player.balance = game_session.balance
        
        # Update cumulative metrics
        turn_revenue = getattr(execution_result, 'revenue', 0)
        turn_profit = getattr(execution_result, 'profit', 0)
        turn_bikes_produced = getattr(execution_result, 'bikes_produced', 0)
        turn_bikes_sold = getattr(execution_result, 'bikes_sold', 0)
        
        player.total_revenue += Decimal(str(turn_revenue))
        player.total_profit += Decimal(str(turn_profit))
        player.bikes_produced += turn_bikes_produced
        player.bikes_sold += turn_bikes_sold
        
        player.save()
    
    def _update_market_shares(self):
        """Update market share calculations for all players."""
        active_players = self.game.players.filter(is_active=True, is_bankrupt=False)
        total_revenue = sum(player.total_revenue for player in active_players)
        
        if total_revenue > 0:
            for player in active_players:
                player.market_share = float(player.total_revenue / total_revenue * 100)
                player.save()
    
    def _generate_default_decisions(self, player):
        """Generate conservative default decisions for timed-out players."""
        return {
            'production': {'continue_current': True},
            'procurement': {'maintain_inventory': True},
            'sales': {'current_prices': True},
            'hr': {'no_changes': True},
            'finance': {'conservative': True}
        }
    
    def _log_ai_actions(self, ai_player):
        """Log AI actions for transparency and analysis."""
        GameEvent.objects.create(
            multiplayer_game=self.game,
            event_type='ai_action',
            message=f"{ai_player.company_name} (AI) completed strategic analysis",
            data={
                'player_id': str(ai_player.id),
                'ai_strategy': ai_player.ai_strategy,
                'difficulty': ai_player.ai_difficulty
            },
            visible_to_all=False
        )
    
    def _get_market_leaders(self):
        """Get current market leaders by various metrics."""
        active_players = self.game.players.filter(is_active=True, is_bankrupt=False)
        
        if not active_players:
            return {}
        
        return {
            'revenue_leader': active_players.order_by('-total_revenue').first().company_name,
            'profit_leader': active_players.order_by('-total_profit').first().company_name,
            'production_leader': active_players.order_by('-bikes_produced').first().company_name,
            'balance_leader': active_players.order_by('-balance').first().company_name
        }
    
    def _has_reached_max_turns(self):
        """Check if game has reached maximum turns."""
        current_progress = (self.game.current_year - 2024) * 12 + self.game.current_month - 1
        return current_progress >= self.game.max_months
    
    def _determine_winners(self):
        """Determine game winners based on multiple criteria."""
        active_players = self.game.players.filter(is_active=True, is_bankrupt=False)
        
        if not active_players:
            return []
        
        # Primary winner: highest balance
        balance_winner = active_players.order_by('-balance').first()
        
        return [balance_winner]
    
    def _get_final_standings(self):
        """Get final standings for all players."""
        all_players = self.game.players.all().order_by('-balance')
        
        standings = []
        for i, player in enumerate(all_players, 1):
            standings.append({
                'rank': i,
                'company_name': player.company_name,
                'player_type': player.player_type,
                'final_balance': float(player.balance),
                'total_revenue': float(player.total_revenue),
                'total_profit': float(player.total_profit),
                'market_share': player.market_share,
                'is_bankrupt': player.is_bankrupt,
                'bankruptcy_month': f"{player.bankruptcy_year}/{player.bankruptcy_month:02d}" if player.is_bankrupt else None
            })
        
        return standings


class MultiplayerTurnManager:
    """Manages turn timing and synchronization for multiplayer games."""
    
    def __init__(self, multiplayer_game):
        self.game = multiplayer_game
        self.simulation_engine = MultiplayerSimulationEngine(multiplayer_game)
    
    def check_turn_ready_status(self):
        """Check if all players have submitted decisions or deadline passed."""
        active_players = self.game.players.filter(is_active=True, is_bankrupt=False)
        
        # Check submission status
        submitted_count = TurnState.objects.filter(
            multiplayer_game=self.game,
            month=self.game.current_month,
            year=self.game.current_year,
            decisions_submitted=True
        ).count()
        
        all_submitted = submitted_count >= active_players.count()
        
        # Check deadline
        deadline_passed = self._is_deadline_passed()
        
        return {
            'ready_to_process': all_submitted or deadline_passed,
            'all_submitted': all_submitted,
            'deadline_passed': deadline_passed,
            'submitted_count': submitted_count,
            'total_players': active_players.count()
        }
    
    def process_turn_if_ready(self):
        """Process turn if ready conditions are met."""
        status = self.check_turn_ready_status()
        
        if status['ready_to_process']:
            return self.simulation_engine.process_multiplayer_turn()
        
        return {
            'processed': False,
            'reason': 'Turn not ready for processing',
            'status': status
        }
    
    def _is_deadline_passed(self):
        """Check if turn deadline has passed."""
        if self.game.turn_deadline_hours <= 0:
            return False
        
        # Find the earliest turn state creation time for current turn
        earliest_turn = TurnState.objects.filter(
            multiplayer_game=self.game,
            month=self.game.current_month,
            year=self.game.current_year
        ).order_by('created_at').first()
        
        if not earliest_turn:
            return False
        
        deadline = earliest_turn.created_at + timedelta(hours=self.game.turn_deadline_hours)
        return timezone.now() > deadline