"""Formulare für CAM-Szenarien.

Die Struktur ist analog zu ``apps.szenarien.forms``: ein Hauptformular
(``CamSzenarioForm``) plus je ein Formular pro Kind-Objekt
(``CamControlForm``, ``CamStageForm``, ``CamVerlustklasseForm``). Anders als
bei ``FaktorEingabeForm`` gibt es für die meisten Felder keine
Verteilungsauswahl – jedes Feld ist durch die pyfair-cam-API fix vorgegeben,
daher reichen dort einfache ModelForms. ``CamVerlustklasseForm`` ist die
Ausnahme (siehe ``models.py``-Docstring) und folgt deshalb demselben
Verteilungs-Params-Muster wie ``FaktorEingabeForm``/
``_VerlustEingabeFormBasis`` in ``apps.szenarien.forms`` – bewusst eigenständig
nachgebaut statt von dort importiert, damit ``apps.cam`` unabhängig bleibt.
"""

from django import forms

from .models import CamControl, CamSzenario, CamStage, CamVerlustklasse

_ZAHL = forms.TextInput(attrs={"class": "form-control form-control-sm", "inputmode": "decimal"})
_TEXT = forms.TextInput(attrs={"class": "form-control"})


def _zahlenfelder(*namen):
    return {name: _ZAHL for name in namen}


class CamSzenarioForm(forms.ModelForm):
    class Meta:
        model = CamSzenario
        fields = (
            "name", "beschreibung", "n_simulations", "random_seed",
            "tef_low", "tef_mode", "tef_high",
            "t_containment_low", "t_containment_mode", "t_containment_high",
            "t_resilience_low", "t_resilience_mode", "t_resilience_high",
            "concurrency_low", "concurrency_mode", "concurrency_high",
        )
        # Nur die Integer-Felder lokalisieren (analog SzenarioForm: Tausenderpunkt
        # bei n_simulations). Die Float-Felder bleiben unlokalisiert – sonst würde
        # das deutsche Tausenderpunkt-Format ("." als Gruppierung) z.B. "0.042" als
        # "42" fehlinterpretieren, weil hier (anders als bei FaktorEingabeForm) kein
        # locale-aware Komma-Eingabefeld existiert.
        localized_fields = ("n_simulations", "random_seed")
        widgets = {
            "name": _TEXT,
            "beschreibung": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "n_simulations": forms.TextInput(attrs={"class": "form-control", "inputmode": "numeric"}),
            "random_seed": forms.TextInput(attrs={"class": "form-control", "inputmode": "numeric"}),
            **_zahlenfelder(
                "tef_low", "tef_mode", "tef_high",
                "t_containment_low", "t_containment_mode", "t_containment_high",
                "t_resilience_low", "t_resilience_mode", "t_resilience_high",
                "concurrency_low", "concurrency_mode", "concurrency_high",
            ),
        }


class CamControlForm(forms.ModelForm):
    class Meta:
        model = CamControl
        fields = (
            "name",
            "intended_efficacy_low", "intended_efficacy_mode", "intended_efficacy_high",
            "variant_efficacy_low", "variant_efficacy_mode", "variant_efficacy_high",
            "variance_frequency_lambda", "variance_frequency_range",
            "variance_duration_low", "variance_duration_mode", "variance_duration_high",
            "coverage_low", "coverage_mode", "coverage_high",
        )
        widgets = {
            "name": _TEXT,
            **_zahlenfelder(
                "intended_efficacy_low", "intended_efficacy_mode", "intended_efficacy_high",
                "variant_efficacy_low", "variant_efficacy_mode", "variant_efficacy_high",
                "variance_frequency_lambda", "variance_frequency_range",
                "variance_duration_low", "variance_duration_mode", "variance_duration_high",
                "coverage_low", "coverage_mode", "coverage_high",
            ),
        }


