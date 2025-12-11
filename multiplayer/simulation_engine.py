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
import random

logger = logging.getLogger(__name__)


def generate_outcome_message(quantity_sold, quantity_planned, price_segment, market, unsold_reason):
    """Generate narrative feedback about sales outcome without revealing mechanics."""
    success_rate = (quantity_sold / quantity_planned * 100) if quantity_planned > 0 else 0

    if success_rate == 100:
        messages = [
            "Excellent! All your bikes found buyers.",
            "Perfect timing! Complete sell-out achieved.",
            "Outstanding performance! Every bike was sold."
        ]
        return random.choice(messages)

    elif success_rate >= 80:
        return f"Strong sales! {quantity_sold} out of {quantity_planned} bikes sold. The market was receptive to your offering."

    elif success_rate >= 50:
        remaining = quantity_planned - quantity_sold
        return f"Moderate success. {quantity_sold} bikes sold, {remaining} remain in inventory. Consider adjusting your strategy."

    elif success_rate >= 20:
        remaining = quantity_planned - quantity_sold
        if unsold_reason and 'price' in unsold_reason.lower():
            return f"Limited sales. {quantity_sold} of {quantity_planned} sold. Your pricing may not have matched market expectations."
        elif unsold_reason and 'oversaturated' in unsold_reason.lower():
            return f"Competitive market. {quantity_sold} of {quantity_planned} sold. Many competitors were targeting the same customers."
        else:
            return f"Challenging conditions. Only {quantity_sold} of {quantity_planned} bikes sold. Market demand was lower than anticipated."

    else:
        if quantity_sold == 0:
            return "No sales completed. Your bikes didn't find buyers this turn. Consider revising your market approach."
        else:
            return f"Very limited success. Only {quantity_sold} of {quantity_planned} bikes sold. Significant inventory remains."


def generate_market_condition_description(market, bike_type, supply_demand_ratio):
    """Describe market conditions narratively."""
    # Don't reveal exact numbers, use qualitative descriptions

    if supply_demand_ratio < 0.5:
        condition = "High demand, low competition"
        description = "The market had strong appetite for bikes with limited competition."
    elif supply_demand_ratio < 0.8:
        condition = "Healthy market"
        description = "Good market conditions with balanced supply and demand."
    elif supply_demand_ratio < 1.2:
        condition = "Competitive market"
        description = "Many sellers competed for available customers."
    else:
        condition = "Oversaturated market"
        description = "The market was flooded with offerings, limiting individual success."

    # Add location-specific color if relevant
    if hasattr(market, 'green_city_factor') and hasattr(bike_type, 'name'):
        if market.green_city_factor > 1.2 and 'e-bike' in bike_type.name.lower():
            description += " This city's eco-conscious population favored e-bikes."
        elif hasattr(market, 'mountain_bike_factor') and market.mountain_bike_factor > 1.2 and 'mountain' in bike_type.name.lower():
            description += " The mountainous terrain increased demand for mountain bikes."

    return {
        'condition': condition,
        'description': description
    }


