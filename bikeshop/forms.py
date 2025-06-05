from django import forms
from .models import GameSession

class ParameterUploadForm(forms.Form):
    parameter_file = forms.FileField(
        label='Parameter ZIP-Datei',
        help_text='Laden Sie eine ZIP-Datei mit den Simulationsparametern hoch.',
        widget=forms.ClearableFileInput(attrs={
            'accept': '.zip',
            'class': 'form-control'
        })
    )

class SessionCreateForm(forms.ModelForm):
    class Meta:
        model = GameSession
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Name der Spielsession'
            })
        }
