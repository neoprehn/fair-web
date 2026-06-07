# fair-web – Roadmap (neu)

Web-App (Django) rund um den FAIR-Risiko-Monte-Carlo-Simulator **pyfair**.
Live: **https://fair.neoprehn.de**. Diese Datei ersetzt die alte `roadmap.md`:
oben eine kompakte Zusammenfassung des Erledigten + Arbeitskontext, unten die
**offenen** Punkte. **Export wurde bewusst ganz ans Ende gestellt.**

---

## 1. Zusammenfassung – was steht (Phasen 1–7, alles live)

- **Grundgerüst (Ph. 1–2):** Django-Projekt `config/`, Apps `szenarien`,
  `berechnung`, `auswertung`, `export`, `admin_bereich`, `konten`. Bootstrap 5,
  Dark-Theme in `base.html`.
- **Szenarien & FAIR-Parameter (Ph. 3):** `Szenario` + `FaktorEingabe`.
  FAIR-Baum mit 12 Knoten (`apps/szenarien/fair_tree.py`), pro Knoten Verteilung
  wählbar (PERT/Normal/Konstant/Poisson/Beta/Lognormal). Unsicherheits-Slider
  (5 Konfidenzstufen, `fair_confidence.py`). CRUD + Dashboard.
- **pyfair-Anbindung (Ph. 4):** `apps/berechnung/services.py` ist die Engine
  (`simuliere`, `simuliere_meta`, `simuliere_vorschau`). MC-Lauf im
  Hintergrund-Thread (Variante A) + AJAX-Fortschritt. Ergebnis als JSON auf
  `Simulationslauf.ergebnis` (Kennzahlen, LEC, Knoten-Stats, Histogramme).
  Mehr-Szenarien-Lauf via `FairMetaModel` (`MetaLauf`).
- **FAIR-Baum-UI (Ph. 4b):** klickbarer Eingabe-Baum (auffalten), interaktives
  SVG, Ergebnis-Baum (Eingabe = Sky-Blau, berechnet = Grün).
- **Grafiken & Auswertung (Ph. 5 + 5b):** Plotly-LEC (log-Achse, P90 bei ¾,
  animiert), Risikotoleranz-Overlay (**rot durchgezogen**), Schnittpunkt
  LEC×Toleranz (Marker + Tabelle), **VaR** 10/20/50/80/90/95/99, SVG-Tooltips,
  Knoten-Detailtabelle (…/P90/P95/Max), Histogramme (Verteilung + Häufigkeit),
  **Live-LEC-Vorschau** auf der Eingabeseite (debounced AJAX `lec-vorschau`).
  **Vergleich**-Entität (gruppiert Szenarien) mit **Compare↔Add**-Umschalter;
  Referenz-Szenario liefert die Toleranzkurve + Schnittpunkte je Szenario-LEC.
- **Deployment (Ph. 6, war Ph. 8):** IONOS-VPS, Plesk→gunicorn (systemd
  `pyfair`), MariaDB, HTTPS. CI/CD via GitHub Actions (`deploy.yml`): bei Push
  auf `main` → `git reset --hard` + `migrate` + `collectstatic` + Restart.
- **Admin-Bereich (Ph. 7):**
  - Django-Admin (Branding „fair-web – Verwaltung", „← Zur Startseite").
  - **`AppKonfiguration`** (Singleton, `apps/admin_bereich/`): globaler
    Standard-Seed, Standard-Simulationsanzahl, **Unternehmens-Risikotoleranz**
    (mit Editor), **Währung €/$**, **Konfidenz-Vorschlagswerte** (5×4-Editor).
    „Global"-Schalter → Wert in der Szenarioeingabe „nur lesend" + beim
    Speichern erzwungen. Konfidenz-Edits steuern **Anzeige UND Berechnung**
    (`to_fair_kwargs` gibt expliziten gamma/sigma/range/k an pyfair).
  - **Hell/Dunkel-Schalter** (Navbar, `data-bs-theme`, CSS-Variablen,
    localStorage; Charts theme-abhängig via `window.fairChartTxt/Grid`).
  - **€/$-Schalter** (global): Locale-Middleware tauscht Separatoren
    (de 1.234,56 ↔ en 1,234.56), Context-Processor liefert `waehrung_symbol`
    /`waehrung_locale`; JS nutzt `window.fairLocale/fairWaehrung`.
  - **Berechtigungskonzept** (App `konten`): App-weite **Login-Pflicht**
    (`LoginRequiredMiddleware`), **Selbstregistrierung** (neue Nutzer → Gruppe
    **Betrachter**), Rollen **Betrachter/Analyst/Konfigurator/Administrator**
    (Gruppen via `post_migrate`, `apps/konten/gruppen.py`), **serverseitige
    Rechte** (403, `PermissionRequiredMixin`/`@permission_required`) + **UI-
    Gating** (`{% if perms.… %}`).

