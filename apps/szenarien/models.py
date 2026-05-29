"""Datenmodell für FAIR-Szenarien.

Ein ``Szenario`` bündelt die Metadaten einer Monte-Carlo-Simulation
(Name, Simulationsanzahl, Seed) und besitzt pro FAIR-Risikofaktor eine
``FaktorEingabe`` mit frei wählbarer Verteilung. Aus den Eingaben lässt
sich direkt ein pyfair-``FairModel`` füttern (Phase 4).
"""

from django.core.exceptions import ValidationError
from django.db import models


class Szenario(models.Model):
    name = models.CharField("Name", max_length=200)
    beschreibung = models.TextField("Beschreibung", blank=True)
    n_simulations = models.PositiveIntegerField("Anzahl Simulationen", default=10_000)
    random_seed = models.PositiveIntegerField("Zufalls-Seed", default=42)
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


class FaktorEingabe(models.Model):
    """Eine Verteilungs-Eingabe für genau einen FAIR-Faktor eines Szenarios."""

    class Faktor(models.TextChoices):
        LEF = "LEF", "Schadenshäufigkeit (Loss Event Frequency)"
        LM = "LM", "Schadenshöhe (Loss Magnitude)"

    class Verteilung(models.TextChoices):
        PERT = "pert", "PERT (min / wahrscheinlich / max)"
        NORMAL = "normal", "Normalverteilung (Mittelwert / Streuung)"
        CONSTANT = "constant", "Konstant (fester Wert)"

    # Mapping unserer Kurzfaktoren auf die pyfair-Knotennamen.
    FAIR_TARGETS = {
        Faktor.LEF: "Loss Event Frequency",
        Faktor.LM: "Loss Magnitude",
    }

    # Pflicht-Parameter je Verteilung (entspricht den pyfair-Generatoren).
    REQUIRED_PARAMS = {
        Verteilung.PERT: ("low", "mode", "high"),
        Verteilung.NORMAL: ("mean", "stdev"),
        Verteilung.CONSTANT: ("constant",),
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
        return self.FAIR_TARGETS[self.faktor]

    def to_fair_kwargs(self):
        """kwargs für die strukturierte pyfair-API ``input_data``."""
        return {"distribution": self.verteilung, "params": dict(self.params)}

    def clean(self):
        """Prüft, dass ``params`` zur gewählten Verteilung passt."""
        params = self.params or {}
        required = self.REQUIRED_PARAMS.get(self.verteilung, ())
        fehlend = [key for key in required if key not in params]
        if fehlend:
            raise ValidationError(
                {"params": f"Verteilung „{self.verteilung}“ benötigt: {', '.join(fehlend)}."}
            )

        if self.verteilung == self.Verteilung.PERT:
            low, mode, high = params["low"], params["mode"], params["high"]
            if not (low <= mode <= high):
                raise ValidationError(
                    {"params": "PERT erfordert die Reihenfolge low ≤ mode ≤ high."}
                )
