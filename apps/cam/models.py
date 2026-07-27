"""Datenmodell für FAIR-CAM-Szenarien.

Ein ``CamSzenario`` bündelt Metadaten (Name, Simulationsanzahl, Seed) sowie
die Threat-Event-Frequency- und Detection/Response-Zeitgrößen. Es besitzt
genau ein ``CamControl`` (Resistive Control, Frequenz-Seite), genau sechs
``CamStage``-Objekte (Kill-Chain, Loss-Magnitude-Seite) und genau fünf
``CamVerlustklasse``-Objekte (bedingte Verlustverteilungen je Outcome-Klasse).

Jedes Feld spiegelt bewusst 1:1 einen Parameter der pyfair-cam-API
(``ResistiveControl``, ``Stage``, ``DetectionResponseFactor``) – anders als
bei ``apps.szenarien.FaktorEingabe`` ist hier kein generisches
Verteilungs-Params-JSON nötig, weil Typ und Bedeutung jedes Feldes durch die
CAM-API fix vorgegeben sind.
"""

from django.db import models


class CamSzenario(models.Model):
    name = models.CharField("Name", max_length=200)
    beschreibung = models.TextField("Beschreibung", blank=True)
    n_simulations = models.PositiveIntegerField("Anzahl Simulationen", default=20_000)
    random_seed = models.PositiveIntegerField("Zufalls-Seed", default=42)

    # Threat Event Frequency (BetaPert, Frequenz-Seite).
    tef_low = models.FloatField("TEF min (/Jahr)")
    tef_mode = models.FloatField("TEF wahrscheinlich (/Jahr)")
    tef_high = models.FloatField("TEF max (/Jahr)")

    # Reporting-only Zeitgrößen (Detection & Response), fließen laut
    # pyfair-cam nicht in die Risikoberechnung ein.
    t_containment_low = models.FloatField("Containment min (Tage)")
    t_containment_mode = models.FloatField("Containment wahrscheinlich (Tage)")
    t_containment_high = models.FloatField("Containment max (Tage)")
    t_resilience_low = models.FloatField("Resilience min (Tage)")
    t_resilience_mode = models.FloatField("Resilience wahrscheinlich (Tage)")
    t_resilience_high = models.FloatField("Resilience max (Tage)")
    concurrency_low = models.FloatField("Concurrency min")
    concurrency_mode = models.FloatField("Concurrency wahrscheinlich")
    concurrency_high = models.FloatField("Concurrency max")

    erstellt_am = models.DateTimeField("Erstellt am", auto_now_add=True)
    geaendert_am = models.DateTimeField("Geändert am", auto_now=True)

    class Meta:
        verbose_name = "CAM-Szenario"
        verbose_name_plural = "CAM-Szenarien"
        ordering = ["-geaendert_am"]

    def __str__(self):
        return self.name


class CamControl(models.Model):
    """Resistive Control (EDR/Anti-Malware o.ä.), genau eines pro Szenario."""

    szenario = models.OneToOneField(
        CamSzenario, related_name="control", on_delete=models.CASCADE, verbose_name="CAM-Szenario"
    )
    name = models.CharField("Name", max_length=200)

    intended_efficacy_low = models.FloatField("Intended Efficacy min (0–1)")
    intended_efficacy_mode = models.FloatField("Intended Efficacy wahrscheinlich (0–1)")
    intended_efficacy_high = models.FloatField("Intended Efficacy max (0–1)")

    variant_efficacy_low = models.FloatField("Variant Efficacy min (0–1)")
    variant_efficacy_mode = models.FloatField("Variant Efficacy wahrscheinlich (0–1)")
    variant_efficacy_high = models.FloatField("Variant Efficacy max (0–1)")

    variance_frequency_lambda = models.FloatField("Variance Frequency λ (/Jahr, Poisson)")
    variance_frequency_range = models.FloatField("Variance Frequency range (Poisson)")

    variance_duration_low = models.FloatField("Variance Duration min (Tage)")
    variance_duration_mode = models.FloatField("Variance Duration wahrscheinlich (Tage)")
    variance_duration_high = models.FloatField("Variance Duration max (Tage)")

    coverage_low = models.FloatField("Coverage min (0–1)")
    coverage_mode = models.FloatField("Coverage wahrscheinlich (0–1)")
    coverage_high = models.FloatField("Coverage max (0–1)")

    class Meta:
        verbose_name = "CAM-Control"
        verbose_name_plural = "CAM-Controls"

    def __str__(self):
        return self.name


class CamStage(models.Model):
    """Eine Kill-Chain-Stufe (Detection & Response, Loss-Magnitude-Seite)."""

    class OutcomeKlasse(models.TextChoices):
        EARLY = "early", "Früh (early)"
        MID = "mid", "Mittel (mid)"
        LATE = "late", "Spät (late)"

    szenario = models.ForeignKey(
        CamSzenario, related_name="stages", on_delete=models.CASCADE, verbose_name="CAM-Szenario"
    )
    reihenfolge = models.PositiveSmallIntegerField("Reihenfolge")
    name = models.CharField("Name", max_length=200)

    coverage = models.FloatField("Coverage (0–1)")
    visibility = models.FloatField("Visibility (0–1)")
    vis_reliability = models.FloatField("Visibility Reliability (0–1)")
    recognition = models.FloatField("Recognition (0–1)")
    rec_reliability = models.FloatField("Recognition Reliability (0–1)")
    monitoring_cadence = models.FloatField("Monitoring Cadence (Tage)")
    mon_reliability = models.FloatField("Monitoring Reliability (0–1)")
    duration = models.FloatField("Verweildauer (Tage)")
    progression_probability = models.FloatField("Progression Probability (0–1)")
    review_independence = models.FloatField("Review Independence (0–1)")

    outcome_class = models.CharField(
        "Outcome-Klasse bei Entdeckung", max_length=10, choices=OutcomeKlasse.choices
    )

    class Meta:
        verbose_name = "CAM-Stufe"
        verbose_name_plural = "CAM-Stufen (Kill-Chain)"
        ordering = ["reihenfolge"]
        constraints = [
            models.UniqueConstraint(
                fields=["szenario", "reihenfolge"], name="unique_stufe_pro_szenario"
            )
        ]

    def __str__(self):
        return f"{self.reihenfolge}. {self.name}"


class CamVerlustklasse(models.Model):
    """Bedingte Verlustverteilung (BetaPert) für eine Outcome-Klasse."""

    class Klasse(models.TextChoices):
        EARLY = "early", "Früh (early)"
        MID = "mid", "Mittel (mid)"
        LATE = "late", "Spät (late)"
        FULL_IMPACT = "full_impact", "Voller Schaden (full_impact)"
        ATTACKER_FAILS = "attacker_fails", "Angreifer scheitert (attacker_fails)"

    szenario = models.ForeignKey(
        CamSzenario, related_name="verlustklassen", on_delete=models.CASCADE, verbose_name="CAM-Szenario"
    )
    klasse = models.CharField("Klasse", max_length=20, choices=Klasse.choices)
    low = models.FloatField("Verlust min (€)")
    mode = models.FloatField("Verlust wahrscheinlich (€)")
    high = models.FloatField("Verlust max (€)")

    class Meta:
        verbose_name = "CAM-Verlustklasse"
        verbose_name_plural = "CAM-Verlustklassen"
        constraints = [
            models.UniqueConstraint(
                fields=["szenario", "klasse"], name="unique_klasse_pro_szenario"
            )
        ]

    def __str__(self):
        return f"{self.get_klasse_display()}"
