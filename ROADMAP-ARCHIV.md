# fair-web – Archiv (erledigte Phasen)

Diese Datei sammelt abgeschlossene Roadmap-Punkte, damit `roadmap.md` schlank
bleibt und nur noch offene Arbeit zeigt. Historischer Kontext, keine
Handlungsanweisung.

---

### Phase 1 – Vorbereitung & Analyse
- [x] Claude Code Prompt einfügen
- [x] PyFair Code analysieren lassen (model.py, meta_model.py, simple_report.py)
- [x] Sample-Dateien analysieren lassen
- [x] requirements.txt prüfen lassen
- [x] Branch `feature-webapp` anlegen

---

### Phase 2 – Django Grundgerüst
- [x] Django installieren
- [x] Django Projekt aufsetzen (`config/`)
- [x] Apps anlegen (szenarien, berechnung, auswertung, export)
- [x] MariaDB Datenbank verbinden
- [x] Bootstrap 5 Grundlayout bauen (`base.html`)
- [x] Navigation zwischen Seiten einrichten
- [x] Lokaler Test – läuft die Seite?
- [x] Commit & Push zu GitHub

---

### Phase 3 – Szenarien & FAIR Parameter
- [x] Datenbankmodell für Szenarien erstellen _(Szenario + FaktorEingabe, Faktor LEF/LM, Verteilung PERT/Normal/Konstant)_
- [x] Formular für FAIR Parameter bauen _(Verteilung pro Faktor wählbar, Parameterfelder per JS ein-/ausgeblendet)_
- [x] Schieber (Slider) für Unsicherheit einbauen _(5 pyfair-Konfidenzstufen, Live-Wertanzeige)_
- [x] Szenario speichern in MariaDB
- [x] Szenario laden & bearbeiten
- [x] Szenario löschen
- [x] Dashboard mit Szenario-Übersicht
- [x] Lokaler Test _(pytest + pytest-django, 19 Tests grün)_
- [x] Commit & Push → Branch `feature-szenarien` mergen in `main`

---

### Phase 4 – PyFair Anbindung & Berechnung
- [x] PyFair als Engine einbinden _(editable im venv installiert; `services.simuliere`)_
- [x] Monte Carlo Simulation starten _(Button → Hintergrund-Thread, Variante A)_
- [x] Live-Fortschrittsanzeige während Simulation _(chunked + AJAX-Polling)_
- [x] Ergebnisse in MariaDB als JSON speichern _(`Simulationslauf.ergebnis` inkl. LEC-Daten)_
- [x] Mehrere Szenarien gleichzeitig berechnen _(`FairMetaModel`, Summenrisiko + Beitrag je Szenario)_
- [x] Lokaler Test _(35 Tests grün)_
- [x] Commit & Push → Branch `feature-berechnung` mergen in `main`

---

### Phase 4b – FAIR-Baum-Eingabe & Ergebnis-Baum (UI-Ausbau)
- [x] **Slice 1:** Baumstruktur + Datenmodell (`fair_tree.py`, alle 12 Knoten, Typen, Schnitt-Validierung)
- [x] **Slice 2:** Dynamisches Baum-Formular, Verteilungs-Auswahl je Faktor eingeschränkt (inkl. Poisson/Beta/Lognormal), korrekte Beschriftungen, Schnitt-Gültigkeit serverseitig
- [x] **Slice 3:** Interaktives SVG des FAIR-Baums; aktiver Knoten leuchtet beim Reinklicken auf
- [x] **Slice 4:** Ergebnis-Baum nach der Simulation — Wert je Knoten, **Eingabe = Sky-Blau**, **berechnet = Grün** (Einzel-Simulation)
- [x] **Umbau:** SVG nach oben (neben Name/Beschreibung), Faktoren als klickbarer FAIR-Baum (Klick = auffalten), 2-Spalten-/Baum-Fächerung, schmalere Karten
- [x] Lokale Vorschau vor jedem Live-Deploy; Slices einzeln nach `main` gemergt

---

