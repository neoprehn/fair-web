# fair-web

Django-Webapp für FAIR Monte Carlo Risk-Simulationen auf Basis von PyFair.

PyFair und fair-web liegen bewusst getrennt:

```
Entwicklung/
├── pyfair/         ← PyFair (Simulations-Engine, eigenes Repo)
└── fair-web/       ← diese Django-Webapp (eigenes Repo)
```

## Phase 1 — Grundgerüst

Aktueller Stand: Django 5.2 LTS Scaffold mit Bootstrap 5, MariaDB und vorbereiteten Apps für die nächsten Feature-Branches.

## Setup (lokal, Windows / VS Code)

1. **MariaDB einrichten**
   ```sql
   -- In der MariaDB-Konsole (mariadb -u root -p):
   CREATE DATABASE fairweb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE USER 'fairweb'@'localhost' IDENTIFIED BY 'fairweb';
   GRANT ALL PRIVILEGES ON fairweb.* TO 'fairweb'@'localhost';
   FLUSH PRIVILEGES;
   ```

2. **Virtualenv + Dependencies**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   pip install -e ..\pyfair        # PyFair als lokales Paket (Nachbarordner, setup.py liegt im pyfair-Root)
   ```

3. **.env anlegen**
   ```powershell
   Copy-Item .env.example .env
   # SECRET_KEY ändern, DATABASE_URL prüfen
   ```

4. **Migrationen + Server starten**
   ```powershell
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py runserver
   ```

   Aufrufen: http://127.0.0.1:8000/

## Projektstruktur

```
fair-web/
├── config/             # Django Settings, URLs, WSGI
├── apps/
│   ├── szenarien/      # FAIR Szenarien (Phase 2)
│   ├── berechnung/     # PyFair Anbindung (Phase 2)
│   ├── auswertung/     # Plotly Charts, LEC (Phase 3)
│   ├── export/         # Excel / PPT (Phase 4)
│   └── admin_bereich/  # Einstellungen (Phase 4)
├── templates/          # HTML mit Bootstrap 5
├── static/
└── media/
```

## Branches

- `main` — stabil, läuft auf VPS
- `feature-webapp` — Grundgerüst (dieser Branch)
- `feature-szenarien` — FAIR-Parameter Eingabe
- `feature-grafiken` — Plotly LEC-Animation
- `feature-export` — Excel / PPT Export