**Rollen-Kurzmatrix:** Betrachter = nur lesen · Analyst = Szenario/Vergleich
CRUD + Simulationen · Konfigurator = + App-Konfiguration/Angreifertypen (braucht
`is_staff` für den Admin) · Administrator = alles inkl. Benutzerverwaltung.

---

## 2. Arbeitskontext für Claude (so arbeiten wir hier)

**Repos (Parent: `…/Entwicklung/`):**
- `fair-web/` – diese Django-App (GitHub `neoprehn/fair-web`, Branch `main`).
- `fair/` – `pyfair` (GitHub `neoprehn/pyfair`), als editable im venv der App.
  → Jedes `git` mit explizitem `-C fair-web` bzw. `-C fair`. Nie vermischen.

**Lokale Umgebung:**
- venv: `fair-web/.venv`. Tests: `.venv/Scripts/python.exe -m pytest -q`
  (läuft gegen flüchtige SQLite via `conftest.py`; `client`-Fixture ist
  eingeloggter Superuser wegen Login-Pflicht).
- System-Check: `.venv/Scripts/python.exe manage.py check`.
- **Preview** (lokaler Server, eigene DB):
  `DATABASE_URL="sqlite:///preview_db.sqlite3" .venv/Scripts/python.exe manage.py runserver 127.0.0.1:8099 --noreload`
  – vorher ggf. `migrate`. Prüfung token-sparsam per `curl`/DOM-Grep, **nicht**
  per Screenshot. Admin-geschützte Seiten: per curl einloggen (CSRF-Token aus
  der Login-Seite ziehen). Preview-DB hat Test-Daten (Szenario, Vergleich,
  Superuser `prev`/`prev12345`).

**Slice-Workflow (pro Änderung):** lokal bauen → Preview/DOM prüfen → `pytest`
→ Commit auf `feature-…`-Branch → `git checkout main` → `merge --no-ff` →
`git push origin main` → Deploy via GitHub-Actions-API verifizieren
(`/repos/neoprehn/fair-web/actions/runs?branch=main`, auf `conclusion=success`
des passenden `head_sha`) → Live-Check (HTTP 200). **Migrationen** greifen
automatisch beim Deploy (`migrate` in `deploy.yml`).

**Konventionen:** Commits/Antworten **deutsch**, knapp; jede Tool-Aktion vorab
1–2 Sätze erklären. Commit-Message endet mit
`Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`. PRs/Merges `--no-ff`.
Token-effizient (Screenshots sparsam, Dateien nicht doppelt lesen).

**Wichtige Dateien:**
- `apps/szenarien/`: `models.py` (Szenario, FaktorEingabe, Vergleich,
  Angreifertyp; `to_fair_kwargs`, `risikotoleranz`), `fair_tree.py`,
  `fair_confidence.py` (`aktuelle_konfidenz_defaults`), `views.py`, `forms.py`.
- `apps/berechnung/`: `services.py` (Engine), `views.py` (LaufDetailView,
  MetaLaufDetailView, Start-Views; `toleranz_overlay`, `schnittpunkt`,
  `_knoten_tabelle`).
