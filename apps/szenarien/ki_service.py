"""Aufruf des pro Nutzer konfigurierten KI-Modells via ``litellm``.

Jeder Nutzer hinterlegt in seinen Konto-Einstellungen
(``apps.konten.models.KIEinstellung``) Anbieter, Modellname und
API-Key. ``litellm`` vereint Anthropic/OpenAI/Gemini hinter einer
gemeinsamen ``completion``-Schnittstelle – der Provider-Präfix vor dem
Modellnamen (z. B. ``"anthropic/claude-sonnet-4-6"``) steuert dabei das
Routing.
"""

import litellm


class KIFehler(Exception):
    """Nutzerfreundlicher Fehler beim Aufruf des KI-Modells."""


def ist_verfuegbar(user):
    """True, wenn der Nutzer ein vollständig konfiguriertes KI-Modell hat."""
    einstellung = getattr(user, "ki_einstellung", None)
    return bool(einstellung and einstellung.ist_konfiguriert)


def frage_ki(user, system_prompt, frage):
    """Schickt System-Prompt + Nutzerfrage an das Modell des Nutzers.

    Gibt die Textantwort zurück oder wirft ``KIFehler`` mit einer
    Meldung, die direkt an den Nutzer weitergegeben werden kann.
    """
    einstellung = getattr(user, "ki_einstellung", None)
    if not einstellung or not einstellung.ist_konfiguriert:
        raise KIFehler(
            "Kein KI-Modell konfiguriert. Bitte zuerst unter "
            "„KI-Einstellungen“ Anbieter, Modell und API-Key hinterlegen."
        )

    modell = f"{einstellung.provider}/{einstellung.modell}"
    try:
        antwort = litellm.completion(
            model=modell,
            api_key=einstellung.api_key,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": frage or "Bitte formuliere einen Vorschlag."},
            ],
            timeout=30,
        )
    except Exception as exc:  # litellm bündelt Provider-Fehler nicht einheitlich
        raise KIFehler(f"Anfrage an {einstellung.provider} fehlgeschlagen: {exc}") from exc

    inhalt = antwort.choices[0].message.content
    if not inhalt:
        raise KIFehler("Das Modell hat keine Antwort geliefert.")
    return inhalt.strip()
