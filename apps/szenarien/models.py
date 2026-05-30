"""Datenmodell für FAIR-Szenarien.

Ein ``Szenario`` bündelt die Metadaten einer Monte-Carlo-Simulation
(Name, Simulationsanzahl, Seed) und besitzt pro FAIR-Risikofaktor eine
``FaktorEingabe`` mit frei wählbarer Verteilung. Aus den Eingaben lässt
sich direkt ein pyfair-``FairModel`` füttern (Phase 4).
"""

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from . import fair_tree
from .fair_confidence import (
    CONFIDENCE_DEFAULTS,
    CONFIDENCE_DISTRIBUTIONS,
    UNSICHERHEIT_DEFAULT,
    UNSICHERHEIT_MAX,
    UNSICHERHEIT_MIN,
    UNSICHERHEIT_TO_CONFIDENCE,
    UNSICHERHEIT_LABELS,
)


class Angreifertyp(models.Model):
    """Vordefiniertes Threat-Capability-Profil (PERT für Threat Capability).

    Dient als Auswahl-Vorlage im Formular (füllt die TC-Werte vor). Im
    späteren Admin-Bereich editierbar (wie auch die Konfidenz-Vorgaben).
    """

    name = models.CharField("Bezeichnung", max_length=120, unique=True)
    beschreibung = models.CharField("Beschreibung", max_length=200, blank=True)
    low = models.FloatField("Minimum (0–1)")
    mode = models.FloatField("Wahrscheinlich (0–1)")
    high = models.FloatField("Maximum (0–1)")
    begruendung = models.CharField("Begründung", max_length=200, blank=True)
    typisches_szenario = models.CharField("Typisches Szenario", max_length=200, blank=True)
    reihenfolge = models.PositiveSmallIntegerField("Reihenfolge", default=0)

    class Meta:
        verbose_name = "Angreifertyp"
        verbose_name_plural = "Angreifertypen"
        ordering = ["reihenfolge", "name"]

    def __str__(self):
        return self.name


class Szenario(models.Model):
    name = models.CharField("Name", max_length=200)
    beschreibung = models.TextField("Beschreibung", blank=True)
    n_simulations = models.PositiveIntegerField("Anzahl Simulationen", default=10_000)
    random_seed = models.PositiveIntegerField("Zufalls-Seed", default=42)
    # Risikotoleranz, kontextbasiert: {"type": "constant"|"curve"|"distribution", ...}
    risikotoleranz = models.JSONField("Risikotoleranz", null=True, blank=True)
    erstellt_am = models.DateTimeField("Erstellt am", auto_now_add=True)
    geaendert_am = models.DateTimeField("Geändert am", auto_now=True)

    class Meta:
        verbose_name = "Szenario"
        verbose_name_plural = "Szenarien"
        ordering = ["-geaendert_am"]

    def __str__(self):
        return self.name

    def fair_inputs(self):
        """Eingaben als Dict ``{FAIR-Target: input_data-kwargs}``.

        Direkt an ``FairModel.input_data(target, **kwargs)`` übergebbar.
        """
        return {
            faktor.fair_target: faktor.to_fair_kwargs()
            for faktor in self.faktoren.all()
        }

    def schnitt_codes(self):
        """Die angegebenen Faktor-Codes (der Schnitt durch den FAIR-Baum)."""
        return list(self.faktoren.values_list("faktor", flat=True))

    def schnitt_ist_gueltig(self):
        """True, wenn die Faktoren einen rechenbaren Schnitt bilden (Risk abgedeckt)."""
        return fair_tree.schnitt_ist_gueltig(self.schnitt_codes())


