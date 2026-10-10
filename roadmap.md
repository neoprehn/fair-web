# fair-web – Roadmap

Web-App (Django) rund um den FAIR-Risiko-Monte-Carlo-Simulator **pyfair**.
Live: **https://fair.neoprehn.de**. Diese Datei zeigt Kompakt-Zusammenfassung +
Arbeitskontext, unten die **offenen** Punkte. Erledigtes (Phasen 1–9,
RTD-Doku-Grundausbau) steht in `ROADMAP-ARCHIV.md`. **Export wurde bewusst
ganz ans Ende gestellt.**

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

### Als Nächstes → Phase 9 – Sicherheit (Rest) (@neoprehn)
Phase 9 ist bis auf einen Punkt komplett erledigt (siehe `ROADMAP-ARCHIV.md`).
Offen ist nur noch:
- [~] Deploy auf Sicherheits-Design-Fehler prüfen: **CSP** (Content-Security-
      Policy) noch nicht umgesetzt (bewusst zurückgestellt; Security-Header,
      HTTPS-Härtung, Registrierungs-Policy, Brute-Force-Schutz und
      Dependency-Audit sind bereits live – siehe `SICHERHEIT.md`)

### Danach → Phase 10 – FAOR + FAIR-CAM (@neoprehn)
- [ ] Einbindung der FAOR-Logik in die Webseite
- [~] Einbindung von FAIR-CAM (Library: `pyfair-cam`, eigenes Repo unter
      `Entwicklung/pyfair-cam`, Rechenkern+Report Phasen 0–4 fertig). Web-Seite:
      eigene `apps.cam`-App mit Top-Level-Menüpunkt „FAIR-CAM", Übersicht +
      volles Eingabeformular (vorbelegt mit dem Ransomware-Beispiel) stehen
      (= pyfair-cam-ROADMAP Phase 5.1). Noch offen: Berechnen/Report-Einbettung
      (pyfair-cam-ROADMAP Phase 5.2+) – siehe dort für den Feinschnitt.