- `apps/admin_bereich/`: `models.py` (`AppKonfiguration`), `admin.py` +
  `change_form.html` (Risikotoleranz- & Konfidenz-Editor), `forms.py`,
  `middleware.py` (Währung-Locale), `context_processors.py`.
- `apps/konten/`: `middleware.py` (Login-Pflicht), `gruppen.py` (Rollen via
  post_migrate), `views.py`/`forms.py` (Registrierung), `urls.py`.
- Templates: `base.html` (Navbar/Theme/Währung-Globals), `templates/szenarien/`,
  `templates/berechnung/`, `templates/registration/`,
  `templates/admin/…/appkonfiguration/change_form.html`.

**Datenmodell-Stichworte:** `Szenario.risikotoleranz` JSON
(`{"type":"constant|curve|distribution",…}`); `AppKonfiguration` Singleton
(pk=1, `load()`); `MetaLauf.vergleich` FK; Roles als `auth.Group`.

---

## 3. Offene Arbeit

### Als Nächstes → Phase 9 – Sicherheit + Ideen (@neoprehn)
- [~] Deploy auf Sicherheits-Design-Fehler prüfen _(App-Härtung umgesetzt:
      Security-Header + HTTPS-Härtung in Prod; Server-/Policy-Checkliste in
      `SICHERHEIT.md` – offen: Registrierungs-Policy, Brute-Force-Schutz, CSP)_
- [x] Home-Bildschirm: Startseite unter `/` mit FAIR-Erklärung + interaktivem,
      klickbarem FAIR-Baum (Knoten-Erklärung ohne Simulation); Szenario-Dashboard
      nach `/szenarien/` verschoben (URL-Namen unverändert)
- [x] Bedienhilfe (In-App): Hilfeseite unter `/hilfe/` im Menü, mit
      Inhaltsverzeichnis + Abschnitten (Szenario/Faktoren/Verteilungen/
      Toleranz/Simulation/Vergleich/Klonen/Rollen/Einstellungen)
  - [ ] optional später: ausführliche Doku-Site (MkDocs/Sphinx im `docs/`-Ordner, ReadTheDocs-Stil)
- [ ] Szenariocluster (Szenarien gruppieren)
- [ ] Gemeinsame Berechnung: compare **oder** add als Ergebnis wählbar **und
      speicherbar** (eigener Reiter „Szenariovergleiche") – teils schon via
      `Vergleich` vorhanden, hier Persistenz/UX ausbauen
- [x] Eingabe von **Annahmen je Faktor** _(bereits umgesetzt: `FaktorEingabe.annahmen`,
      im Formular eingebbar, in der Szenario-Detailansicht je Faktor angezeigt)_
- [ ] Ausbaustufe: KI-Agent, der bei der Szenario-Formulierung hilft
- [ ] Lokaler Test · Commit & Push → `feature-…` mergen in `main`

### Danach → Phase 10 – FAOR + FAIR-CAM (@neoprehn)
- [ ] Einbindung der FAOR-Logik in die Webseite
- [ ] Einbindung von FAIR-CAM (ggf. als `pyfaircam` zu entwickeln)
- [ ] Wenn ein Modell schon simuliert wurde: Ergebnisse in der Eingabeseite
      anzeigen + automatisch nachberechnen bei Änderung („Neu berechnen")
- [ ] Historie der Simulationen (aufklappbar, Verzeichnis-artig, neueste oben)
- [ ] Schnittpunkte LEC×Toleranz bzw. mehrere LECs×Toleranz als Tabelle
      (Vorbild: `fair/results/Laptop_neu.html`)
- [ ] Punkte-Streudiagramm primäre/sekundäre Verluste (rot/blau, wie Laptop_neu)
- [ ] Lokaler Test · Commit & Push → `feature-…` mergen in `main`

### Ganz zuletzt → Phase Export
- [ ] Excel-Export (openpyxl)
- [ ] PPT-Bericht (python-pptx)
- [ ] PDF-Bericht
- [ ] Grafiken in den Export einbetten
- [ ] Download-Button in der Oberfläche
- [ ] Lokaler Test · Commit & Push → `feature-export` mergen in `main`
