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

### Phase 6 – Deployment auf IONOS VPS ✅ erledigt
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
- [ ] Django Admin einrichten
- [ ] Standard-Seed konfigurierbar machen mit Otion als globale Variable. Wenn global, dann in der Szenarioeingabe nur noch als "nur lesend" anzeigen
- [ ] Standard-Simulationsanzahl konfigurierbar machen mit Otion als globale Variable. Wenn global, dann in der Szenarioeingabe nur noch als "nur lesend" anzeigen
- [ ] Benutzer & Zugriffsrechte einrichten
- [ ] Vorschlagswerte für Konfidenzen editierbar machen (wahrscheinlich mit Eingriff in pyfair)
- [ ] Hell/Dunkel-Design Schalter
- [ ] Euro/ Dollar Schalter und damit verbunden "." und "," für die Separatoren tauschen
- [ ] "Unternehmens-Risikotoleranz" als global konfigurierbar machen. Wenn diese vorgegeben ist, dann aus der Eingabe nur noch als "nur lesend" anzeigen
- [ ] Lokaler Test
- [ ] Commit & Push → Branch `feature-admin` mergen in `main`

---

### Phase 8 – Export _(ganz nach hinten gestellt)_
- [ ] Excel Export mit openpyxl
- [ ] PPT Bericht mit python-pptx
- [ ] PDF Bericht 
- [ ] Grafiken in Export einbetten
- [ ] Download-Button in der Oberfläche
- [ ] Lokaler Test
- [ ] Commit & Push → Branch `feature-export` mergen in `main`

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
- [ ] Schnittpunkte in der LEC berechnen zwischen Toleranz und LEC bzw. bei mehreren Simulationen zwischen den individuellen LECs und der Risikotoleranz. Ergebnisdarstellung in Tabellenform (wie bei file:///C:/Users/mirko/OneDrive/Dokumente/Entwicklung/fair/results/Laptop_neu.html)
- [ ] Punkte-Streudiagramm der primären und sekundären Verluste (in rot und blau) - wie bei Laptop_neu.html
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
