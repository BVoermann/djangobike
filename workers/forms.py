from django import forms
from .models import Worker


class WorkerForm(forms.ModelForm):
    class Meta:
        model = Worker
        fields = ['name', 'worker_type', 'hourly_wage', 'efficiency', 'experience_level']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Name des Arbeiters eingeben'
            }),
            'worker_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'hourly_wage': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01'
            }),
            'efficiency': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '200'
            }),
            'experience_level': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '10'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Setze Standard-Löhne basierend auf Arbeitertyp
        if not self.instance.pk:  # Nur bei neuen Arbeitern
            self.fields['hourly_wage'].help_text = "Empfohlen: Facharbeiter 25-35€/h, Hilfsarbeiter 15-20€/h"


class QuickHireForm(forms.Form):
    WORKER_CHOICES = [
        ('skilled', 'Facharbeiter'),
        ('unskilled', 'Hilfsarbeiter'),
    ]

    worker_type = forms.ChoiceField(
        choices=WORKER_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Arbeitertyp"
    )

    count = forms.IntegerField(
        min_value=1,
        max_value=10,
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label="Anzahl"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['worker_type'].help_text = "Wählen Sie den Typ der Arbeiter aus"
        self.fields['count'].help_text = "Anzahl der Arbeiter, die eingestellt werden sollen"