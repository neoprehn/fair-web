**Pflicht: Knowledge-Graph zuerst.** Für jede Code-Exploration in diesem
Workspace (Funktionen/Klassen/Routen finden, Aufrufketten, Architektur- und
Auswirkungsfragen) MUSST du zuerst die `codebase-memory-mcp`-Tools nutzen
(`search_graph`, `trace_path`, `get_code_snippet`, `query_graph`,
`get_architecture`, `search_code`) — nicht Grep/Read als ersten Reflex.
Grep/Read/Glob bleiben für Text, Configs, Nicht-Code-Dateien und als Ergänzung,
wenn der Graph keine Antwort liefert. Projektname beim Tool-Aufruf immer
mitgeben: `fair` (Rechenkern), `pyfair-cam` (CAM), `fair-web` (Frontend).

Lies bitte:

    Als allererstes: git pull (bzw. mind. git fetch + Abgleich mit origin/main) — es gibt seit
    2026-07-12 zwei Arbeitsgeräte (Heim-Rechner + mobiler Laptop für Zugfahrten), der lokale Stand
    kann also hinter dem sein, was vom jeweils anderen Gerät gepusht wurde. 
    
    Nach dem Pull den Graph-Index auffrischen: index_repository für das aktuelle
    Repo aufrufen (der Pull kann Änderungen vom anderen Gerät gebracht haben,
    die der lokale Index noch nicht kennt), danach index_status prüfen (siehe
    Pflicht-Regel oben zur Graph-Nutzung selbst).

    Erst danach die folgenden Dateien lesen, sonst ggf. veralteter Stand:
    roadmap.md — „Stand" + offene Punkte mit [ ]/[~]/[x] (das ist der eigentliche Übergabepunkt),
    ROADMAP-ARCHIV.md — was erledigt ist,
    Git-Historie — jeder Commit beschreibt einen Schritt,
    das persistente Memory (MEMORY.md + memory/*.md) — wird in jede neue Session geladen,
    CLAUDE.md — Projektregeln.

    Subagenten in .claude/agents/ (werden automatisch beim Session-Start erkannt, kein
    manuelles Laden nötig): security-review (Django-Sicherheitscheck gegen SICHERHEIT.md),
    testing (pytest-django + optional Playwright gegen runserver), docs-i18n-sync (DE/EN-
    Parität docs/*.md+*.en.md, mkdocs.yml/.en.yml, static/js/i18n*.js). Bei Code-Änderungen vor
    jedem Commit/Push als Kette aufrufen: security-review -> testing -> docs-i18n-sync (letzterer
    nur relevant, wenn Doku/i18n betroffen sind).

Was steht als nächstes an?

