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
- [x] PostgreSQL Datenbank verbinden
- [x] Bootstrap 5 Grundlayout bauen (`base.html`)
- [x] Navigation zwischen Seiten einrichten
- [ ] Lokaler Test – läuft die Seite?
- [x] Commit & Push zu GitHub

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
| `pyfair/model/model.py` | FairModel Kernlogik |
| `pyfair/model/meta_model.py` | Mehrere Szenarien kombinieren |
| `pyfair/report/simple_report.py` | Bestehende Report-Logik |
| `pyfair/utility/beta_pert.py` | Wahrscheinlichkeitsverteilung |
| `requirements.txt` | Bestehende Abhängigkeiten |
| `sample/` | Beispiele wie PyFair genutzt wird |