- [ ] Wenn ein Modell schon simuliert wurde: Ergebnisse in der Eingabeseite
      anzeigen + automatisch nachberechnen bei Änderung („Neu berechnen")
- [ ] Historie der Simulationen (aufklappbar, Verzeichnis-artig, neueste oben)
- [ ] Schnittpunkte LEC×Toleranz bzw. mehrere LECs×Toleranz als Tabelle
      (Vorbild: `fair/results/Laptop_neu.html`)
- [x] Punkte-Streudiagramm primäre/sekundäre Verluste (Ergebnisseite, `apps/berechnung/services.py::_streudiagramm`)
- [x] Szenario-Kategorie (Cluster) direkt im Szenario-Formular zuordenbar (bisher nur andersherum)
- [x] C/I/A-Kennzeichnung je Szenario (Mehrfachauswahl, `Szenario.cia`) inkl. Anzeige in
      Detail-/Ergebnisseite
- [x] Szenario-Name/-Beschreibung als Header über den Ergebnissen (`berechnung/lauf.html`,
      bisher nur Breadcrumb)
- [x] Ergebnis-Baum: nicht verwendete Knoten (z. B. CF/PoA bei direkt eingegebenem TEF) komplett
      ausgeblendet statt nur abgedunkelt (war im Dark-Theme praktisch unsichtbar)
- [ ] Lokaler Test · Commit & Push → `feature-…` mergen in `main`

### LM-Seite – Aufschlüsselung von PL/SL (Slices, @neoprehn)

`Szenario.lm_modus` steuert, wie Primary/Secondary Loss modelliert werden – elementweise
Monte-Carlo-Aggregation in `apps/berechnung/services.py::simuliere`, taxonomie-agnostisch über
`Szenario.verlust_komponenten()`.

- [x] Slice 1: Grundgerüst + **6 Forms of Loss** (`VerlustFormEingabe`, Modus `formen`)
- [x] Slice 2: **FAIR-MAM-Fragebogen** (`VerlustMamEingabe`, Modus `fair_mam`) – 10 Module/26
      Kategorien, Primary/Secondary je Kategorie fest vorgegeben (→ PL/SL)
- [x] Slice 3: **Aggregationsmodus-Umschalter** (`aggregations_modus`) – "Elementweise" (echte
      Monte-Carlo-Faltung, bisheriges Verhalten) vs. "Kennwerte" (Mittelwert+Varianz je Form/
      Kategorie exakt addieren, per Moment-Matching in eine Lognormalverteilung für PL/SL
      übersetzt – schneller, aber Näherung an die Form der Summenverteilung)
- [x] Slice 4: **SLEF-Granularität** (`slef_modus`) – behebt, dass SLEF (Secondary Loss Event
      Frequency) bei aufgeschlüsseltem SL bisher komplett ignoriert wurde (SL = Formen-Summe, als
      gälte SLEF=1). "Gemeinsam" nutzt den wiederverwendeten Baum-Knoten SLEF als ein
      Multiplikator auf die gesamte SL-Formen-Summe; "Individuell" gibt jeder SL-Form/-Kategorie
      eine eigene SLEF-Verteilung (`VerlustFormSlef`/`VerlustMamSlef`). Damit ist die
      LM-Aufschlüsselungs-Serie (Slices 1–4) vollständig abgeschlossen.

### Deutsch/Englisch-Schalter für UI-Beschriftungen (@neoprehn)

Rein clientseitiger Umschalter (localStorage, `#lang-toggle` in `base.html`, wie der Dark/Light-
Toggle) – bewusst **getrennt** von Djangos translation/gettext und der bestehenden
`WaehrungLocaleMiddleware` (steuert nur das Zahlenformat, nicht die Sprache). Wörterbücher als
externe `static/js/i18n*.js`-Dateien (nicht inline – sonst tauchen berechtigungsabhängig
ausgeblendete Wörter trotzdem im HTML-Response auf), `data-i18n`/`data-i18n-title`/
`data-i18n-aria-label`-Attribute im Markup, `window.fairT(key)` für JS-generierten Text
(Plotly-Achsentitel/Legenden).

- [x] Infrastruktur (`static/js/i18n.js`) + Kernseiten: `base.html` (Navigation/Footer/Menü),
      `szenarien/dashboard.html`, `szenarien/detail.html`, `szenarien/form.html`,
      `berechnung/lauf.html`
- [ ] Vorbereitet, aber noch nicht angebunden: DeepL-API-Key in der Admin-Konfiguration
      (`AppKonfiguration.deepl_api_key`) für eine künftige Funktion, die Nutzerinhalte
      (Szenario-Name/-Beschreibung/-Annahmen) dynamisch übersetzt – anderer Mechanismus als
      dieser statische Label-Schalter
- [ ] Noch nicht übersetzt (zurückgestellt): Admin-Bereich, `apps.cam`-Templates,
      `vergleich_*.html`/`cluster_*.html`/`meta_lauf.html`, lange Erklärtexte/Tooltips
      (6-Forms-/FAIR-MAM-Infomodal-Texte, Risikotoleranz-Hilfetexte), die 32 dynamischen
      Loss-Form-/FAIR-MAM-Kategorie-Labels, Konten-/Login-Seiten

### RTD-Doku nachgezogen (`docs/bedienung.md` + `templates/hilfe.html`)

Nach Nachfrage aufgefallen: die komplette LM-Serie (Slices 1–4), die Zweig-Farben, die
5-Verbesserungen-Runde (C/I/A, Streudiagramm, Baum-Ausblenden) und der DE/EN-Schalter waren
nirgends dokumentiert – Roadmap wurde laufend gepflegt, RTD/In-App-Hilfe aber übersprungen
(Verstoß gegen die eigene "Phase fertig = Roadmap + RTD + Commit/Push"-Regel). Beide Dateien
(RTD-Quelle und die inhaltsgleiche In-App-Hilfeseite) jetzt nachgezogen:
**Loss-Magnitude-Aufschlüsselung** (6 Forms of Loss/FAIR-MAM/Aggregations-/SLEF-Modus),
**Zweig-Farben** + ausgeblendete ungenutzte Knoten, **Streudiagramm**, **C/I/A-Kennzeichnung**,
Cluster-Korrektur (Zuordnung nur noch auf der Cluster-Seite), **DE/EN-Schalter** +
**DeepL-Vorbereitung**. pyfair-Engine-Kapitel (`modelle.md`/`eingaben.md`) bewusst nicht
angefasst – die Session-Arbeit war ausschließlich in fair-web, nicht im pyfair-Fork selbst.

### RTD zweisprachig (DE/EN) umgesetzt (@neoprehn)

Angefragt 2026-10-10 – zieht den ursprünglich für "ganz zuletzt" geplanten Big-Bang
(siehe `ROADMAP-ARCHIV.md`-Historie bzw. den jetzt überholten Punkt unten) bewusst vor.
Technik: [mkdocs-static-i18n](https://github.com/ultrabug/mkdocs-static-i18n) (`docs_structure:
suffix`), Deutsch bleibt Default (`index.md` etc.), Englisch als `*.en.md`-Geschwisterdateien.

- [x] Alle 14 bestehenden `docs/*.md`-Seiten ins Englische übersetzt (`*.en.md`), inkl.
      interner Querverweis-Anker (`modelle.md#faktornamen-abkurzungen` →
      `#factor-names-abbreviations` usw. – per Skript gegenprüft, keine toten Anker)
- [x] `mkdocs.yml`: `i18n`-Plugin + `nav_translations` für die Sidebar, Theme-Locale wird pro
      Sprachbuild automatisch umgeschaltet (`readthedocs`-Theme wird vom Plugin nativ unterstützt)
- [x] Sprachumschalter (Deutsch/English) oben in der Seitenleiste neben der Suche –
      eigener `docs/overrides/base.html` (Theme-Template **kopiert statt erweitert**, da
      `{% extends "base.html" %}` aus einem `custom_dir` auf sich selbst rekursiert), nutzt
      `page.file.alternates` für die Verlinkung zur übersetzten Version derselben Seite
- [x] Lesebereich verbreitert: `.wy-nav-content` von 800px auf 1100px (`docs/extra.css`)
- [x] `docs/requirements.txt`: `mkdocs-static-i18n` ergänzt (für den RTD-Build)
- **Policy-Änderung:** ab sofort werden **alle künftigen** Doku-Änderungen (RTD + In-App-Hilfe)
  direkt zweisprachig vorgenommen – ersetzt die alte "DE laufend / EN Big Bang am Ende"-Regel
  (siehe Hinweis oben bei "Eigene ReadTheDocs-Dokumentationssite").

### Später — Geführter Szenario-Dialog (Name noch offen)

Angefragt 2026-09-15. Ziel: ein Zwischendialog, der ein neues FAIR-Szenario Schritt für
Schritt mit allen Werten füllt (statt der aktuellen "alles auf einer Seite"-Eingabe direkt im
Baum) — Arbeitstitel bisher nur "neues Szenario geführter Dialog", kürzerer Name noch zu finden.
Bewusst **zurückgestellt bis nach** der LM-Seite/6-Forms-of-Loss-Überarbeitung (siehe
`ROADMAP-ARCHIV.md`-Vorlauf bzw. den aktuellen Slice dazu) — der geführte Dialog soll die dann
neue LM-Struktur (PL/SL-Aufschlüsselung nach Loss-Formen) mit abfragen, macht also erst danach
Sinn.
- [ ] Konzept/Screens für den Dialog entwerfen, sobald die LM-Struktur steht
- [ ] Kürzeren Arbeitsnamen festlegen

### Ganz zuletzt

#### Eigene ReadTheDocs-Dokumentationssite
Grundausbau + Live-Betrieb bereits erledigt (siehe `ROADMAP-ARCHIV.md`). Offen:
- [ ] Beispiele/Tutorials ausbauen (optional, laufend)

> **Sprachen-Policy (aktualisiert 2026-10-10):** Die ursprüngliche Policy ("DE
> laufend, EN erst ganz am Ende als Big Bang") wurde auf Wunsch vorgezogen und
> **ersetzt** – siehe [RTD zweisprachig (DE/EN) umgesetzt](#rtd-zweisprachig-deen-umgesetzt-neoprehn)
> unten. Ab sofort gilt: **jede** Doku-Änderung (RTD + In-App-Hilfe) wird **im
> selben Commit sowohl deutsch als auch englisch** nachgezogen – kein
> getrenntes "Big Bang"-Projekt mehr am Ende.

#### Export
- [ ] Excel-Export (openpyxl)
- [ ] PPT-Bericht (python-pptx)
- [ ] PDF-Bericht
- [ ] Grafiken in den Export einbetten
- [ ] Download-Button in der Oberfläche
- [ ] **Batch-API: Excel-Vorlage mit mehreren FAIR-Szenarien hochladen, serverseitig
      durchsimulieren, ausgefüllte Ergebnis-Excel(s) zurückgeben** (angefragt
      2026-07-28). Eine Zeile = ein Szenario (Name + Faktor-Parameter je nach
      gewähltem Schnitt); Antwort = Excel mit angehängten Ergebnis-Spalten
      (ALE, Median, VaR 95/99, ggf. LEC-Kurzfassung). Format/Validierung noch
      nicht festgelegt. Soll später auch für FAIR-CAM gebaut werden – siehe
      `pyfair-cam/ROADMAP.md` Phase 5.6 (bewusst erst nach diesem FAIR-Teil,
      damit sich ein wiederverwendbares Muster zeigt statt zweimal Ad-hoc).
- [ ] Lokaler Test · Commit & Push → `feature-export` mergen in `main`

---

### ~~Allerletzter Schritt — Englische Doku (Big Bang)~~ — erledigt, vorgezogen

Ursprünglich für ganz zum Schluss geplant, auf Wunsch am 2026-10-10 vorgezogen und
umgesetzt – siehe [RTD zweisprachig (DE/EN) umgesetzt](#rtd-zweisprachig-deen-umgesetzt-neoprehn)
weiter oben. Offen bleibt nur noch laufende Pflege: jede künftige Doku-Änderung direkt in
beiden Sprachen.
