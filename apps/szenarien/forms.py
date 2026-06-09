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
from .models import Cluster, FaktorEingabe, Szenario, Vergleich


class ClusterForm(forms.ModelForm):
    """Anlegen/Bearbeiten eines Szenario-Clusters (organisatorische Gruppe)."""

    class Meta:
        model = Cluster
        fields = ("name", "beschreibung", "szenarien")
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "beschreibung": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "szenarien": forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
        }


class RangeInput(forms.NumberInput):
    """Bootstrap-Range-Slider (<input type="range">)."""

    input_type = "range"


class SzenarioForm(forms.ModelForm):
    class Meta:
        model = Szenario
        fields = ("name", "beschreibung", "n_simulations", "random_seed")
        localized_fields = ("n_simulations", "random_seed")
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "beschreibung": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "n_simulations": forms.TextInput(attrs={"class": "form-control", "inputmode": "numeric"}),
            "random_seed": forms.TextInput(attrs={"class": "form-control", "inputmode": "numeric"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Global vorgegebene Werte: Feld deaktivieren + globalen Wert vorbelegen.
        from apps.admin_bereich.models import AppKonfiguration
        konfig = AppKonfiguration.load()
        if konfig.seed_global:
            self.fields["random_seed"].disabled = True
            self.initial["random_seed"] = konfig.standard_seed
        if konfig.n_simulations_global:
            self.fields["n_simulations"].disabled = True
            self.initial["n_simulations"] = konfig.standard_n_simulations


class VergleichForm(forms.ModelForm):
    """Anlegen/Bearbeiten eines Szenario-Vergleichs (Gruppe bestehender Szenarien)."""

    class Meta:
        model = Vergleich
        fields = ("name", "beschreibung", "szenarien", "referenz_szenario",
                  "n_simulations", "random_seed")
        localized_fields = ("n_simulations", "random_seed")
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "beschreibung": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "szenarien": forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
            "referenz_szenario": forms.Select(attrs={"class": "form-select"}),
            "n_simulations": forms.TextInput(attrs={"class": "form-control", "inputmode": "numeric"}),
            "random_seed": forms.TextInput(attrs={"class": "form-control", "inputmode": "numeric"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Nur rechenbare Szenarien (gültiger Schnitt) zur Auswahl anbieten.
        waehlbar = [s.pk for s in Szenario.objects.all() if s.schnitt_ist_gueltig()]
        qs = Szenario.objects.filter(pk__in=waehlbar)
        self.fields["szenarien"].queryset = qs
        self.fields["referenz_szenario"].queryset = qs
        self.fields["referenz_szenario"].empty_label = "— keine Risikotoleranz zeichnen —"

    def clean_szenarien(self):
        szenarien = self.cleaned_data["szenarien"]
        if szenarien.count() < 2:
            raise forms.ValidationError("Bitte mindestens zwei Szenarien auswählen.")
        return szenarien

    def clean(self):
        cleaned = super().clean()
        ref = cleaned.get("referenz_szenario")
        szenarien = cleaned.get("szenarien")
        if ref and szenarien is not None and ref not in szenarien:
            self.add_error("referenz_szenario",
                           "Das Referenz-Szenario muss zu den ausgewählten Szenarien gehören.")
        return cleaned


# Sprechende Labels je Verteilungs-Parameter, abhängig vom Faktortyp.
_PARAM_LABELS = {
    "frequency": {"low": "min (/Jahr)", "mode": "wahrsch. (/Jahr)",
                  "high": "max (/Jahr)", "mean": "Mittelwert (/Jahr)",
                  "stdev": "Streuung", "constant": "Fester Wert (/Jahr)",
                  "rate": "λ (Ereignisse/Jahr)"},
    "probability": {"low": "min (0–1)", "mode": "wahrsch. (0–1)",
                    "high": "max (0–1)", "mean": "Mittelwert (0–1)",
                    "stdev": "Streuung", "constant": "Fester Wert (0–1)",
                    "beta_mean": "Mittelwert (0–1)"},
    "magnitude": {"low": "min (€)", "mode": "wahrsch. (€)",
                  "high": "max (€)", "mean": "Mittelwert (€)",
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
    "lognormal": [("ln_mean", "mean")],
    # Beta separat (zwei Eingabearten: mean+k oder Konfidenzintervall).
}


class FaktorEingabeForm(forms.ModelForm):
    """ModelForm für genau einen FAIR-Knoten (Faktor steht fest)."""

    low = forms.FloatField(required=False, localize=True, widget=forms.TextInput(attrs={"class": "form-control form-control-sm", "inputmode": "decimal"}))
    mode = forms.FloatField(required=False, localize=True, widget=forms.TextInput(attrs={"class": "form-control form-control-sm", "inputmode": "decimal"}))
    high = forms.FloatField(required=False, localize=True, widget=forms.TextInput(attrs={"class": "form-control form-control-sm", "inputmode": "decimal"}))
    mean = forms.FloatField(required=False, localize=True, widget=forms.TextInput(attrs={"class": "form-control form-control-sm", "inputmode": "decimal"}))
    stdev = forms.FloatField(required=False, localize=True, widget=forms.TextInput(attrs={"class": "form-control form-control-sm", "inputmode": "decimal"}))
    constant = forms.FloatField(required=False, localize=True, widget=forms.TextInput(attrs={"class": "form-control form-control-sm", "inputmode": "decimal"}))
    rate = forms.FloatField(required=False, localize=True, widget=forms.TextInput(attrs={"class": "form-control form-control-sm", "inputmode": "decimal"}))
    beta_mean = forms.FloatField(required=False, localize=True, widget=forms.TextInput(attrs={"class": "form-control form-control-sm", "inputmode": "decimal"}))
    ln_mean = forms.FloatField(required=False, localize=True, widget=forms.TextInput(attrs={"class": "form-control form-control-sm", "inputmode": "decimal"}))
    # Beta-Eingabearten: Mittelwert+k oder Konfidenzintervall (low/high/confidence).
    beta_k = forms.FloatField(required=False, localize=True,
        widget=RangeInput(attrs={"class": "form-range beta-k-slider", "min": 2, "max": 100, "step": 1}))
    beta_low = forms.FloatField(required=False, localize=True, widget=forms.TextInput(attrs={"class": "form-control form-control-sm", "inputmode": "decimal"}))
    beta_high = forms.FloatField(required=False, localize=True, widget=forms.TextInput(attrs={"class": "form-control form-control-sm", "inputmode": "decimal"}))
    beta_confidence = forms.FloatField(required=False,
        widget=RangeInput(attrs={"class": "form-range beta-conf-slider", "min": 50, "max": 90, "step": 10}))
    beta_mode = forms.ChoiceField(required=False,
        choices=[("mean_k", "Mittelwert + k"), ("ci", "Konfidenzintervall")],
        widget=forms.Select(attrs={"class": "form-select form-select-sm beta-mode-select"}))

    class Meta:
        model = FaktorEingabe
        fields = ("verteilung", "unsicherheit", "annahmen", "angreifertyp")
        widgets = {
            "verteilung": forms.Select(attrs={"class": "form-select form-select-sm verteilung-select"}),
            "unsicherheit": RangeInput(attrs={
                "class": "form-range unsicherheit-slider",
                "min": UNSICHERHEIT_MIN, "max": UNSICHERHEIT_MAX, "step": 1,
            }),
            "annahmen": forms.Textarea(attrs={"class": "form-control form-control-sm", "rows": 2,
                                              "placeholder": "Annahmen / Begründung …"}),
            "angreifertyp": forms.HiddenInput(),
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
            # Standard-Verteilung je Faktor vorschlagen (nur bei neuen Eingaben).
            # Bei ModelForms gewinnt self.initial (aus der Instanz) über field.initial.
            if not (self.instance and self.instance.pk):
                self.initial["verteilung"] = fair_tree.standard_verteilung(self.faktor_code)
        # Beta-Eingabearten vorbelegen (Defaults + beim Bearbeiten).
        self.fields["beta_k"].initial = 15
        self.fields["beta_confidence"].initial = 90
        self.initial.setdefault("beta_mode", "mean_k")
        # Bestehende params auf die passenden Einzelfelder legen (Bearbeiten).
        if self.instance and self.instance.pk:
            vorhandene = self.instance.params or {}
            if self.instance.verteilung == "beta":
                if "low" in vorhandene:
                    self.fields["beta_low"].initial = vorhandene.get("low")
                    self.fields["beta_high"].initial = vorhandene.get("high")
                    self.fields["beta_confidence"].initial = round(float(vorhandene.get("confidence", 0.9)) * 100)
                    self.initial["beta_mode"] = "ci"
                else:
                    self.fields["beta_mean"].initial = vorhandene.get("mean")
                    self.fields["beta_k"].initial = vorhandene.get("k", 15)
                    self.initial["beta_mode"] = "mean_k"
            for feld, key in FELD_MAP.get(self.instance.verteilung, []):
                if key in vorhandene:
                    self.fields[feld].initial = vorhandene[key]

    def clean(self):
        cleaned = super().clean()
        verteilung = cleaned.get("verteilung")
        if not verteilung:
            return cleaned
        # Beta: je nach Eingabeart mean+k oder Konfidenzintervall.
        if verteilung == "beta":
            params = {}
            if (cleaned.get("beta_mode") or "mean_k") == "ci":
                if cleaned.get("beta_low") is not None:
                    params["low"] = cleaned["beta_low"]
                if cleaned.get("beta_high") is not None:
                    params["high"] = cleaned["beta_high"]
                conf = cleaned.get("beta_confidence")
                if conf is not None:
                    params["confidence"] = conf / 100.0 if conf > 1 else conf
            else:
                if cleaned.get("beta_mean") is not None:
                    params["mean"] = cleaned["beta_mean"]
                if cleaned.get("beta_k") is not None:
                    params["k"] = cleaned["beta_k"]
            self.instance.params = params
            return cleaned
        # Felder der gewählten Verteilung in pyfair-Param-Keys übersetzen.
        params = {}
        for feld, key in FELD_MAP.get(verteilung, []):
            if cleaned.get(feld) is not None:
                params[key] = cleaned[feld]
        # params VOR der Modell-Validierung setzen (clean prüft Pflichtfelder/PERT/[0,1]).
        self.instance.params = params
        return cleaned
