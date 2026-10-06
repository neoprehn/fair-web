from django import forms

from .models import AppKonfiguration


class AppKonfigurationForm(forms.ModelForm):
    """Admin-Form: breitere Zahlenfelder; Risikotoleranz via eigenem Editor
    (im Change-Form-Template, serverseitig in ``save_model`` zusammengebaut),
    daher ist ``unternehmens_risikotoleranz`` hier nicht als Feld enthalten.

    ``deepl_api_key`` ist wie bei ``KIEinstellungForm`` (apps.konten.forms) ein separates,
    nicht modellgebundenes Feld: leer gelassen bleibt ein bereits gespeicherter Key
    unverändert, ein neuer Wert wird verschlüsselt in ``deepl_api_key_verschluesselt`` abgelegt.
    """

    deepl_api_key = forms.CharField(
        label="DeepL-API-Key", required=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "off"}),
        help_text="Leer lassen, um einen bereits gespeicherten Key unverändert zu lassen.",
    )

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.hat_deepl_api_key:
            self.fields["deepl_api_key"].help_text = "Bereits hinterlegt – " + self.fields["deepl_api_key"].help_text

    def save(self, commit=True):
        instance = super().save(commit=False)
        deepl_api_key = self.cleaned_data.get("deepl_api_key")
        if deepl_api_key:
            instance.set_deepl_api_key(deepl_api_key)
        if commit:
            instance.save()
        return instance
