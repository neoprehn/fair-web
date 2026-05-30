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

### Phase 4b – FAIR-Baum-Eingabe & Ergebnis-Baum (UI-Ausbau) ✅ live
- [x] **Slice 1:** Baumstruktur + Datenmodell (`fair_tree.py`, alle 12 Knoten, Typen, Schnitt-Validierung)
- [x] **Slice 2:** Dynamisches Baum-Formular, Verteilungs-Auswahl je Faktor eingeschränkt (inkl. Poisson/Beta/Lognormal), korrekte Beschriftungen, Schnitt-Gültigkeit serverseitig
- [x] **Slice 3:** Interaktives SVG des FAIR-Baums; aktiver Knoten leuchtet beim Reinklicken auf
- [x] **Slice 4:** Ergebnis-Baum nach der Simulation — Wert je Knoten, **Eingabe = Sky-Blau**, **berechnet = Grün** (Einzel-Simulation)
- [x] **Umbau:** SVG nach oben (neben Name/Beschreibung), Faktoren als klickbarer FAIR-Baum (Klick = auffalten), 2-Spalten-/Baum-Fächerung, schmalere Karten
- [x] Lokale Vorschau vor jedem Live-Deploy; Slices einzeln nach `main` gemergt

---

### Phase 5 – Grafiken & Auswertung
- [ ] Plotly einbinden
- [ ] LEC-Kurve animiert aufbauen
- [ ] Weitere Grafiken (Verteilung, Häufigkeit etc.)
- [ ] Schieber bewegen → Kurve aktualisiert sich live
- [ ] Mehrere Szenarien in einem Chart vergleichen
- [ ] Lokaler Test
- [ ] Commit & Push → Branch `feature-grafiken` mergen in `main`

---

### Phase 6 – Export
- [ ] Excel Export mit openpyxl
- [ ] PPT Bericht mit python-pptx
- [ ] Grafiken in Export einbetten
- [ ] Download-Button in der Oberfläche
- [ ] Lokaler Test
- [ ] Commit & Push → Branch `feature-export` mergen in `main`

---

### Phase 7 – Admin-Bereich
- [ ] Django Admin einrichten
- [ ] Standard-Seed konfigurierbar machen
- [ ] Standard-Simulationsanzahl konfigurierbar machen
- [ ] Benutzer & Zugriffsrechte einrichten
- [ ] Vorschlagswerte für Konfidenzen editierbar machen (wahrscheinlich mit Eingriff in pyfair)
- [ ] Hell/Dunkel-Design Schalter
- [ ] Lokaler Test
- [ ] Commit & Push → Branch `feature-admin` mergen in `main`

---

### Phase 8 – Deployment auf IONOS VPS
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
### ab hier alles von @neoprehn
### Phase 9 - Sicherheit + Ideen
- [ ] Prüfen des Deploys hinsichtlich Sicherheits-Design Fehler
- [ ] Home Bildschirm verbessern (Modellerklärung. interaktives User-Durchklicken ohne Simulation)
- [ ] Dokumentation zur Webseite (Bedienhilfe etc. aufbauen)
- [ ] Szenariocluster mit Szenarien 
- [ ] Bei Auswahl der gemeinsamen Berechnung von Szenarien die Möglichkeit schaffen, compare oder add als Ergebnis zu haben, diese sollte dann auch als Ergebnis abgespeichert werden (unter eigenem Reiter "Gemeinsame Szenarien" oder "Szenariovergleiche")
- [ ] Eingabe von Annahmen je eigegebener Faktor (ist dann auch im Szenarioergebnis abzuspeichern)
- [ ] Ausbaustufe: KI-Agent, der bei der Formulierung der Szenarien hilft, um eine hohe Qualität sicherzustellen
- [ ] Lokaler Test
- [ ] Commit & Push → Branch `feature-export` mergen in `main`

---
### ab hier alles von @neoprehn
### Phase 10 - FAOR + FAIR CAM
- [ ] Einbindung in die Webseite der FAOR - Logik
- [ ] Einbindung von FAIR CAM (hierzu muss wahrscheinlich noch alles als pyfaircam entwickelt werden)
- [ ] Wenn Modelle schon einmal simuliert wurden, dann Ergebnisse in der Eingabeseite mit angebeben und automatisch nachberechnen, wenn neue Eingaben stattgefunden haben (Knopf neuberechnen)
- [ ] Historie in den Simulationen (aufklappbar) im Protokoll zeigen (wie eine Verzeichnisstruktur mit letzter Simulaion ganz oben)
- [ ] 
- [ ] 
- [ ] 
- [ ] Lokaler Test
- [ ] Commit & Push → Branch `feature-export` mergen in `main`

## Branch-Übersicht

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

---

## Deployment Workflow (ab Phase 8)

```
VS Code → git push → GitHub → VPS: git pull → neoprehn.de
```

---

## Wichtige Dateien zum Start

| Datei | Warum wichtig |
|---|---|
| `pyfair/model/model.py` | FairModel Kernlogik |
| `pyfair/model/meta_model.py` | Mehrere Szenarien kombinieren |
| `pyfair/report/simple_report.py` | Bestehende Report-Logik |
| `pyfair/utility/beta_pert.py` | Wahrscheinlichkeitsverteilung |
| `requirements.txt` | Bestehende Abhängigkeiten |
| `sample/` | Beispiele wie PyFair genutzt wird |
