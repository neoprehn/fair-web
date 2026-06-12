"""Pro-Nutzer-Konfiguration für den optionalen KI-Assistenten.

Jeder Nutzer kann sein eigenes KI-Modell (Provider + Modellname +
API-Key) hinterlegen. Der API-Key wird verschlüsselt gespeichert
(``krypto``). Ohne hinterlegten Key bleibt die KI-Unterstützung
ausgeblendet bzw. liefert eine entsprechende Fehlermeldung.
"""

from django.contrib.auth.models import User
from django.db import models

from . import krypto


class KIEinstellung(models.Model):
    """Pro-Nutzer-Konfiguration für den optionalen KI-Assistenten."""

    class Provider(models.TextChoices):
        ANTHROPIC = "anthropic", "Anthropic (Claude)"
        OPENAI = "openai", "OpenAI (GPT)"
        GEMINI = "gemini", "Google (Gemini)"

    user = models.OneToOneField(
        User, related_name="ki_einstellung", on_delete=models.CASCADE
    )
    provider = models.CharField(
        "Anbieter", max_length=20, choices=Provider.choices, blank=True
    )
    modell = models.CharField("Modell", max_length=100, blank=True)
    api_key_verschluesselt = models.TextField("API-Key (verschlüsselt)", blank=True)
    geaendert_am = models.DateTimeField("Geändert am", auto_now=True)

    class Meta:
        verbose_name = "KI-Einstellung"
        verbose_name_plural = "KI-Einstellungen"

    def __str__(self):
        return f"KI-Einstellung von {self.user}"

    @property
    def hat_api_key(self):
        return bool(self.api_key_verschluesselt)

    @property
    def api_key(self):
        return krypto.entschluesseln(self.api_key_verschluesselt)

    def set_api_key(self, klartext):
        self.api_key_verschluesselt = krypto.verschluesseln(klartext)

    @property
    def ist_konfiguriert(self):
        return bool(self.provider and self.modell and self.hat_api_key)
