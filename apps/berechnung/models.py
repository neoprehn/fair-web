"""Datenmodell für Monte-Carlo-Simulationsläufe.

Ein ``Simulationslauf`` gehört zu einem Szenario und hält Status,
Fortschritt (0–100) und das berechnete Ergebnis (als JSON). Die
eigentliche Berechnung läuft asynchron in einem Hintergrund-Thread
(siehe ``services.py``) und schreibt den Fortschritt fortlaufend hierher.
"""

from django.db import models


class Simulationslauf(models.Model):
    class Status(models.TextChoices):
        ANGELEGT = "angelegt", "Angelegt"
        LAEUFT = "laeuft", "Läuft"
        FERTIG = "fertig", "Fertig"
        FEHLER = "fehler", "Fehler"

    szenario = models.ForeignKey(
        "szenarien.Szenario",
        related_name="laeufe",
        on_delete=models.CASCADE,
        verbose_name="Szenario",
    )
    status = models.CharField(
        "Status", max_length=20, choices=Status.choices, default=Status.ANGELEGT
    )
    fortschritt = models.PositiveSmallIntegerField("Fortschritt (%)", default=0)
    n_simulations = models.PositiveIntegerField("Anzahl Simulationen")
    random_seed = models.PositiveIntegerField("Zufalls-Seed")
    ergebnis = models.JSONField("Ergebnis", null=True, blank=True)
    fehler_text = models.TextField("Fehlertext", blank=True)
    erstellt_am = models.DateTimeField("Erstellt am", auto_now_add=True)
    aktualisiert_am = models.DateTimeField("Aktualisiert am", auto_now=True)

    class Meta:
        verbose_name = "Simulationslauf"
        verbose_name_plural = "Simulationsläufe"
        ordering = ["-erstellt_am"]

    def __str__(self):
        return f"Lauf {self.pk} – {self.szenario.name} ({self.get_status_display()})"

    @property
    def ist_fertig(self):
        return self.status == self.Status.FERTIG


class MetaLauf(models.Model):
    """Ein gemeinsamer Lauf über mehrere Szenarien (Gesamtrisiko = Summe).

    Nutzt pyfairs ``FairMetaModel`` (mode='sum'). Das Ergebnis-JSON enthält
    das Gesamtrisiko (``gesamt``) und die Einzelergebnisse je Szenario
    (``szenarien``).
    """

    szenarien = models.ManyToManyField(
        "szenarien.Szenario", related_name="meta_laeufe", verbose_name="Szenarien"
    )
    status = models.CharField(
        "Status",
        max_length=20,
        choices=Simulationslauf.Status.choices,
        default=Simulationslauf.Status.ANGELEGT,
    )
    fortschritt = models.PositiveSmallIntegerField("Fortschritt (%)", default=0)
    n_simulations = models.PositiveIntegerField("Anzahl Simulationen")
    random_seed = models.PositiveIntegerField("Zufalls-Seed")
    ergebnis = models.JSONField("Ergebnis", null=True, blank=True)
    fehler_text = models.TextField("Fehlertext", blank=True)
    erstellt_am = models.DateTimeField("Erstellt am", auto_now_add=True)
    aktualisiert_am = models.DateTimeField("Aktualisiert am", auto_now=True)

    class Meta:
        verbose_name = "Meta-Lauf"
        verbose_name_plural = "Meta-Läufe"
        ordering = ["-erstellt_am"]

    def __str__(self):
        return f"Meta-Lauf {self.pk} ({self.get_status_display()})"

    @property
    def ist_fertig(self):
        return self.status == Simulationslauf.Status.FERTIG
