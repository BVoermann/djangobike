from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator
from .models import (
    ResearchProject, MarketingCampaign, SustainabilityInitiative, 
    BusinessStrategy, SustainabilityProfile
)


class ResearchProjectForm(forms.ModelForm):
    """Form for creating/editing R&D projects"""
    
    class Meta:
        model = ResearchProject
        fields = [
            'name', 'project_type', 'description', 'total_investment_required',
            'duration_months', 'production_efficiency_bonus', 'quality_bonus',
            'cost_reduction_bonus', 'sustainability_bonus', 'target_bike_types',
            'target_components'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'target_bike_types': forms.CheckboxSelectMultiple(),
            'target_components': forms.CheckboxSelectMultiple(),
        }
    
    def __init__(self, *args, session=None, **kwargs):
        super().__init__(*args, **kwargs)
        if session:
            # Filter target options by session
            self.fields['target_bike_types'].queryset = session.biketype_set.all()
            self.fields['target_components'].queryset = session.component_set.all()
        
        # Add CSS classes
        for field_name, field in self.fields.items():
            if field_name not in ['target_bike_types', 'target_components']:
                field.widget.attrs['class'] = 'form-control'


class StartResearchProjectForm(forms.Form):
    """Form to start an existing research project"""
    
    project = forms.ModelChoiceField(
        queryset=ResearchProject.objects.none(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Forschungsprojekt auswählen'
    )
    
    def __init__(self, *args, session=None, **kwargs):
        super().__init__(*args, **kwargs)
        if session:
            self.fields['project'].queryset = ResearchProject.objects.filter(
                session=session,
                status='planned'
            )


class MarketingCampaignForm(forms.ModelForm):
    """Form for creating/editing marketing campaigns"""
    
    class Meta:
        model = MarketingCampaign
        fields = [
            'name', 'campaign_type', 'target_segment', 'description',
            'total_budget', 'duration_months', 'immediate_demand_boost',
            'brand_awareness_boost', 'customer_loyalty_bonus',
            'price_premium_tolerance', 'target_markets', 'target_bike_types'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'target_markets': forms.CheckboxSelectMultiple(),
            'target_bike_types': forms.CheckboxSelectMultiple(),
        }
    
    def __init__(self, *args, session=None, **kwargs):
        super().__init__(*args, **kwargs)
        if session:
            # Filter target options by session
            from sales.models import Market
            self.fields['target_markets'].queryset = Market.objects.filter(session=session)
            self.fields['target_bike_types'].queryset = session.biketype_set.all()
        
        # Add CSS classes
        for field_name, field in self.fields.items():
            if field_name not in ['target_markets', 'target_bike_types']:
                field.widget.attrs['class'] = 'form-control'


class StartMarketingCampaignForm(forms.Form):
    """Form to start an existing marketing campaign"""
    
    campaign = forms.ModelChoiceField(
        queryset=MarketingCampaign.objects.none(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Marketing Kampagne auswählen'
    )
    
    def __init__(self, *args, session=None, **kwargs):
        super().__init__(*args, **kwargs)
        if session:
            self.fields['campaign'].queryset = MarketingCampaign.objects.filter(
                session=session,
                status='planned'
            )


class SustainabilityInitiativeForm(forms.ModelForm):
    """Form for creating/editing sustainability initiatives"""
    
    class Meta:
        model = SustainabilityInitiative
        fields = [
            'name', 'initiative_type', 'description', 'total_cost',
            'implementation_months', 'renewable_energy_bonus', 'waste_reduction_bonus',
            'sustainable_materials_bonus', 'local_sourcing_bonus',
            'certification_level_bonus', 'monthly_cost', 'requires_ongoing_investment'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add CSS classes
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            else:
                field.widget.attrs['class'] = 'form-control'


class StartSustainabilityInitiativeForm(forms.Form):
    """Form to start an existing sustainability initiative"""
    
    initiative = forms.ModelChoiceField(
        queryset=SustainabilityInitiative.objects.none(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Nachhaltigkeits-Initiative auswählen'
    )
    
    def __init__(self, *args, session=None, **kwargs):
        super().__init__(*args, **kwargs)
        if session:
            try:
                sustainability_profile = SustainabilityProfile.objects.get(session=session)
                self.fields['initiative'].queryset = SustainabilityInitiative.objects.filter(
                    session=session,
                    status='planned'
                )
            except SustainabilityProfile.DoesNotExist:
                self.fields['initiative'].queryset = SustainabilityInitiative.objects.none()


class BusinessStrategyForm(forms.ModelForm):
    """Form for editing overall business strategy"""
    
    class Meta:
        model = BusinessStrategy
        fields = [
            'rd_focus_percentage', 'marketing_focus_percentage',
            'sustainability_focus_percentage', 'operational_focus_percentage',
            'rd_monthly_budget', 'marketing_monthly_budget',
            'sustainability_monthly_budget'
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add CSS classes
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
        
        # Add help text for focus percentages
        self.fields['rd_focus_percentage'].help_text = 'Prozent (Gesamt sollte 100% ergeben)'
        self.fields['marketing_focus_percentage'].help_text = 'Prozent (Gesamt sollte 100% ergeben)'
        self.fields['sustainability_focus_percentage'].help_text = 'Prozent (Gesamt sollte 100% ergeben)'
        self.fields['operational_focus_percentage'].help_text = 'Prozent (Gesamt sollte 100% ergeben)'
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validate that focus percentages sum to 100
        rd_focus = cleaned_data.get('rd_focus_percentage', 0)
        marketing_focus = cleaned_data.get('marketing_focus_percentage', 0)
        sustainability_focus = cleaned_data.get('sustainability_focus_percentage', 0)
        operational_focus = cleaned_data.get('operational_focus_percentage', 0)
        
        total_focus = rd_focus + marketing_focus + sustainability_focus + operational_focus
        
        if abs(total_focus - 100.0) > 0.1:
            raise forms.ValidationError(
                f'Die Summe der Fokus-Prozente muss 100% ergeben. '
                f'Aktuell: {total_focus}%'
            )
        
        return cleaned_data


class SustainabilityProfileForm(forms.ModelForm):
    """Form for editing sustainability profile settings"""
    
    class Meta:
        model = SustainabilityProfile
        fields = [
            'sustainable_materials_percentage', 'recycled_materials_usage',
            'local_supplier_percentage', 'renewable_energy_usage'
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add CSS classes
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
        
        # Make fields read-only as they are updated through initiatives
        for field in self.fields.values():
            field.widget.attrs['readonly'] = True
            field.help_text = 'Wird durch Nachhaltigkeits-Initiativen aktualisiert'


class QuickStartProjectForm(forms.Form):
    """Quick form to start predefined projects"""
    
    PROJECT_CHOICES = [
        ('automation', 'Automatisierte Produktion (50.000€, 8 Monate)'),
        ('materials', 'Leichtbaurahmen-Technologie (35.000€, 6 Monate)'),
        ('smart_ebike', 'Smart E-Bike System (75.000€, 12 Monate)'),
        ('sustainable_paint', 'Nachhaltige Lackierung (25.000€, 4 Monate)'),
        ('quality_ai', 'Qualitätskontroll-KI (40.000€, 6 Monate)'),
    ]
    
    project_type = forms.ChoiceField(
        choices=PROJECT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Vordefiniertes Projekt starten'
    )


class QuickStartCampaignForm(forms.Form):
    """Quick form to start predefined campaigns"""
    
    CAMPAIGN_CHOICES = [
        ('spring', 'Frühjahrskampagne (15.000€, 3 Monate)'),
        ('sustainability', 'Nachhaltigkeit im Fokus (20.000€, 4 Monate)'),
        ('premium_launch', 'Premium E-Bike Launch (25.000€, 2 Monate)'),
        ('social_media', 'Social Media Boost (10.000€, 6 Monate)'),
    ]
    
    campaign_type = forms.ChoiceField(
        choices=CAMPAIGN_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Vordefinierte Kampagne starten'
    )


class QuickStartInitiativeForm(forms.Form):
    """Quick form to start predefined sustainability initiatives"""
    
    INITIATIVE_CHOICES = [
        ('solar', 'Solaranlage Installation (30.000€, 3 Monate)'),
        ('waste_reduction', 'Abfallreduktionsprogramm (15.000€, 2 Monate)'),
        ('local_suppliers', 'Lokale Lieferantennetzwerk (20.000€, 4 Monate)'),
        ('iso_certification', 'Umweltzertifizierung ISO 14001 (25.000€, 6 Monate)'),
    ]
    
    initiative_type = forms.ChoiceField(
        choices=INITIATIVE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Vordefinierte Initiative starten'
    )