class FaktorEingabe(models.Model):
    """Eine Verteilungs-Eingabe für genau einen FAIR-Faktor eines Szenarios."""

    class Faktor(models.TextChoices):
        LEF = "LEF", "Loss Event Frequency (LEF)"
        TEF = "TEF", "Threat Event Frequency (TEF)"
        CF = "CF", "Contact Frequency (CF)"
        POA = "POA", "Probability of Action (PoA)"
        VULN = "VULN", "Vulnerability (Vuln)"
        TC = "TC", "Threat Capability (TC)"
        CS = "CS", "Control Strength (CS)"
        LM = "LM", "Loss Magnitude (LM)"
        PL = "PL", "Primary Loss (PL)"
        SL = "SL", "Secondary Loss (SL)"
        SLEF = "SLEF", "Secondary Loss Event Frequency (SLEF)"
        SLEM = "SLEM", "Secondary Loss Event Magnitude (SLEM)"

    class Verteilung(models.TextChoices):
        PERT = "pert", "PERT (min / wahrscheinlich / max)"
        NORMAL = "normal", "Normalverteilung (Mittelwert / Streuung)"
        CONSTANT = "constant", "Konstant (fester Wert)"
        POISSON = "poisson", "Poisson (λ Ereignisse pro Jahr)"
        BETA = "beta", "Beta (Mittelwert 0–1)"
        LOGNORMAL = "lognormal", "Lognormal (Mittelwert)"

    # Pflicht-Parameter je Verteilung (pyfair-Keys; Formparameter wie gamma/
    # sigma/k/range liefert der Unsicherheits-Slider via confidence).
    REQUIRED_PARAMS = {
        Verteilung.PERT: ("low", "mode", "high"),
        Verteilung.NORMAL: ("mean", "stdev"),
        Verteilung.CONSTANT: ("constant",),
        Verteilung.POISSON: ("lambda",),
        Verteilung.BETA: ("mean",),
        Verteilung.LOGNORMAL: ("mean",),
    }

    szenario = models.ForeignKey(
        Szenario,
        related_name="faktoren",
        on_delete=models.CASCADE,
        verbose_name="Szenario",
    )
    faktor = models.CharField("Faktor", max_length=10, choices=Faktor.choices)
    verteilung = models.CharField(
        "Verteilung",
        max_length=20,
        choices=Verteilung.choices,
        default=Verteilung.PERT,
    )
    params = models.JSONField("Parameter", default=dict)
    # Unsicherheit als 5-Stufen-Slider (0 = niedrigste ... 4 = höchste).
    # Wird invertiert auf pyfair-"confidence" abgebildet (siehe fair_confidence).
    unsicherheit = models.PositiveSmallIntegerField(
        "Unsicherheit",
        default=UNSICHERHEIT_DEFAULT,
        validators=[MinValueValidator(UNSICHERHEIT_MIN), MaxValueValidator(UNSICHERHEIT_MAX)],
    )

    class Meta:
        verbose_name = "Faktor-Eingabe"
        verbose_name_plural = "Faktor-Eingaben"
        constraints = [
            models.UniqueConstraint(
                fields=["szenario", "faktor"],
                name="unique_faktor_pro_szenario",
            )
        ]

    def __str__(self):
        return f"{self.get_faktor_display()} – {self.get_verteilung_display()}"

    @property
    def fair_target(self):
        """Der pyfair-Knotenname für diesen Faktor (z. B. 'Loss Magnitude')."""
        return fair_tree.target(self.faktor)

    @property
    def faktor_abbr(self):
        return fair_tree.abbr(self.faktor)

    @property
    def confidence_level(self):
        """pyfair-Konfidenzstufe (invertiert zur Unsicherheit)."""
        return UNSICHERHEIT_TO_CONFIDENCE[self.unsicherheit]

    @property
    def unsicherheit_label(self):
        """Lesbares Label der Unsicherheitsstufe (z. B. 'mittel')."""
        return UNSICHERHEIT_LABELS[self.unsicherheit]

    @property
    def confidence_shape(self):
        """Aufgelöster pyfair-Formparameter (z. B. {'gamma': 4}) oder None."""
        if self.verteilung not in CONFIDENCE_DISTRIBUTIONS:
            return None
        return CONFIDENCE_DEFAULTS[self.confidence_level].get(self.verteilung)

    def to_fair_kwargs(self):
        """kwargs für die strukturierte pyfair-API ``input_data``.

        Für Verteilungen mit Konfidenz-Formparameter (PERT/Lognormal/
        Poisson/Beta) wird ``confidence`` mitgegeben – pyfair leitet daraus
        gamma/sigma/k/range ab. Konstant/Normal kennen keine Konfidenz.
        """
        kwargs = {"distribution": self.verteilung, "params": dict(self.params)}
        if self.verteilung in CONFIDENCE_DISTRIBUTIONS:
            kwargs["confidence"] = self.confidence_level
        return kwargs

    def clean(self):
        """Prüft, dass ``params`` zur gewählten Verteilung passt."""
        params = self.params or {}
        required = self.REQUIRED_PARAMS.get(self.verteilung, ())
        fehlend = [key for key in required if key not in params]
        if fehlend:
            raise ValidationError(
                f"Verteilung „{self.verteilung}“ benötigt: {', '.join(fehlend)}."
            )

        if self.verteilung == self.Verteilung.PERT:
            low, mode, high = params["low"], params["mode"], params["high"]
            if not (low <= mode <= high):
                raise ValidationError(
                    "PERT erfordert die Reihenfolge low ≤ mode ≤ high."
                )

        # Wahrscheinlichkeits-Faktoren müssen in [0, 1] liegen.
        if self.faktor and fair_tree.ist_gebunden(self.faktor):
            for key, value in params.items():
                if isinstance(value, (int, float)) and not (0.0 <= value <= 1.0):
                    raise ValidationError(
                        f"„{fair_tree.abbr(self.faktor)}“ ist eine Wahrscheinlichkeit – "
                        f"Werte müssen zwischen 0 und 1 liegen (war {key}={value})."
                    )
