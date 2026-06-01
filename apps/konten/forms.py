from django.contrib.auth.forms import AuthenticationForm
from django.forms import PasswordInput, TextInput


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
