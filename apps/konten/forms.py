from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.forms import PasswordInput, TextInput

from .models import KIEinstellung


class RegistrierForm(UserCreationForm):
    """Selbstregistrierung (Benutzername + Passwort), Bootstrap-Styling."""

    class Meta(UserCreationForm.Meta):
        fields = ("username",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for feld in self.fields.values():
            feld.widget.attrs["class"] = "form-control"


class KIEinstellungForm(forms.ModelForm):
    """Pro-Nutzer-Konfiguration für den optionalen KI-Assistenten.

    Der API-Key ist ein separates, nicht modellgebundenes Feld: leer
    gelassen bleibt ein bereits gespeicherter Key unverändert, ein neuer
    Wert wird verschlüsselt in ``api_key_verschluesselt`` abgelegt.
    """

    api_key = forms.CharField(
        label="API-Key",
        required=False,
        widget=PasswordInput(attrs={"class": "form-control", "autocomplete": "off"}),
        help_text="Leer lassen, um einen bereits gespeicherten Key unverändert zu lassen.",
    )

    class Meta:
        model = KIEinstellung
        fields = ("provider", "modell")
        widgets = {
            "provider": forms.Select(attrs={"class": "form-select", "id": "ki-provider"}),
            "modell": forms.TextInput(attrs={"class": "form-control", "list": "ki-modell-vorschlaege"}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        api_key = self.cleaned_data.get("api_key")
        if api_key:
            instance.set_api_key(api_key)
        if commit:
            instance.save()
        return instance


class BootstrapAuthenticationForm(AuthenticationForm):
    """Login-Form mit Bootstrap-Styling (Dark-/Light-Theme)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget = TextInput(
            attrs={"class": "form-control", "autofocus": True, "autocomplete": "username"}
        )
        self.fields["password"].widget = PasswordInput(
            attrs={"class": "form-control", "autocomplete": "current-password"}
        )
