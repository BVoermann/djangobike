from django import forms
from .models import MultiplayerGame, GameParameters


class MultiplayerGameForm(forms.ModelForm):
    """Form for creating and editing multiplayer games"""

    parameters_file = forms.FileField(
        required=True,
        label='Parameter-Datei (ZIP)',
        help_text='ZIP-Datei mit allen Excel-Parameterdateien (Pflichtfeld)',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.zip'})
    )

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
            'parameters_file',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'max_players': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_months': forms.NumberInput(attrs={'class': 'form-control'}),
            'turn_deadline_hours': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'difficulty': forms.Select(attrs={'class': 'form-control'}),
            'bankruptcy_threshold': forms.NumberInput(attrs={'class': 'form-control'}),
            'starting_balance': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        help_texts = {
            'turn_deadline_hours': 'Stunden für Spieler zur Entscheidungsabgabe. Bei 0 springt das Spiel sofort weiter, wenn alle Spieler abgegeben haben.'
        }


class GameParametersForm(forms.ModelForm):
    """Form for editing game parameters"""

    class Meta:
        model = GameParameters
        fields = [
            # Supplier parameters
            'supplier_payment_terms_multiplier',
            'supplier_delivery_time_multiplier',
            'supplier_complaint_probability_multiplier',
            'supplier_complaint_quantity_multiplier',
            'component_cost_multiplier',
            # Bike parameters
            'bike_skilled_worker_hours_multiplier',
            'bike_unskilled_worker_hours_multiplier',
            'bike_storage_space_multiplier',
            # Bike price parameters
            'bike_price_cheap_multiplier',
            'bike_price_standard_multiplier',
            'bike_price_premium_multiplier',
            # Warehouse parameters
            'warehouse_cost_multiplier',
            'warehouse_capacity_multiplier',
            'component_storage_space_multiplier',
            # Market parameters
            'market_demand_multiplier',
            'market_distance_multiplier',
            'market_price_sensitivity_multiplier',
            'transport_cost_multiplier',
            'seasonal_effects_enabled',
            # Worker parameters
            'worker_cost_multiplier',
            'worker_hours_multiplier',
            'worker_productivity_multiplier',
            # Finance parameters
            'start_capital_multiplier',
            'interest_rate',
            'loan_availability_multiplier',
            'other_costs_multiplier',
            'inflation_rate',
            # Competitor parameters
            'competitor_aggressiveness',
            'competitor_financial_resources_multiplier',
            'competitor_efficiency_multiplier',
            'competitor_market_presence_multiplier',
            'competitor_marketing_budget_multiplier',
        ]
        widgets = {
            # Supplier parameters
            'supplier_payment_terms_multiplier': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0.1'}),
            'supplier_delivery_time_multiplier': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0.1'}),
            'supplier_complaint_probability_multiplier': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0.1'}),
            'supplier_complaint_quantity_multiplier': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0.1'}),
            'component_cost_multiplier': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0.1'}),
            # Bike parameters
            'bike_skilled_worker_hours_multiplier': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0.1'}),
            'bike_unskilled_worker_hours_multiplier': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0.1'}),
            'bike_storage_space_multiplier': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0.1'}),
            # Bike price parameters
            'bike_price_cheap_multiplier': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0.1'}),
            'bike_price_standard_multiplier': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0.1'}),
            'bike_price_premium_multiplier': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0.1'}),
            # Warehouse parameters
            'warehouse_cost_multiplier': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0.1'}),
            'warehouse_capacity_multiplier': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0.1'}),
            'component_storage_space_multiplier': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0.1'}),
            # Market parameters
            'market_demand_multiplier': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0.1'}),
            'market_distance_multiplier': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0.1'}),
            'market_price_sensitivity_multiplier': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0.1'}),
            'transport_cost_multiplier': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0.1'}),
            # Worker parameters
            'worker_cost_multiplier': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0.1'}),
            'worker_hours_multiplier': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0.1'}),
            'worker_productivity_multiplier': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0.1'}),
            # Finance parameters
            'start_capital_multiplier': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0.1'}),
            'interest_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'loan_availability_multiplier': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0.1'}),
            'other_costs_multiplier': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0.1'}),
            'inflation_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            # Competitor parameters
            'competitor_aggressiveness': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0.1', 'max': '2.0'}),
            'competitor_financial_resources_multiplier': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0.1'}),
            'competitor_efficiency_multiplier': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0.1'}),
            'competitor_market_presence_multiplier': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0.1'}),
            'competitor_marketing_budget_multiplier': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0.1'}),
        }
        labels = {
            # Supplier parameters
            'supplier_payment_terms_multiplier': 'Zahlungsziel-Multiplikator',
            'supplier_delivery_time_multiplier': 'Lieferzeit-Multiplikator',
            'supplier_complaint_probability_multiplier': 'Reklamationswahrscheinlichkeit-Multiplikator',
            'supplier_complaint_quantity_multiplier': 'Reklamationsmenge-Multiplikator',
            'component_cost_multiplier': 'Komponentenkosten-Multiplikator',
            # Bike parameters
            'bike_skilled_worker_hours_multiplier': 'Facharbeiter-Stunden-Multiplikator',
            'bike_unskilled_worker_hours_multiplier': 'Hilfsarbeiter-Stunden-Multiplikator',
            'bike_storage_space_multiplier': 'Fahrrad-Lagerplatz-Multiplikator',
            # Bike price parameters
            'bike_price_cheap_multiplier': 'Günstig-Segment Preis-Multiplikator',
            'bike_price_standard_multiplier': 'Standard-Segment Preis-Multiplikator',
            'bike_price_premium_multiplier': 'Premium-Segment Preis-Multiplikator',
            # Warehouse parameters
            'warehouse_cost_multiplier': 'Lagerkosten-Multiplikator',
            'warehouse_capacity_multiplier': 'Lagerkapazität-Multiplikator',
            'component_storage_space_multiplier': 'Komponenten-Lagerplatz-Multiplikator',
            # Market parameters
            'market_demand_multiplier': 'Marktnachfrage-Multiplikator',
            'market_distance_multiplier': 'Marktentfernung-Multiplikator',
            'market_price_sensitivity_multiplier': 'Preissensibilität-Multiplikator',
            'transport_cost_multiplier': 'Transportkosten-Multiplikator',
            'seasonal_effects_enabled': 'Saisonale Effekte aktivieren',
            # Worker parameters
            'worker_cost_multiplier': 'Arbeitskosten-Multiplikator',
            'worker_hours_multiplier': 'Arbeitsstunden-Multiplikator',
            'worker_productivity_multiplier': 'Produktivität-Multiplikator',
            # Finance parameters
            'start_capital_multiplier': 'Startkapital-Multiplikator',
            'interest_rate': 'Zinssatz',
            'loan_availability_multiplier': 'Kreditverfügbarkeit-Multiplikator',
            'other_costs_multiplier': 'Sonstige-Kosten-Multiplikator',
            'inflation_rate': 'Inflationsrate',
            # Competitor parameters
            'competitor_aggressiveness': 'Konkurrenz-Aggressivität',
            'competitor_financial_resources_multiplier': 'Konkurrenz-Kapital-Multiplikator',
            'competitor_efficiency_multiplier': 'Konkurrenz-Effizienz-Multiplikator',
            'competitor_market_presence_multiplier': 'Konkurrenz-Marktanteil-Multiplikator',
            'competitor_marketing_budget_multiplier': 'Konkurrenz-Marketing-Multiplikator',
        }
