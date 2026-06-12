# KI-Agent (optionale KI-Unterstützung)

fair-web kann beim Formulieren von Texten unterstützen: für die
**Beschreibung** eines Szenarios und für die **Annahmen** jedes
einzelnen FAIR-Faktors (LEF, TEF, CF, PoA, Vulnerability, TC, CS, LM,
PL, SL, SLEF, SLEM). Die Funktion ist **vollständig optional** – ohne
Konfiguration funktioniert die Eingabe wie gewohnt, ganz ohne KI.

## Konzept

- Jeder Nutzer bringt sein **eigenes KI-Modell** mit: Anbieter,
  Modellname und API-Key werden pro Nutzer in den
  **KI-Einstellungen** hinterlegt.
- Der API-Key wird **verschlüsselt** in der Datenbank gespeichert
  (Fernet, Schlüssel abgeleitet aus `SECRET_KEY`).
- Anfragen gehen **direkt vom Server** an den gewählten Anbieter
  (Anthropic, OpenAI oder Google Gemini) – über die einheitliche
  [`litellm`](https://github.com/BerriAI/litellm)-Schnittstelle.
- Es gibt **kein** zentral hinterlegtes/geteiltes Modell – jeder Nutzer
  zahlt und verantwortet seine eigenen API-Aufrufe.

## Konfiguration (pro Nutzer)

Im Nutzer-Menü (oben rechts) → **„KI-Einstellungen“**
(`/accounts/ki-einstellungen/`):

1. **Anbieter** wählen: Anthropic (Claude), OpenAI (GPT) oder Google
   (Gemini).
2. **Modell**: Freitextfeld mit Vorschlägen (Datalist). Hier muss die
   **exakte Modell-ID** aus der Console/API-Dokumentation des Anbieters
   stehen (z. B. `claude-sonnet-4-5-20250929`, `gpt-4o`,
   `gemini-2.5-pro`) – die Vorschläge sind nur ein Startpunkt.
3. **API-Key**: einfügen und speichern. Beim erneuten Öffnen bleibt das
   Feld leer; ein Hinweis zeigt an, dass bereits ein Key gespeichert
   ist. **Leer lassen** beim Speichern = bestehender Key bleibt
   unverändert.

Modell und Anbieter lassen sich jederzeit ändern, ohne den Key neu
eingeben zu müssen – einfach das Feld überschreiben und speichern.

Ohne vollständige Konfiguration (Anbieter **und** Modell **und**
API-Key) bleibt die KI-Unterstützung inaktiv; ein Klick auf einen
KI-Button zeigt dann nur einen Hinweis auf die Einstellungsseite.

## Bedienung im Szenario-Formular

Neben der **Beschreibung** und neben jedem **Annahmen**-Feld gibt es
einen kleinen **✨-Button**. Klick öffnet ein Offcanvas-Panel:

1. Im Textfeld „Was soll die KI tun?“ kann eine kurze Anweisung
   formuliert werden (optional – ohne Text formuliert die KI einen
   Standard-Vorschlag).
2. **„Anfrage senden“** schickt den aktuellen Formularstand (Name,
   Beschreibung, Verteilung/Parameter des jeweiligen Faktors) zusammen
   mit dem feldspezifischen Kontext an das konfigurierte Modell.
3. Die Antwort erscheint im Antwortfeld; **„Übernehmen“** schreibt sie
   ins ursprüngliche Feld (mit Bestätigungsabfrage, falls dort schon
   Text steht).

## Technischer Aufbau (für Entwickler)

| Baustein | Datei | Zweck |
|---|---|---|
| Verschlüsselung | `apps/konten/krypto.py` | Fernet-Verschlüsselung des API-Keys |
| Pro-Nutzer-Modell | `apps/konten/models.py` (`KIEinstellung`) | Provider, Modell, verschlüsselter Key |
| Einstellungs-UI | `apps/konten/forms.py`, `views.py`, `templates/registration/ki_einstellungen.html` | GET/POST-Formular |
| Prompt-Bausteine | `apps/szenarien/ki_prompts.py` | System-Prompts pro Feldtyp |
| KI-Aufruf | `apps/szenarien/ki_service.py` | `litellm.completion(...)`, Fehlerbehandlung |
| AJAX-Endpoint | `apps/szenarien/views.py` (`ki_vorschlag`), `urls.py` | Nimmt Formularstand entgegen, liefert `{"ok": ..., "antwort"/"fehler": ...}` |
| UI | `templates/szenarien/_node_fields.html`, `form.html` | ✨-Buttons, Offcanvas, JS |

### Prompt-Aufbau (`ki_prompts.py`)

Jede Anfrage bekommt einen **System-Prompt**, der Rolle und Kontext
vorgibt, plus die freie Nutzerfrage als „user“-Nachricht
(`ki_service.frage_ki`).

- **`prompt_beschreibung(szenario_name)`** – Kontext: Name des
  Szenarios. Bittet um eine kurze (2–5 Sätze), auch für
  Nicht-Techniker verständliche Beschreibung mit Fokus auf Auslöser,
  betroffene Assets und möglichen Schaden.

- **`prompt_annahmen(code, szenario_name, szenario_beschreibung,
  verteilung, params)`** – Kontext: Szenario-Name/-Beschreibung sowie
  Name, Kürzel und FAIR-Erläuterung des Faktors (über
  `fair_tree.target(code)` / `abbr(code)` / `erklaerung(code)`), plus
  aktuell eingestellte Verteilung und Parameter. Bittet um eine kurze
  (1–4 Sätze) Begründung der gewählten Werte.

### Faktorspezifische Zusatz-Hinweise

Damit die KI bei bestimmten Faktoren die richtigen FAIR-Konzepte
mitdenkt, gibt es in `ki_prompts.py` die Map `_ZUSATZ_HINWEISE`
(Code → zusätzlicher Satz, der an den Annahmen-Prompt angehängt wird).
Aktuell hinterlegt:

- **LM, PL, SL, SLEM** – Erinnerung an die **sechs FAIR-Verlustformen**
  (Productivity, Response, Replacement, Fines & Judgments, Competitive
  Advantage, Reputation); bei SL/SLEM zusätzlich Fokus auf sekundäre
  Beteiligte (Behörden, Kunden, Öffentlichkeit).
- **TC, CS** – Einordnung als **Perzentil** (Akteurs- bzw.
  Kontrollstärke-Population).
- **CF, TEF** – Begründung über **branchentypische
  Kontakt-/Angriffsraten** bzw. Threat-Intelligence-Daten.
- **POA** – Begründung über Attraktivität des Ziels und
  Aufwand/Risiko für den Akteur.
- **SLEF** – Anteil der Primärereignisse mit Reaktion sekundärer
  Beteiligter.

#### Eigene Hinweise ergänzen oder anpassen

Um den Prompt für einen Faktor zu verfeinern, in
`apps/szenarien/ki_prompts.py` die Map `_ZUSATZ_HINWEISE` erweitern
bzw. den vorhandenen Eintrag anpassen:

```python
_ZUSATZ_HINWEISE = {
    "TC": "Ordne die Fähigkeit des Bedrohungsakteurs als Perzentil ein …",
    # weiteren/angepassten Hinweis für einen Code (z. B. "VULN") ergänzen:
    "VULN": "…",
}
```

Der Hinweis wird automatisch an den Annahmen-Prompt des jeweiligen
Faktors angehängt (`_hinweis(code)` in `prompt_annahmen`). Für
grundsätzliche Änderungen an Ton, Sprache oder Länge der Antworten
dient `_BASIS` als gemeinsamer Grundbaustein aller Prompts.

### Fehlerbehandlung & Verfügbarkeit

`ki_service.ist_verfuegbar(user)` prüft, ob `KIEinstellung` vollständig
konfiguriert ist (Provider **und** Modell **und** API-Key).
`ki_service.frage_ki(...)` wirft bei fehlender Konfiguration oder
Provider-Fehlern (z. B. ungültiger Key) eine `KIFehler`-Exception mit
nutzerfreundlicher Meldung – der Endpoint `ki_vorschlag` gibt diese als
`{"ok": false, "fehler": "..."}` zurück (nie HTTP 500).

### Unterstützte Anbieter

Aktuell: **Anthropic (Claude)**, **OpenAI (GPT)**, **Google (Gemini)** –
über `litellm` mit Provider-Präfix vor dem Modellnamen (z. B.
`anthropic/claude-sonnet-4-5-20250929`). Microsoft Copilot ist
vorerst zurückgestellt (keine offene Chat-API für Drittnutzer
verfügbar), ggf. später als Azure-OpenAI-Modell nachrüstbar.
