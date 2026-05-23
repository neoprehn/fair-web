### Phase 1 – Vorbereitung & Analyse
- [ ] Claude Code Prompt einfügen
- [ ] PyFair Code analysieren lassen (model.py, meta_model.py, simple_report.py)
- [ ] Sample-Dateien analysieren lassen
- [ ] requirements.txt prüfen lassen
- [ ] Branch `feature-webapp` anlegen

---

### Phase 2 – Django Grundgerüst
- [ ] Django installieren
- [ ] Django Projekt aufsetzen (`config/`)
- [ ] Apps anlegen (szenarien, berechnung, auswertung, export)
- [ ] PostgreSQL Datenbank verbinden
- [ ] Bootstrap 5 Grundlayout bauen (`base.html`)
- [ ] Navigation zwischen Seiten einrichten
- [ ] Lokaler Test – läuft die Seite?
- [ ] Commit & Push zu GitHub

---

### Phase 3 – Szenarien & FAIR Parameter
- [ ] Datenbankmodell für Szenarien erstellen
- [ ] Formular für FAIR Parameter bauen
- [ ] Schieber (Slider) für Unsicherheit einbauen
- [ ] Szenario speichern in PostgreSQL
- [ ] Szenario laden & bearbeiten
- [ ] Szenario löschen
- [ ] Dashboard mit Szenario-Übersicht
- [ ] Lokaler Test
- [ ] Commit & Push → Branch `feature-szenarien` mergen in `main`

---

### Phase 4 – PyFair Anbindung & Berechnung
- [ ] PyFair als Engine einbinden
- [ ] Monte Carlo Simulation starten
- [ ] Live-Fortschrittsanzeige während Simulation
- [ ] Ergebnisse in PostgreSQL als JSON speichern
- [ ] Mehrere Szenarien gleichzeitig berechnen
- [ ] Lokaler Test
- [ ] Commit & Push → Branch `feature-berechnung` mergen in `main`

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
- [ ] Lokaler Test
- [ ] Commit & Push → Branch `feature-admin` mergen in `main`

---

### Phase 8 – Deployment auf IONOS VPS
- [ ] Per SSH auf VPS verbinden
- [ ] Ubuntu aktualisieren
- [ ] Python & pip installieren
- [ ] PostgreSQL auf VPS installieren & einrichten
- [ ] Nginx installieren & konfigurieren
- [ ] Gunicorn installieren & konfigurieren
- [ ] GitHub Repository auf VPS klonen
- [ ] Umgebungsvariablen setzen
- [ ] SSL Zertifikat (Let's Encrypt) einrichten
- [ ] Domain `fair.neoprehn.de` verbinden
- [ ] Finaler Test auf neoprehn.de

---

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
| `fair/model/model.py` | FairModel Kernlogik |
| `fair/model/meta_model.py` | Mehrere Szenarien kombinieren |
| `fair/report/simple_report.py` | Bestehende Report-Logik |
| `fair/utility/beta_pert.py` | Wahrscheinlichkeitsverteilung |
| `requirements.txt` | Bestehende Abhängigkeiten |
| `sample/` | Beispiele wie PyFair genutzt wird |
