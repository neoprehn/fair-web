"""Prompt-Baustein für den optionalen KI-Assistenten bei CAM-Verlustklassen.

Eigenständige, schlanke Kopie des Musters aus ``apps.szenarien.ki_prompts``
(dort: ``prompt_annahmen`` für FAIR-Faktoren) – nur für das eine
unterstützte Feld (Annahmen einer ``CamVerlustklasse``), da ``apps.cam``
bewusst unabhängig von ``apps.szenarien``/``fair_tree`` bleibt (siehe
``models.py``-Docstring). Der generische KI-Aufruf selbst
(``ki_service.frage_ki``) wird dagegen wiederverwendet, nicht dupliziert –
der ist provider-/domänenunabhängig.
"""

_BASIS = (
    "Du bist ein erfahrener Analyst für FAIR-CAM (Controls Analytics Model) "
    "und hilfst beim Formulieren von Texten für ein CAM-Szenario in einer "
    "Webanwendung. Antworte auf Deutsch, knapp und konkret, ohne Floskeln. "
    "Gib nur den Text zurück, der in das Feld eingetragen werden soll – "
    "keine Erklärungen oder Anführungszeichen um die Antwort."
)

_KLASSE_HINWEISE = {
    "early": "Das ist der Verlust bei früher Erkennung (early) – der Angriff "
             "wurde schon in einer frühen Kill-Chain-Stufe gestoppt.",
    "mid": "Das ist der Verlust bei mittlerer Erkennung (mid) – der Angriff "
           "kam weiter voran, bevor er gestoppt wurde.",
    "late": "Das ist der Verlust bei später Erkennung (late) – der Angriff "
            "wurde erst kurz vor dem eigentlichen Schaden gestoppt.",
    "full_impact": "Das ist der Verlust bei vollem Schaden (full_impact) – "
                   "der Angriff wurde in keiner Stufe erkannt/gestoppt.",
    "attacker_fails": "Das ist der Verlust, wenn der Angreifer scheitert "
                       "(attacker_fails) – meist nur geringe Restkosten "
                       "(z. B. Aufwand für Analyse/Monitoring des Versuchs).",
}


def prompt_annahmen(klasse_display, klasse_code, szenario_name, szenario_beschreibung, verteilung, params):
    """System-Prompt für das Annahmen-Feld einer CAM-Verlustklasse.

    ``klasse_display`` ist das lesbare Label (z. B. "Früh (early)"),
    ``klasse_code`` der rohe Klassen-Code (z. B. "early") für die
    Zusatz-Hinweise, ``verteilung``/``params`` die aktuell eingestellte
    Verteilung mit Parametern.
    """
    kontext = [f"CAM-Szenario: \"{szenario_name or '(noch ohne Namen)'}\""]
    if szenario_beschreibung:
        kontext.append(f"Beschreibung des Szenarios: {szenario_beschreibung}")
    kontext.append(f"Verlustklasse: {klasse_display}")
    if verteilung:
        kontext.append(f"Aktuell eingestellte Verteilung: {verteilung}")
    if params:
        kontext.append(f"Aktuelle Parameter: {params}")
    kontext_text = "\n".join(f"- {z}" for z in kontext)
    hinweis = _KLASSE_HINWEISE.get(klasse_code, "")
    hinweis_text = f" {hinweis}" if hinweis else ""
    return (
        f"{_BASIS}\n\n"
        f"Es geht um das Feld \"Annahmen\" für die Verlustklasse {klasse_display} "
        f"des oben genannten CAM-Szenarios. Kontext:\n{kontext_text}\n\n"
        "Formuliere bzw. überarbeite die Annahmen/Begründung für die gewählten "
        "Werte dieser Verlustklasse: kurz (1-4 Sätze), nachvollziehbar für eine "
        f"spätere Prüfung.{hinweis_text}"
    )
