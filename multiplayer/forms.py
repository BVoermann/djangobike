from django import forms
from .models import MultiplayerGame, GameParameters


class MultiplayerGameForm(forms.ModelForm):
    """Form for creating and editing multiplayer games"""

    class Meta:
        model = MultiplayerGame
        fields = [
            'name',
            'description',
            'max_players',
            'max_months',
            'turn_deadline_hours',
            'status',
            'difficulty',
            'allow_bankruptcy',
            'bankruptcy_threshold',
            'starting_balance',
            'enable_real_time_updates',
            'enable_player_chat',
            'enable_market_intelligence',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'max_players': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_months': forms.NumberInput(attrs={'class': 'form-control'}),
            'turn_deadline_hours': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'difficulty': forms.Select(attrs={'class': 'form-control'}),
            'bankruptcy_threshold': forms.NumberInput(attrs={'class': 'form-control'}),
            'starting_balance': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class GameParametersForm(forms.ModelForm):
    """Form for editing game parameters"""

    class Meta:
        model = GameParameters
        fields = [
            'market_demand_multiplier',
            'seasonal_effects_enabled',
            'inflation_rate',
            'interest_rate',
            'component_cost_multiplier',
            'worker_cost_multiplier',
            'transport_cost_multiplier',
            'warehouse_cost_multiplier',
            'competitor_aggressiveness',
        ]
        widgets = {
            'market_demand_multiplier': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'inflation_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'interest_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'component_cost_multiplier': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'worker_cost_multiplier': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'transport_cost_multiplier': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'warehouse_cost_multiplier': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'competitor_aggressiveness': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
        }
        labels = {
            'market_demand_multiplier': 'Marktnachfrage-Multiplikator',
            'seasonal_effects_enabled': 'Saisonale Effekte aktivieren',
            'inflation_rate': 'Inflationsrate',
            'interest_rate': 'Zinssatz',
            'component_cost_multiplier': 'Komponentenkosten-Multiplikator',
            'worker_cost_multiplier': 'Arbeitskosten-Multiplikator',
            'transport_cost_multiplier': 'Transportkosten-Multiplikator',
            'warehouse_cost_multiplier': 'Lagerkosten-Multiplikator',
            'competitor_aggressiveness': 'Konkurrenz-Aggressivität',
        }
