"""Formulare für Szenarien und ihre FAIR-Faktor-Eingaben.

Pro FAIR-Knoten gibt es ein ``FaktorEingabeForm`` (Prefix = Knoten-Code).
Der Faktor steht fest (durch den Knoten), die Verteilungs-Auswahl ist je
Faktortyp eingeschränkt, und die Zahlenfelder werden zum ``params``-Dict
zusammengesetzt. Welche Knoten tatsächlich gespeichert werden, entscheidet
der „Schnitt" durch den Baum (siehe View + ``fair_tree``).
"""

from django import forms

from . import fair_tree
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


# Sprechende Labels je Verteilungs-Parameter, abhängig vom Faktortyp.
_PARAM_LABELS = {
    "frequency": {"low": "Minimum (pro Jahr)", "mode": "Wahrscheinlich (pro Jahr)",
                  "high": "Maximum (pro Jahr)", "mean": "Mittelwert (pro Jahr)",
                  "stdev": "Streuung", "constant": "Fester Wert (pro Jahr)",
                  "rate": "λ (Ereignisse pro Jahr)"},
    "probability": {"low": "Minimum (0–1)", "mode": "Wahrscheinlich (0–1)",
                    "high": "Maximum (0–1)", "mean": "Mittelwert (0–1)",
                    "stdev": "Streuung", "constant": "Fester Wert (0–1)",
                    "beta_mean": "Mittelwert (0–1)"},
    "magnitude": {"low": "Minimum (€)", "mode": "Wahrscheinlich (€)",
                  "high": "Maximum (€)", "mean": "Mittelwert (€)",
                  "stdev": "Streuung (€)", "constant": "Fester Wert (€)",
                  "ln_mean": "Mittelwert (€)"},
}

# Verteilung -> [(Formularfeld, pyfair-Param-Key)]. Formparameter (gamma/sigma/
# k/range) kommen nicht von hier, sondern aus der Konfidenz (Unsicherheits-Slider).
FELD_MAP = {
    "pert": [("low", "low"), ("mode", "mode"), ("high", "high")],
    "normal": [("mean", "mean"), ("stdev", "stdev")],
    "constant": [("constant", "constant")],
    "poisson": [("rate", "lambda")],
    "beta": [("beta_mean", "mean")],
    "lognormal": [("ln_mean", "mean")],
}


class FaktorEingabeForm(forms.ModelForm):
    """ModelForm für genau einen FAIR-Knoten (Faktor steht fest)."""

    low = forms.FloatField(required=False, widget=forms.NumberInput(attrs={"class": "form-control"}))
    mode = forms.FloatField(required=False, widget=forms.NumberInput(attrs={"class": "form-control"}))
    high = forms.FloatField(required=False, widget=forms.NumberInput(attrs={"class": "form-control"}))
    mean = forms.FloatField(required=False, widget=forms.NumberInput(attrs={"class": "form-control"}))
    stdev = forms.FloatField(required=False, widget=forms.NumberInput(attrs={"class": "form-control"}))
    constant = forms.FloatField(required=False, widget=forms.NumberInput(attrs={"class": "form-control"}))
    rate = forms.FloatField(required=False, widget=forms.NumberInput(attrs={"class": "form-control"}))
    beta_mean = forms.FloatField(required=False, widget=forms.NumberInput(attrs={"class": "form-control"}))
    ln_mean = forms.FloatField(required=False, widget=forms.NumberInput(attrs={"class": "form-control"}))

    class Meta:
        model = FaktorEingabe
        fields = ("verteilung", "unsicherheit")
        widgets = {
            "verteilung": forms.Select(attrs={"class": "form-select form-select-sm verteilung-select"}),
            "unsicherheit": RangeInput(attrs={
                "class": "form-range unsicherheit-slider",
                "min": UNSICHERHEIT_MIN, "max": UNSICHERHEIT_MAX, "step": 1,
            }),
        }

    def __init__(self, *args, faktor_code=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Faktor steht durch den Knoten fest.
        self.faktor_code = faktor_code or (self.instance.faktor if self.instance else None)
        if self.faktor_code:
            self.instance.faktor = self.faktor_code
            typ = fair_tree.typ(self.faktor_code)
            # Verteilungen je Faktortyp einschränken.
            erlaubt = set(fair_tree.erlaubte_verteilungen(self.faktor_code))
            self.fields["verteilung"].choices = [
                (w, label) for w, label in FaktorEingabe.Verteilung.choices if w in erlaubt
            ]
            # Param-Labels typgerecht setzen.
            for key, label in _PARAM_LABELS[typ].items():
                self.fields[key].label = label
        # Bestehende params auf die passenden Einzelfelder legen (Bearbeiten).
        if self.instance and self.instance.pk:
            vorhandene = self.instance.params or {}
            for feld, key in FELD_MAP.get(self.instance.verteilung, []):
                if key in vorhandene:
                    self.fields[feld].initial = vorhandene[key]

    def clean(self):
        cleaned = super().clean()
        verteilung = cleaned.get("verteilung")
        if not verteilung:
            return cleaned
        # Felder der gewählten Verteilung in pyfair-Param-Keys übersetzen.
        params = {}
        for feld, key in FELD_MAP.get(verteilung, []):
            if cleaned.get(feld) is not None:
                params[key] = cleaned[feld]
        # params VOR der Modell-Validierung setzen (clean prüft Pflichtfelder/PERT/[0,1]).
        self.instance.params = params
        return cleaned
