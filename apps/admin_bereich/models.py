from django.db import models


class AppKonfiguration(models.Model):
    """Globale App-Konfiguration (Singleton, pk=1).

    Erlaubt es, Standard-Seed, Standard-Simulationsanzahl und eine
    Unternehmens-Risikotoleranz zentral vorzugeben. Ist ein Wert „global"
    geschaltet, wird er in der Szenario-Eingabe nur noch lesend angezeigt
    und beim Speichern erzwungen.
    """

    standard_seed = models.PositiveIntegerField("Standard-Seed", default=42)
    seed_global = models.BooleanField(
        "Seed global erzwingen", default=False,
        help_text="Wenn aktiv, gilt der Standard-Seed für alle Szenarien (Eingabe nur lesend).",
    )
    standard_n_simulations = models.PositiveIntegerField(
        "Standard-Anzahl Simulationen", default=10_000
    )
    n_simulations_global = models.BooleanField(
        "Simulationsanzahl global erzwingen", default=False,
        help_text="Wenn aktiv, gilt die Standard-Anzahl für alle Szenarien (Eingabe nur lesend).",
    )
    unternehmens_risikotoleranz = models.JSONField(
        "Unternehmens-Risikotoleranz", null=True, blank=True,
        help_text='Kontextbasiert, z. B. {"type": "constant", "value": 100000}.',
    )
    risikotoleranz_global = models.BooleanField(
        "Risikotoleranz global erzwingen", default=False,
        help_text="Wenn aktiv, gilt die Unternehmens-Risikotoleranz für alle Szenarien (Eingabe nur lesend).",
    )
    geaendert_am = models.DateTimeField("Geändert am", auto_now=True)

    class Meta:
        verbose_name = "App-Konfiguration"
        verbose_name_plural = "App-Konfiguration"

    def __str__(self):
        return "App-Konfiguration"

    def save(self, *args, **kwargs):
        self.pk = 1  # Singleton erzwingen.
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        """Liefert die (einzige) Konfiguration; legt sie bei Bedarf an."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
