# Balance Management System - Multiplayer Games

## Overview

The balance management system ensures that each player's financial balance in multiplayer games is stored correctly and synchronized between the two database models that need it.

## Architecture

### Source of Truth: `PlayerSession.balance`

In multiplayer games, **`PlayerSession.balance` is the authoritative source of truth**. This field stores each player's balance for their specific game instance.

### Synchronized Copy: `GameSession.balance`

For compatibility with existing singleplayer code, each player also has a `GameSession` object. The `GameSession.balance` field is kept synchronized with `PlayerSession.balance` to ensure the singleplayer simulation engine works correctly.

## Why Two Balance Fields?

- **`PlayerSession.balance`**: Multiplayer-specific model, stores balance per player per game
- **`GameSession.balance`**: Singleplayer model reused for multiplayer, needed for compatibility with existing simulation code

The dual system allows us to:
1. Store each player's balance specific to their game (multiplayer requirement)
2. Reuse existing singleplayer simulation code without modifications
3. Maintain data integrity through automatic synchronization

## Using the Balance Manager

### Basic Usage

```python
from multiplayer.balance_manager import get_balance_manager

# Get balance manager for a player
balance_mgr = get_balance_manager(player_session, game_session)

# Get current balance
current_balance = balance_mgr.get_balance()

# Subtract from balance (e.g., for purchases)
balance_mgr.subtract_from_balance(
    amount=Decimal('5000.00'),
    reason="procurement_order"
)

# Add to balance (e.g., for sales revenue)
balance_mgr.add_to_balance(
    amount=Decimal('10000.00'),
    reason="sales_revenue"
)

# Set specific balance
balance_mgr.set_balance(
    new_balance=Decimal('75000.00'),
    reason="balance_correction"
)

# Force synchronization
balance_mgr.sync_balances()

# Check for and fix mismatches
had_mismatch, current_balance = balance_mgr.check_and_fix_balance_mismatch()
```

### Direct Import

```python
from multiplayer.balance_manager import BalanceManager

balance_mgr = BalanceManager(player_session, game_session)
balance_mgr.subtract_from_balance(amount, reason="purchase")
```

## Synchronization Points

The balance is automatically synchronized at these points:

1. **Player Initialization** (`player_state_manager.py:initialize_player_game_state`)
   - When a player joins a game
   - PlayerSession.balance → GameSession.balance

2. **Procurement Orders** (`views.py:multiplayer_procurement`)
   - When a player purchases components
   - Both balances updated atomically

3. **Turn Processing** (`simulation_engine.py:_update_player_metrics`)
   - After each turn is processed
   - GameSession.balance → PlayerSession.balance (reverse sync)
   - This is the only place where GameSession is treated as source

4. **Session Retrieval** (`simulation_engine.py:_get_or_create_game_session`)
   - When getting/creating a game session
   - PlayerSession.balance → GameSession.balance

## Management Command

A Django management command is available to check and fix balance synchronization issues:

### Check for Mismatches

```bash
python manage.py sync_multiplayer_balances --check-only
```

### Fix All Mismatches

```bash
python manage.py sync_multiplayer_balances
```

### Fix Specific Game

```bash
python manage.py sync_multiplayer_balances --game-id <GAME_UUID>
```

## Important Rules

1. **Always use BalanceManager** for balance updates in multiplayer code
2. **Never directly modify** `PlayerSession.balance` or `GameSession.balance` outside of BalanceManager
3. **PlayerSession.balance is source of truth** except during turn processing
4. **All balance updates are atomic** - wrapped in database transactions
5. **Logging is automatic** - all balance changes are logged for debugging

## Exception: Turn Processing

The only exception to "PlayerSession is source of truth" is during turn processing:

- The singleplayer `SimulationEngine.process_month()` modifies `GameSession.balance`
- After processing, `_update_player_metrics()` syncs back to `PlayerSession.balance`
- This allows reuse of existing simulation code without modifications

## Files Modified

### New Files Created
- `multiplayer/balance_manager.py` - Core balance management logic
- `multiplayer/management/commands/sync_multiplayer_balances.py` - Management command
- `BALANCE_MANAGEMENT.md` - This documentation

### Files Updated
- `multiplayer/models.py` - Added documentation to PlayerSession
- `multiplayer/player_state_manager.py` - Uses BalanceManager for initialization
- `multiplayer/simulation_engine.py` - Uses BalanceManager for synchronization
- `multiplayer/views.py` - Uses BalanceManager for procurement

## Testing

All balance operations have been tested:
- ✓ Initial balance synchronization
- ✓ Balance deduction (subtract_from_balance)
- ✓ Balance addition (add_to_balance)
- ✓ Balance setting (set_balance)
- ✓ Automatic synchronization
- ✓ Mismatch detection and fixing

## Migration Notes

For existing games, run the sync command to ensure all balances are synchronized:

```bash
python manage.py sync_multiplayer_balances
```

This is safe to run multiple times and will not cause issues.