def generate_competitive_position(player_price, average_market_price, player_quality=None):
    """Describe how player's offering compared to competition."""
    if average_market_price == 0:
        return "You were the only seller in this market segment."

    price_ratio = player_price / average_market_price if average_market_price > 0 else 1.0

    if price_ratio < 0.85:
        return "Your competitive pricing gave you an advantage in the market."
    elif price_ratio < 0.95:
        return "Your pricing was slightly below market average, helping sales."
    elif price_ratio < 1.05:
        return "Your pricing aligned with market expectations."
    elif price_ratio < 1.15:
        return "Your pricing was slightly higher than competitors, which may have affected sales."
    else:
        return "Your premium pricing positioned you at the higher end of the market."


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
    
    def _process_multiplayer_market_segment(self, market, bike_type, price_segment, player_decisions, month, year):
        """
        Process sales for a multiplayer market segment where each player has their own session/bikes.

        This is adapted from MarketSimulator but handles multiple players with separate GameSessions.
        """
        from sales.models import Market, SalesOrder
        from production.models import ProducedBike
        from finance.models import Transaction
        import random

        logger.info(f"Processing multiplayer market segment: {market.name} - {bike_type.name} ({price_segment})")

        # Calculate market demand (use first player's session for market data)
        first_session = player_decisions[0].session
        base_demand = self._calculate_market_demand(market, bike_type, price_segment, month, first_session)
        logger.info(f"Base demand: {base_demand} bikes")

        # Collect all offers from all players
        all_offers = []

        for decision in player_decisions:
            # Find available bikes from THIS player's session
            available_bikes = ProducedBike.objects.filter(
                session=decision.session,  # Use the decision's session, not a shared one
                bike_type=bike_type,
                price_segment=price_segment,
                is_sold=False
            )[:decision.quantity]

            if len(available_bikes) < decision.quantity:
                logger.warning(
                    f"Player {decision._player_session.company_name}: Requested {decision.quantity} bikes but only {len(available_bikes)} available"
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
                    'quality_factor': self._get_quality_factor_for_segment(price_segment),
                    'player_session': decision._player_session,
                })

        logger.info(f"Total offers: {len(all_offers)} from {len(player_decisions)} players")

        # Sort offers by effective price (lower prices sell first)
        # Add small random factor for realism (10% variance)
        for offer in all_offers:
            random_factor = random.uniform(0.95, 1.05)
            offer['sort_price'] = float(offer['price']) * random_factor / offer['quality_factor']

        all_offers.sort(key=lambda x: x['sort_price'])

        # Apply price elasticity - higher average prices reduce demand
        if all_offers:
            avg_price = sum(float(offer['price']) for offer in all_offers) / len(all_offers)
            base_price = self._get_base_price_for_segment(price_segment)
            price_ratio = avg_price / base_price if base_price > 0 else 1.0
            elasticity_adjustment = 1.0 - (price_ratio - 1.0) * 0.3  # Simple elasticity
            elasticity_adjustment = max(0.3, min(1.5, elasticity_adjustment))
            adjusted_demand = int(base_demand * elasticity_adjustment)
            logger.info(f"Demand adjusted for price elasticity: {base_demand} -> {adjusted_demand}")
        else:
            adjusted_demand = base_demand

        # Allocate sales based on demand
        bikes_to_sell = min(len(all_offers), adjusted_demand)
        logger.info(f"Allocating {bikes_to_sell} sales out of {len(all_offers)} offers (demand: {adjusted_demand})")

        # Execute sales for the top offers
        for i, offer in enumerate(all_offers[:bikes_to_sell]):
            self._execute_multiplayer_player_sale(offer, month, year)

        # Mark remaining offers as unsold
        for offer in all_offers[bikes_to_sell:]:
            decision = offer['decision']
            if not hasattr(decision, '_temp_unsold_count'):
                decision._temp_unsold_count = 0
            decision._temp_unsold_count += 1

        # Update all player decisions with results
        for decision in player_decisions:
            sold_count = getattr(decision, '_temp_sold_count', 0)
            unsold_count = getattr(decision, '_temp_unsold_count', 0)
            total_revenue = getattr(decision, '_temp_total_revenue', Decimal('0'))

            decision.quantity_sold = sold_count
            decision.actual_revenue = total_revenue
            decision.is_processed = True

            if unsold_count > 0:
                if sold_count == 0:
                    decision.unsold_reason = 'market_oversaturated_no_sales'
                else:
                    decision.unsold_reason = 'market_oversaturated_partial_sales'

            logger.info(
                f"Player {decision._player_session.company_name}: {sold_count}/{decision.quantity} sold, revenue: {total_revenue}€"
            )

    def _execute_multiplayer_player_sale(self, offer, month, year):
        """Execute a sale for a player in multiplayer context."""
        from sales.models import SalesOrder
        from finance.models import Transaction

        decision = offer['decision']
        bike = offer['bike']
        sale_price = offer['price']
        transport_cost = offer['transport_cost']
        player_session = offer['player_session']

        # Mark bike as sold
        bike.is_sold = True
        bike.selling_price = sale_price
        bike.save()

        # Create sales order
        sales_order = SalesOrder.objects.create(
            session=decision.session,
            market=decision.market,
            bike=bike,
            sale_price=sale_price,
            transport_cost=transport_cost,
            sale_month=month,
            sale_year=year
        )

        # Calculate net revenue (after transport cost)
        # Transport cost is per shipment, not per bike, but we divide it across bikes
        net_revenue = sale_price - (transport_cost / Decimal(str(decision.quantity)))

        # Update decision statistics
        if not hasattr(decision, '_temp_sold_count'):
            decision._temp_sold_count = 0
        if not hasattr(decision, '_temp_total_revenue'):
            decision._temp_total_revenue = Decimal('0')

        decision._temp_sold_count += 1
        decision._temp_total_revenue += net_revenue

        # Update player balance using BalanceManager
        from multiplayer.balance_manager import BalanceManager
        game_session = decision.session
        balance_mgr = BalanceManager(player_session, game_session)
        balance_mgr.add_to_balance(net_revenue, reason=f"bike_sale_{bike.id}")

        # Create transaction record
        Transaction.objects.create(
            session=game_session,
            transaction_type='sale',
            amount=net_revenue,
            description=f'Verkauf: {bike.bike_type.name} ({bike.get_price_segment_display()})',
            month=month,
            year=year
        )

        logger.info(f"Sale executed: {bike.bike_type.name} for {sale_price}€ (net: {net_revenue}€)")

    def _calculate_market_demand(self, market, bike_type, price_segment, month, session):
        """Calculate market demand for a specific bike type/segment."""
        # Base capacity from market
        base_capacity = market.monthly_volume_capacity if hasattr(market, 'monthly_volume_capacity') else 200

        # Adjust for bike type based on location characteristics
        bike_type_multiplier = market.get_bike_type_demand_multiplier(bike_type.name) if hasattr(market, 'get_bike_type_demand_multiplier') else 1.0

        # Segment distribution
        segment_distribution = {
            'cheap': 0.4,
            'standard': 0.4,
            'premium': 0.2
        }
        segment_factor = segment_distribution.get(price_segment, 0.33)

        # Seasonal adjustment (simple)
        seasonal_factor = 1.0
        if month in [5, 6, 7, 8]:  # Summer months
            seasonal_factor = 1.2
        elif month in [11, 12, 1, 2]:  # Winter months
            seasonal_factor = 0.8

        # Calculate final demand
        demand = int(base_capacity * bike_type_multiplier * segment_factor * seasonal_factor)

        # Add some randomness (±10%)
        variance = random.uniform(0.9, 1.1)
        demand = int(demand * variance)

        return max(1, demand)  # At least 1 bike demand

    def _get_quality_factor_for_segment(self, price_segment):
        """Get quality multiplier for price segment."""
        quality_factors = {
            'cheap': 0.8,
            'standard': 1.0,
            'premium': 1.2
        }
        return quality_factors.get(price_segment, 1.0)

    def _get_base_price_for_segment(self, price_segment):
        """Get baseline expected price for a segment."""
        base_prices = {
            'cheap': Decimal('300'),
            'standard': Decimal('500'),
            'premium': Decimal('800')
        }
        return base_prices.get(price_segment, Decimal('500'))

    def _process_market_competition(self):
        """Process market competition using MarketSimulator for deferred sales.

        This integrates the singleplayer MarketSimulator to handle multiplayer
        sales decisions stored in TurnState objects.
        """
        try:
            from sales.market_simulator import MarketSimulator
            from sales.models import Market, SalesDecision
            from production.models import ProducedBike
            from finance.models import Transaction
            from bikeshop.models import BikeType
            from decimal import Decimal

            active_players = self.game.players.filter(is_active=True, is_bankrupt=False)

            # Group all sales decisions by market and segment
            market_segment_decisions = {}

            # Collect all player sales decisions from TurnState
            for player in active_players:
                game_session = self._get_or_create_game_session(player)

                turn_state = TurnState.objects.filter(
                    multiplayer_game=self.game,
                    player_session=player,
                    month=self.game.current_month,
                    year=self.game.current_year
                ).first()

                if not turn_state or not turn_state.sales_decisions:
                    logger.info(f"No sales decisions for player {player.company_name}")
                    continue

                # Process each decision
                for decision_data in turn_state.sales_decisions:
                    market_id = decision_data['market_id']
                    bike_type_id = decision_data['bike_type_id']
                    price_segment = decision_data['price_segment']

                    # Create key for grouping
                    key = (market_id, bike_type_id, price_segment)

                    if key not in market_segment_decisions:
                        market_segment_decisions[key] = []

                    # Create temporary SalesDecision object (not saved to DB)
                    # MarketSimulator expects SalesDecision objects
                    market = Market.objects.get(id=market_id, session=game_session)
                    bike_type = BikeType.objects.get(id=bike_type_id, session=game_session)

                    temp_decision = SalesDecision(
                        session=game_session,
                        market=market,
                        bike_type=bike_type,
                        price_segment=price_segment,
                        quantity=decision_data['quantity'],
                        desired_price=Decimal(str(decision_data['desired_price'])),
                        transport_cost=Decimal(str(decision_data['transport_cost'])),
                        decision_month=self.game.current_month,
                        decision_year=self.game.current_year,
                        is_processed=False
                    )
                    # Store reference to player and turn_state for later processing
                    temp_decision._player_session = player
                    temp_decision._turn_state = turn_state

                    market_segment_decisions[key].append(temp_decision)

            # Process each market segment using multiplayer-aware sales processing
            for (market_id, bike_type_id, price_segment), decisions in market_segment_decisions.items():
                if not decisions:
                    continue

                # Get market and bike_type
                first_decision = decisions[0]
                market = first_decision.market
                bike_type = first_decision.bike_type

                logger.info(f"Processing market segment: {market.name} - {bike_type.name} ({price_segment}) with {len(decisions)} players")

                # Process sales for this market segment with all players' bikes
                self._process_multiplayer_market_segment(
                    market=market,
                    bike_type=bike_type,
                    price_segment=price_segment,
                    player_decisions=decisions,
                    month=self.game.current_month,
                    year=self.game.current_year
                )

                # Calculate supply/demand ratio and average prices for this segment
                total_quantity_offered = sum(d.quantity for d in decisions)
                total_quantity_sold_segment = sum(getattr(d, 'quantity_sold', 0) for d in decisions)
                supply_demand_ratio = total_quantity_offered / total_quantity_sold_segment if total_quantity_sold_segment > 0 else 2.0

                # Calculate average market price for competitive position
                total_price_sum = sum(float(d.desired_price) for d in decisions)
                average_market_price = total_price_sum / len(decisions) if decisions else 0

                # Store results in each player's TurnState with narrative feedback
                for decision in decisions:
                    player = decision._player_session
                    turn_state = decision._turn_state

                    # Get actual sold count
                    quantity_sold = decision.quantity_sold if hasattr(decision, 'quantity_sold') else 0
                    actual_revenue = decision.actual_revenue if hasattr(decision, 'actual_revenue') else 0
                    unsold_reason = decision.unsold_reason if hasattr(decision, 'unsold_reason') else ''

                    # Initialize sales_results if needed
                    if not turn_state.sales_results or not isinstance(turn_state.sales_results, dict):
                        turn_state.sales_results = {
                            'total_sold': 0,
                            'total_revenue': 0,
                            'total_unsold': 0,
                            'success_rate': 0,
                            'decisions': []
                        }

                    # Get price segment display name
                    segment_display_map = {
                        'cheap': 'Cheap',
                        'standard': 'Standard',
                        'premium': 'Premium'
                    }
                    price_segment_display = segment_display_map.get(price_segment, price_segment.title())

                    # Add decision result with narrative feedback
                    decision_result = {
                        'market_name': market.name,
                        'bike_type_name': bike_type.name,
                        'price_segment': price_segment,
                        'price_segment_display': price_segment_display,
                        'quantity_planned': decision.quantity,
                        'quantity_sold': quantity_sold,
                        'quantity_unsold': decision.quantity - quantity_sold,
                        'desired_price': float(decision.desired_price),
                        'actual_revenue': float(actual_revenue),
                        'unsold_reason': unsold_reason,
                        'success_rate': (quantity_sold / decision.quantity * 100) if decision.quantity > 0 else 0,

                        # NARRATIVE FEEDBACK
                        'outcome_message': generate_outcome_message(
                            quantity_sold,
                            decision.quantity,
                            price_segment,
                            market,
                            unsold_reason
                        ),
                        'market_condition': generate_market_condition_description(
                            market,
                            bike_type,
                            supply_demand_ratio
                        ),
                        'competitive_position': generate_competitive_position(
                            float(decision.desired_price),
                            average_market_price
                        )
                    }

                    turn_state.sales_results['decisions'].append(decision_result)
                    turn_state.sales_results['total_sold'] += quantity_sold
                    turn_state.sales_results['total_revenue'] += float(actual_revenue)
                    turn_state.sales_results['total_unsold'] += (decision.quantity - quantity_sold)

                    # Update TurnState performance metrics
                    turn_state.bikes_sold_this_turn += quantity_sold
                    turn_state.revenue_this_turn += Decimal(str(actual_revenue))

                # Calculate overall success rate for each player after processing all segments
                for decision in decisions:
                    player = decision._player_session
                    turn_state = decision._turn_state

                    # Calculate overall success rate
                    total_attempted = sum(d['quantity_planned'] for d in turn_state.sales_results['decisions'])
                    total_sold = turn_state.sales_results['total_sold']
                    turn_state.sales_results['success_rate'] = (total_sold / total_attempted * 100) if total_attempted > 0 else 0

                    turn_state.save()

                    # Update PlayerSession metrics
                    player.bikes_sold += getattr(decision, 'quantity_sold', 0)
                    player.total_revenue += Decimal(str(getattr(decision, 'actual_revenue', 0)))
                    player.save()

                    # Create GameEvent for significant outcomes
                    if unsold_reason and unsold_reason != '':
                        GameEvent.objects.create(
                            multiplayer_game=self.game,
                            event_type='market_event',
                            message=f"{player.company_name}: {quantity_sold}/{decision.quantity} {bike_type.name} verkauft in {market.name}",
                            data={
                                'player_id': str(player.id),
                                'market': market.name,
                                'bike_type': bike_type.name,
                                'quantity_sold': quantity_sold,
                                'quantity_planned': decision.quantity,
                                'reason': unsold_reason
                            },
                            visible_to_all=False
                        )

                        # Make visible only to this player
                        event = GameEvent.objects.filter(
                            multiplayer_game=self.game,
                            data__player_id=str(player.id)
                        ).order_by('-timestamp').first()
                        if event:
                            event.visible_to.add(player)

            # Update market share calculations
            self._update_market_shares()

            logger.info("Market competition processing completed using MarketSimulator")

        except Exception as e:
            logger.error(f"Error processing market competition: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
    
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
        # Record when this turn was processed
        self.game.last_turn_processed_at = timezone.now()

        # Advance month
        if self.game.current_month == 12:
            self.game.current_month = 1
            self.game.current_year += 1
        else:
            self.game.current_month += 1

        self.game.save()

        # Reset worker hours for all players for the new month
        self._reset_all_player_worker_hours()

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

    def _reset_all_player_worker_hours(self):
        """Reset worker hours for all active players for the new month."""
        from bikeshop.models import Worker

        active_players = self.game.players.filter(is_active=True, is_bankrupt=False)

        for player in active_players:
            try:
                game_session = self._get_or_create_game_session(player)
                workers = Worker.objects.filter(session=game_session)

                for worker in workers:
                    worker.used_hours_this_month = Decimal('0')
                    worker.tracking_month = self.game.current_month
                    worker.tracking_year = self.game.current_year
                    worker.save()

                logger.info(f"Reset worker hours for {player.company_name}")

            except Exception as e:
                logger.error(f"Error resetting worker hours for {player.company_name}: {str(e)}")

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
        game_session.save()

        # Sync balance using BalanceManager (PlayerSession is source of truth)
        from .balance_manager import BalanceManager
        balance_mgr = BalanceManager(player, game_session)
        balance_mgr.sync_balances()

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
        # Sync balance from GameSession back to PlayerSession after turn processing
        # GameSession may have been modified by SimulationEngine.process_month()
        from .balance_manager import BalanceManager
        game_session = self._get_or_create_game_session(player)

        # Special case: After turn processing, GameSession.balance may have changed
        # Update PlayerSession.balance to match (reverse sync for this case only)
        game_session.refresh_from_db()
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

        logger.info(
            f"Updated metrics for {player.company_name}: "
            f"Balance={player.balance}€, Revenue={turn_revenue}€, Profit={turn_profit}€"
        )
    
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
        # First check if enough time has passed since last turn
        can_process, remaining_time = self.game.can_process_next_turn()

        if not can_process:
            countdown = self.game.get_next_turn_countdown()
            return {
                'processed': False,
                'reason': 'Waiting for turn duration to elapse',
                'waiting_for_time': True,
                'remaining_time': countdown,
                'message': f'Next turn can be processed in {countdown}'
            }

        # Then check if all players have submitted
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