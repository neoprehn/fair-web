from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.forms import PasswordInput, TextInput


class RegistrierForm(UserCreationForm):
    """Selbstregistrierung (Benutzername + Passwort), Bootstrap-Styling."""

    class Meta(UserCreationForm.Meta):
        fields = ("username",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for feld in self.fields.values():
            feld.widget.attrs["class"] = "form-control"


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
