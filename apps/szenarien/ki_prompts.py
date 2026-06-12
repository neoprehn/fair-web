"""Prompt-Bausteine für den optionalen KI-Assistenten.

Baut System-Prompts für die zwei unterstützten Feldtypen:

- ``beschreibung``: die freie Beschreibung eines ``Szenario``
- ``annahmen``: das "Annahmen"-Feld einer ``FaktorEingabe`` (pro
  FAIR-Knoten)

Beide liefern einen System-Prompt, der dem Modell Rolle + Kontext
vorgibt; die eigentliche Nutzeranfrage (Freitext) kommt separat dazu
(siehe ``ki_service.frage_ki``).
"""

from . import fair_tree

_BASIS = (
    "Du bist ein erfahrener FAIR-Risikoanalyst (Factor Analysis of "
    "Information Risk) und hilfst beim Formulieren von Texten für ein "
    "Risikoszenario in einer Webanwendung. Antworte auf Deutsch, knapp "
    "und konkret, ohne Floskeln. Gib nur den Text zurück, der in das "
    "Feld eingetragen werden soll – keine Erklärungen oder Anführungszeichen "
    "um die Antwort."
)

# Zusätzliche fachliche Denkanstöße je FAIR-Faktor für die KI (nicht für die
# Nutzer-Erklärung in fair_tree.ERKLAERUNG gedacht, sondern um die KI gezielt
# an FAIR-Konzepte zu erinnern, die in den Annahmen auftauchen sollten).
_ZUSATZ_HINWEISE = {
    "LM": "Berücksichtige dabei die sechs FAIR-Verlustformen (Productivity, "
          "Response, Replacement, Fines & Judgments, Competitive Advantage, "
          "Reputation) – nenne, welche davon hier relevant sind.",
    "PL": "Berücksichtige dabei die sechs FAIR-Verlustformen (Productivity, "
          "Response, Replacement, Fines & Judgments, Competitive Advantage, "
          "Reputation) – nenne, welche davon als Primärverlust unmittelbar "
          "beim Asset-Eigner anfallen.",
    "SL": "Berücksichtige dabei die sechs FAIR-Verlustformen (Productivity, "
          "Response, Replacement, Fines & Judgments, Competitive Advantage, "
          "Reputation) – beschreibe, welche sekundären Beteiligten (Behörden, "
          "Kunden, Öffentlichkeit) reagieren könnten und welche davon "
          "betroffen sind.",
    "SLEM": "Berücksichtige dabei die sechs FAIR-Verlustformen (Productivity, "
            "Response, Replacement, Fines & Judgments, Competitive Advantage, "
            "Reputation), soweit sie für sekundäre Beteiligte anfallen.",
    "TC": "Ordne die Fähigkeit des Bedrohungsakteurs als Perzentil der "
          "Akteurspopulation ein (z. B. Gelegenheitstäter vs. organisierte "
          "Gruppen vs. staatliche Akteure).",
    "CS": "Ordne die Stärke der Schutzmaßnahmen als Perzentil ein, gemessen "
          "daran, wie schwer sie für einen durchschnittlichen Akteur zu "
          "überwinden sind.",
    "CF": "Stütze die Häufigkeit auf beobachtbare oder branchentypische "
          "Kontaktraten (z. B. Anzahl Angriffsversuche/Scans pro Zeitraum).",
    "TEF": "Stütze die Häufigkeit auf Threat-Intelligence- oder "
           "Branchendaten zu Angriffsversuchen auf vergleichbare Assets.",
    "POA": "Begründe die Wahrscheinlichkeit, dass der Akteur nach Kontakt "
           "tatsächlich agiert, z. B. anhand von Attraktivität des Ziels und "
           "Aufwand/Risiko für den Akteur.",
    "SLEF": "Begründe, in welchem Anteil der Primärereignisse überhaupt eine "
            "Reaktion sekundärer Beteiligter zu erwarten ist.",
}


def _hinweis(code):
    return _ZUSATZ_HINWEISE.get(code, "")


def prompt_beschreibung(szenario_name):
    """System-Prompt für die Beschreibung eines Szenarios."""
    name = szenario_name or "(noch ohne Namen)"
    return (
        f"{_BASIS}\n\n"
        f"Es geht um die Beschreibung des Risikoszenarios \"{name}\". "
        "Formuliere bzw. überarbeite die Beschreibung: kurz (2-5 Sätze), "
        "verständlich auch für Nicht-Techniker, mit Fokus auf Auslöser, "
        "betroffene Assets und möglichen Schaden."
    )


def prompt_annahmen(code, szenario_name, szenario_beschreibung, verteilung, params):
    """System-Prompt für das Annahmen-Feld eines FAIR-Faktors.

    ``code`` ist der FAIR-Knoten-Code (z. B. "TC"), ``verteilung``/
    ``params`` die aktuell eingestellte Verteilung mit Parametern.
    """
    name = fair_tree.target(code)
    abbr = fair_tree.abbr(code)
    erklaerung = fair_tree.erklaerung(code)
    kontext = [f"Szenario: \"{szenario_name or '(noch ohne Namen)'}\""]
    if szenario_beschreibung:
        kontext.append(f"Beschreibung des Szenarios: {szenario_beschreibung}")
    kontext.append(f"FAIR-Faktor: {name} ({abbr})")
    if erklaerung:
        kontext.append(f"Erläuterung dieses Faktors: {erklaerung}")
    if verteilung:
        kontext.append(f"Aktuell eingestellte Verteilung: {verteilung}")
    if params:
        kontext.append(f"Aktuelle Parameter: {params}")
    kontext_text = "\n".join(f"- {z}" for z in kontext)
    hinweis = _hinweis(code)
    hinweis_text = f" {hinweis}" if hinweis else ""
    return (
        f"{_BASIS}\n\n"
        f"Es geht um das Feld \"Annahmen\" für den Faktor {name} ({abbr}) "
        f"des oben genannten Risikoszenarios. Kontext:\n{kontext_text}\n\n"
        "Formuliere bzw. überarbeite die Annahmen/Begründung für die "
        "gewählten Werte dieses Faktors: kurz (1-4 Sätze), nachvollziehbar "
        f"für eine spätere Prüfung.{hinweis_text}"
    )
