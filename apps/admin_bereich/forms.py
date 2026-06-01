from django import forms

from .models import AppKonfiguration


class AppKonfigurationForm(forms.ModelForm):
    """Admin-Form: breitere Zahlenfelder; Risikotoleranz via eigenem Editor
    (im Change-Form-Template, serverseitig in ``save_model`` zusammengebaut),
    daher ist ``unternehmens_risikotoleranz`` hier nicht als Feld enthalten."""

    class Meta:
        model = AppKonfiguration
        fields = (
            "waehrung",
            "standard_seed", "seed_global",
            "standard_n_simulations", "n_simulations_global",
            "risikotoleranz_global",
        )
        widgets = {
            "standard_seed": forms.NumberInput(attrs={"style": "width: 16em;"}),
            "standard_n_simulations": forms.NumberInput(attrs={"style": "width: 16em;"}),
        }