class CamStageForm(forms.ModelForm):
    class Meta:
        model = CamStage
        fields = (
            "reihenfolge", "name",
            "coverage", "visibility", "vis_reliability",
            "recognition", "rec_reliability",
            "monitoring_cadence", "mon_reliability", "duration",
            "progression_probability", "review_independence",
            "outcome_class",
        )
        widgets = {
            "reihenfolge": forms.HiddenInput(),
            "name": _TEXT,
            "outcome_class": forms.Select(attrs={"class": "form-select form-select-sm"}),
            **_zahlenfelder(
                "coverage", "visibility", "vis_reliability",
                "recognition", "rec_reliability",
                "monitoring_cadence", "mon_reliability", "duration",
                "progression_probability", "review_independence",
            ),
        }


# Verlustklasse -> [(Formularfeld, pyfair_cam-Konstruktor-Key)]. Lognormal und
# Normal teilen sich dieselben Felder (mean/stdev) - nur die Beschriftung im
# Template unterscheidet sie (siehe cam/form.html, data-dist="mean-stdev").
_VERLUST_FELD_MAP = {
    "pert": [("low", "low"), ("mode", "mode"), ("high", "high")],
    "lognormal": [("mean", "mean"), ("stdev", "stdev")],
    "normal": [("mean", "mean"), ("stdev", "stdev")],
    "constant": [("constant", "constant")],
}

_VERLUST_PARAM_LABELS = {
    "low": "min (€)", "mode": "wahrsch. (€)", "high": "max (€)",
    "mean": "Mittelwert (€)", "stdev": "Streuung (€)", "constant": "Fester Wert (€)",
}


class CamVerlustklasseForm(forms.ModelForm):
    """Verlustverteilung je Outcome-Klasse - Verteilung+Parameter+Annahmen,
    analog zu ``FaktorEingabeForm`` (magnitude-Verteilungen), siehe
    ``_VERLUST_FELD_MAP``. ``klasse`` steht durch die Karte fest (wird von der
    View gesetzt, nicht vom Formular - analog ``faktor`` bei ``FaktorEingabeForm``)."""

    low = forms.FloatField(required=False, localize=True, widget=_ZAHL)
    mode = forms.FloatField(required=False, localize=True, widget=_ZAHL)
    high = forms.FloatField(required=False, localize=True, widget=_ZAHL)
    mean = forms.FloatField(required=False, localize=True, widget=_ZAHL)
    stdev = forms.FloatField(required=False, localize=True, widget=_ZAHL)
    constant = forms.FloatField(required=False, localize=True, widget=_ZAHL)

    class Meta:
        model = CamVerlustklasse
        fields = ("klasse", "verteilung", "annahmen")
        widgets = {
            "klasse": forms.HiddenInput(),
            "verteilung": forms.Select(attrs={"class": "form-select form-select-sm verteilung-select"}),
            "annahmen": forms.Textarea(attrs={"class": "form-control form-control-sm", "rows": 2,
                                              "placeholder": "Annahmen / Begründung …"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for key, label in _VERLUST_PARAM_LABELS.items():
            self.fields[key].label = label
        # Bestehende params auf die passenden Einzelfelder legen (Bearbeiten).
        if self.instance and self.instance.pk:
            vorhandene = self.instance.params or {}
            for feld, key in _VERLUST_FELD_MAP.get(self.instance.verteilung, []):
                if key in vorhandene:
                    self.fields[feld].initial = vorhandene[key]

    def clean(self):
        cleaned = super().clean()
        verteilung = cleaned.get("verteilung")
        if not verteilung:
            return cleaned
        params = {}
        for feld, key in _VERLUST_FELD_MAP.get(verteilung, []):
            if cleaned.get(feld) is not None:
                params[key] = cleaned[feld]
        # params VOR der Modell-Validierung setzen (clean() prüft Pflichtfelder/PERT-Reihenfolge).
        self.instance.params = params
        return cleaned