### Phase 5 – Grafiken & Auswertung
- [x] Plotly einbinden _(Plotly.js CDN, LEC-Chart im Dark-Theme)_
- [x] LEC-Kurve **logarithmische Schadensachse** _(P90 bei ~3/4 der Achse)_
- [x] **Risikotoleranz-Overlay** _(constant→vline, curve→Punkte, distribution→Exceedance)_
- [x] LEC-Kurve **animiert aufbauen**
- [x] **Schnittpunkt LEC × Risikotoleranz** berechnen + im Chart markieren + in Tabelle (Loss €, Toleranz %)
- [x] **Risikoperzentile als VaR** 10/20/50/80/90/95/99 (farblich umrandete Gruppe)
- [x] **SVG-Baum-Tooltips** je Knoten (5 Nachkommastellen; berechnet: Mittelwert/StdAbw/P90/P95, Eingabe: Parameter)
- [x] **Knoten-Detailtabelle** unter der Grafik (pyfair-Report-Form + P90/P95)
- [x] „Neu berechnen" → führt zum Szenario-Bearbeiten
- [x] Lokaler Test _(76 Tests grün)_
- [x] Commit & Push → Branch `feature-ergebnis-grafik` mergen in `main`
- [x] Weitere Grafiken: **Verteilung** des Jahresschadens + **Häufigkeit** der Schadenereignisse (Histogramme); Ergebnis-SVG schmaler; VaR + Risikotoleranz horizontal angeordnet
- [x] Schieber bewegen → Kurve aktualisiert sich live _(Live-LEC-Vorschau auf der Eingabeseite: debounced Mini-Simulation via AJAX `lec-vorschau`, inkl. Toleranz-Overlay + Schnittpunkt)_
- [x] Mehrere Szenarien in einem Chart vergleichen _(neue **Vergleich**-Entität gruppiert bestehende Szenarien; Dashboard-Liste + „Neuer Vergleich"; Ergebnis mit **Compare**-Überlagerung der LECs ↔ **Add**-Summe umschaltbar)_

---

### Phase 5b – Feinschliff der Auswertungen
- [x] Einzeichnen der Risikotoleranzkurve bei Compare (durchgezogen in rot) _(Referenz-Szenario am Vergleich wählbar)_
- [x] Risikotoleranzkurve auf rot durchgezogen ändern _(Einzel- + Vergleichs-Chart)_
- [x] Risikotoleranz-Eingabe wird jetzt auf der Szenario-Detailseite angezeigt
- [x] In der Version Vergleichen die Schnittpunkte mit der Risikotoleranz – als Punkt in der Grafik + Tabelle
- [x] Designänderung bei der einzelnen Simulation:
    - [x] Maximum-Karte → „Maximum (Worst Case P95)", zeigt P95
    - [x] SVG: Baum im Kästchen zentriert, 20 % größere Knoten-Kästchen
    - [x] VaR & Risikotoleranz-Kästchen auf Median-Zeilen-Höhe, rechtsbündig
    - [x] mehr Abstand zwischen Knoten-Detailtabelle und Grafik-Block
    - [x] Knoten-Detailtabelle: Min raus, Spalten enden mit P90/P95/Max

---

### Phase 6 – Deployment auf IONOS VPS
- [x] Per SSH auf VPS verbinden
- [x] Ubuntu aktualisieren
- [x] Python & pip installieren
- [x] MariaDB auf VPS installieren & einrichten
- [x] Nginx/Reverse-Proxy konfiguriert _(Plesk proxyt auf gunicorn-Unix-Socket, HTTPS aktiv)_
- [x] Gunicorn installieren & konfigurieren _(systemd-Dienst `pyfair`, 3 Worker, Socket `pyfair.sock`, WSGI `config.wsgi`)_
- [x] GitHub Repository auf VPS klonen _(am 29.05.2026 nachgeholt – Ordner war vorher KEIN Git-Repo)_
- [x] Umgebungsvariablen setzen _(`.env` auf dem Server vorhanden, MariaDB-Verbindung steht)_
- [x] SSL Zertifikat einrichten _(HTTPS auf fair.neoprehn.de aktiv, liefert 200)_
- [x] Domain `fair.neoprehn.de` verbinden
- [x] Finaler Test auf neoprehn.de _(Phase-3-App ist live – Dashboard & Anlege-Formular erreichbar)_

> **CI/CD-Hinweis (29.05.2026):** Der Auto-Deploy griff lange Zeit NICHT – das Zielverzeichnis war kein Git-Checkout, und `deploy.yml` verbarg den Fehler hinter grünen Häkchen (kein `set -e`). Beides ist gefixt: Server-Ordner ist jetzt ein `main`-Checkout, `deploy.yml` nutzt `set -euo pipefail` + `git fetch`/`reset --hard`. Push/Merge nach `main` deployt jetzt zuverlässig.

---

### Phase 7 – Admin-Bereich
- [x] Django Admin einrichten _(Modelle registriert: Szenario/Faktor/Angreifertyp/Vergleich/Läufe + App-Konfiguration)_
- [x] Standard-Seed konfigurierbar (globale Variable in der App-Konfiguration; wenn global → in der Szenarioeingabe „nur lesend")
- [x] Standard-Simulationsanzahl konfigurierbar (globale Variable; wenn global → „nur lesend")
- [x] Benutzer & Zugriffsrechte einrichten _(Login-Pflicht + Selbstregistrierung; Rollen Betrachter/Analyst/Konfigurator/Administrator via Gruppen; serverseitige Rechte (403) + UI-Gating je Rolle)_
- [x] Vorschlagswerte für Konfidenzen editierbar (App-Konfiguration, strukturierter 5×4-Editor): steuert Anzeige UND Berechnung – `to_fair_kwargs` übergibt den expliziten Formparameter (gamma/sigma/range/k) an pyfair statt der Konfidenzstufe (kein pyfair-Patch)
- [x] Hell/Dunkel-Design Schalter _(Navbar-Umschalter, Bootstrap data-bs-theme, Light-/Dark-Palette via CSS-Variablen, in localStorage gemerkt; Plotly-Charts theme-abhängig)_
- [x] Euro/Dollar-Schalter (global in App-Konfiguration): tauscht Währungssymbol und Separatoren app-weit (€ → 1.234,56 · $ → 1,234.56) via Locale-Middleware + Context-Processor; Charts/JS folgen der Locale
- [x] „Unternehmens-Risikotoleranz" als global konfigurierbar (App-Konfiguration; wenn vorgegeben → Eingabe „nur lesend", gilt für alle Szenarien)
- [x] Lokaler Test · Commit & Push → Branch `feature-admin` mergen in `main`

---

### Phase 9 – Sicherheit + Ideen (größtenteils erledigt)
- [x] Home-Bildschirm: Startseite unter `/` mit FAIR-Erklärung + interaktivem,
      klickbarem FAIR-Baum (Knoten-Erklärung ohne Simulation); Szenario-Dashboard
      nach `/szenarien/` verschoben (URL-Namen unverändert)
- [x] Bedienhilfe (In-App): Hilfeseite unter `/hilfe/` im Menü, mit
      Inhaltsverzeichnis + Abschnitten (Szenario/Faktoren/Verteilungen/
      Toleranz/Simulation/Vergleich/Klonen/Rollen/Einstellungen)
- [x] Szenariocluster (organisatorische Gruppen): `Cluster`-Modell (M2M Szenarien),
      CRUD, Dashboard-Filterleiste + Cluster-Badges je Szenario, Rechte je Rolle
- [x] Szenariovergleiche als eigener Reiter „Vergleiche" in der Navbar:
      `/szenarien/vergleiche/` listet alle Vergleiche mit gespeichertem
      Gesamtrisiko (Ø) + Link zum letzten Lauf; Berechnen/Bearbeiten/Löschen.
      Compare↔Add-Umschalter + Persistenz via `Vergleich`/`MetaLauf` bestand bereits
- [x] Eingabe von **Annahmen je Faktor** _(`FaktorEingabe.annahmen`, im Formular
      eingebbar, in der Szenario-Detailansicht je Faktor angezeigt)_
- [x] Ausbaustufe: KI-Agent, der bei der Szenario-Formulierung hilft
      _(pro Nutzer eigenes KI-Modell in den KI-Einstellungen konfigurierbar –
      Provider (Anthropic/OpenAI/Gemini) + Modell + API-Key, verschlüsselt
      gespeichert (`apps/konten/krypto.py`, `KIEinstellung`); Anbindung via
      `litellm` (`apps/szenarien/ki_service.py`). ✨-Button + gemeinsames
      Offcanvas für Szenario-Beschreibung und alle 12 Annahmen-Felder,
      faktorspezifische Zusatz-Hinweise in `apps/szenarien/ki_prompts.py`.
      Copilot weiterhin zurückgestellt. Doku: `docs/ki-agent.md`.)_
- [x] Lokaler Test · Commit & Push → `feature-ki-agent` gemerged in `main`
- [x] App-Härtung: Security-Header + HTTPS-Härtung in Prod; Registrierungs-Policy
      (Admin-Freigabe, `is_active=False`), Brute-Force-Schutz (`django-axes`),
      Dependency-Audit (`pip-audit`) — siehe `SICHERHEIT.md`

---

### Eigene ReadTheDocs-Dokumentationssite (Grundausbau erledigt)
- [x] **Live:** https://fair-web.readthedocs.io/de/latest/ — ReadTheDocs mit
      GitHub verbunden, baut grün bei jedem Push auf `main`
      (Dashboard: https://app.readthedocs.org/dashboard/)
- [x] Gerüst im fair-web-Repo: `.readthedocs.yaml`, `mkdocs.yml` (Material),
      `docs/` (Start, Bedienung, FAIR-Taxonomie, pyfair-Fork) + `docs/requirements.txt`
- [x] Vollausbau der Engine-Doku auf pyfair-Detailgrad (DE), aus dem
      Fork-Quellcode abgeleitet: Installation, Schnellstart, Modelle erstellen,
      Eingaben & Verteilungen (Legacy + strukturierte API, alle 6 Verteilungen,
      Konfidenz-Mapping-Tabelle, Beta-Konfidenzintervall), Meta-Modelle
      (sum/compare), Berichte, Serialisierung & Datenbank, Fork-Erweiterungen;
      Nav in Sektionen, `mkdocs build --strict` grün
  - [x] deutsche pyfair-Seite (aus README, an den neoprehn-Fork angepasst)
- [x] **Inhaltliche Basis** umgesetzt: Doku bildet den **erweiterten** Fork ab
      (`neoprehn/pyfair`), nicht nur das Original (strukturierte Eingabe-API,
      Konfidenz-Mapping, Beta-Konfidenzintervall, zusätzliche Verteilungen)
- [x] Abschnitte vorhanden: FAIR-Taxonomie (Open-FAIR/O-RT), pyfair-API (Fork),
      fair-web-Bedienung (aus der In-App-Hilfe abgeleitet)
- [x] Verlinkung aus der App auf die Doku-Site (Footer + Hilfeseite)

---

## Branch-Übersicht (Stand vor Phase 8)

```
main                    →  stabil, läuft auf VPS
│
├── feature-webapp       →  Phase 2: Django Grundgerüst
├── feature-szenarien    →  Phase 3: FAIR Parameter
├── feature-berechnung   →  Phase 4: PyFair Anbindung
├── feature-grafiken     →  Phase 5: Plotly Animationen
├── feature-export       →  Phase 6: Excel & PPT
└── feature-admin        →  Phase 7: Admin-Bereich
```

## Wichtige Dateien zum Start (aus der ursprünglichen Roadmap)

| Datei | Warum wichtig |
|---|---|
| `pyfair/model/model.py` | FairModel Kernlogik |
| `pyfair/model/meta_model.py` | Mehrere Szenarien kombinieren |
| `pyfair/report/simple_report.py` | Bestehende Report-Logik |
| `pyfair/utility/beta_pert.py` | Wahrscheinlichkeitsverteilung |
| `requirements.txt` | Bestehende Abhängigkeiten |
| `sample/` | Beispiele wie PyFair genutzt wird |
