"""Formulare für CAM-Szenarien.

Die Struktur ist analog zu ``apps.szenarien.forms``: ein Hauptformular
(``CamSzenarioForm``) plus je ein Formular pro Kind-Objekt
(``CamControlForm``, ``CamStageForm``, ``CamVerlustklasseForm``). Anders als
bei ``FaktorEingabeForm`` gibt es hier keine Verteilungsauswahl – jedes Feld
ist durch die pyfair-cam-API fix vorgegeben, daher reichen einfache
ModelForms.
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


class CamVerlustklasseForm(forms.ModelForm):
    class Meta:
        model = CamVerlustklasse
        fields = ("klasse", "low", "mode", "high")
        widgets = {
            "klasse": forms.HiddenInput(),
            **_zahlenfelder("low", "mode", "high"),
        }
