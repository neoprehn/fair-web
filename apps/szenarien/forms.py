"""Formulare für Szenarien und ihre FAIR-Faktor-Eingaben.

Die Verteilungs-Parameter werden dem Nutzer als einzelne Zahlenfelder
(Slider/Number) angeboten statt als rohes JSON. Beim Speichern setzt das
Formular daraus das ``params``-Dict passend zur gewählten Verteilung
zusammen und nutzt die Modell-Validierung (``FaktorEingabe.clean``).
"""

from django import forms
from django.forms import inlineformset_factory

from .fair_confidence import UNSICHERHEIT_MAX, UNSICHERHEIT_MIN
from .models import FaktorEingabe, Szenario


class RangeInput(forms.NumberInput):
    """Bootstrap-Range-Slider (<input type="range">)."""

    input_type = "range"


class SzenarioForm(forms.ModelForm):
    class Meta:
        model = Szenario
        fields = ("name", "beschreibung", "n_simulations", "random_seed")
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "beschreibung": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "n_simulations": forms.NumberInput(attrs={"class": "form-control"}),
            "random_seed": forms.NumberInput(attrs={"class": "form-control"}),
        }


class FaktorEingabeForm(forms.ModelForm):
    """ModelForm mit Einzelfeldern für die Verteilungs-Parameter."""

    low = forms.FloatField(required=False, label="Minimum",
                           widget=forms.NumberInput(attrs={"class": "form-control"}))
    mode = forms.FloatField(required=False, label="Wahrscheinlichster Wert",
                            widget=forms.NumberInput(attrs={"class": "form-control"}))
    high = forms.FloatField(required=False, label="Maximum",
                            widget=forms.NumberInput(attrs={"class": "form-control"}))
    mean = forms.FloatField(required=False, label="Mittelwert",
                            widget=forms.NumberInput(attrs={"class": "form-control"}))
    stdev = forms.FloatField(required=False, label="Streuung (Std.-Abw.)",
                             widget=forms.NumberInput(attrs={"class": "form-control"}))
    constant = forms.FloatField(required=False, label="Fester Wert",
                                widget=forms.NumberInput(attrs={"class": "form-control"}))

    # Alle Felder, die in params landen können.
    PARAM_FIELDS = ("low", "mode", "high", "mean", "stdev", "constant")

    class Meta:
        model = FaktorEingabe
        fields = ("faktor", "verteilung", "unsicherheit")
        widgets = {
            "faktor": forms.Select(attrs={"class": "form-select"}),
            "verteilung": forms.Select(attrs={"class": "form-select verteilung-select"}),
            "unsicherheit": RangeInput(attrs={
                "class": "form-range unsicherheit-slider",
                "min": UNSICHERHEIT_MIN,
                "max": UNSICHERHEIT_MAX,
                "step": 1,
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Leere Auswahl ("---------") entfernen – die Karten sind fest auf
        # LEF bzw. LM vorbelegt (Initial kommt aus der View).
        self.fields["faktor"].choices = FaktorEingabe.Faktor.choices
        # Beim Bearbeiten die gespeicherten params auf die Einzelfelder legen.
        if self.instance and self.instance.pk:
            for key, value in (self.instance.params or {}).items():
                if key in self.fields:
                    self.fields[key].initial = value

    def clean(self):
        cleaned = super().clean()
        verteilung = cleaned.get("verteilung")
        if not verteilung:
            return cleaned

        # Nur die für diese Verteilung relevanten Felder in params übernehmen.
        required = FaktorEingabe.REQUIRED_PARAMS.get(verteilung, ())
        params = {key: cleaned[key] for key in required if cleaned.get(key) is not None}

        # params am Instance setzen, BEVOR die Modell-Validierung (clean) im
        # ModelForm-_post_clean läuft – sie prüft Pflichtfelder + PERT-Reihenfolge.
        self.instance.params = params
        return cleaned


# Genau zwei Faktoren pro Szenario (LEF + LM).
FaktorFormSet = inlineformset_factory(
    Szenario,
    FaktorEingabe,
    form=FaktorEingabeForm,
    extra=2,
    max_num=2,
    validate_max=True,
    can_delete=False,
)
