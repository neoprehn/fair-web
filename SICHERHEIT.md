# Sicherheit – Status & Checkliste

Begleitet das Roadmap-Thema „Deploy auf Sicherheits-Design-Fehler prüfen" (Phase 9).

## Im Code umgesetzt (greift automatisch)

- **Antwort-Header immer aktiv:** `X-Content-Type-Options: nosniff`,
  `Referrer-Policy: same-origin`, `X-Frame-Options: DENY`.
- **HTTPS-Härtung – standardmäßig AUS** (`SECURE_HTTPS`, Default `False`).
  Aktiviert `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`,
  `CSRF_COOKIE_SECURE`, **HSTS** (1 Jahr, inkl. Subdomains).
  > ⚠️ **Erst aktivieren, wenn der Proxy `X-Forwarded-Proto` korrekt
  > weitergibt** (`request.is_secure()` == True). Sonst Redirect-Schleife
  > (`SSL_REDIRECT`) bzw. nie gesetzte Secure-Cookies. Genau das ist beim
  > ersten Versuch passiert → Hotfix: Default jetzt `False`.

### HTTPS-Härtung sicher einschalten (wenn der Proxy passt)
1. Auf dem Server prüfen, ob Django HTTPS erkennt – z. B. temporär im
   Django-Shell/Logging `request.is_secure()` bzw. den ankommenden Header
   `X-Forwarded-Proto` kontrollieren (Plesk/nginx→gunicorn). Ggf. nginx so
   konfigurieren, dass `proxy_set_header X-Forwarded-Proto $scheme;` gesetzt
   und bis gunicorn durchgereicht wird.
2. Erst dann `SECURE_HTTPS=True` in die `.env` setzen und neu deployen.
3. Verifizieren: `curl -I https://fair.neoprehn.de/` zeigt
   `Strict-Transport-Security`, Login funktioniert, **keine** Redirect-Schleife.
- Bereits vorhanden: TLS-Proxy-Header (`SECURE_PROXY_SSL_HEADER`),
  `CSRF_TRUSTED_ORIGINS`, App-weite **Login-Pflicht**, CSRF-/Clickjacking-
  Middleware, rollenbasierte Rechte (403) + UI-Gating.
- Lokal/Tests bleiben unberührt (`SECURE_HTTPS=False`).

## Auf dem Server prüfen/erledigen (kann ich von hier nicht einsehen)

- [ ] **`.env`: `DEBUG=False`** (sonst greift die HTTPS-Härtung NICHT und
      Fehlerseiten verraten Interna). Prüfen mit:
      `python manage.py check --deploy` (im Server-venv, mit Prod-`.env`).
- [ ] **Starker `SECRET_KEY`** (≥ 50 zufällige Zeichen, nicht der Default).
      Neu erzeugen: `python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"`.
- [ ] **`ALLOWED_HOSTS`** auf `fair.neoprehn.de` (kein `*`).
- [ ] **`.env`-Dateirechte** restriktiv (`chmod 600`, nur der App-User).
- [ ] **MariaDB** nur lokal erreichbar (kein öffentlicher 3306-Port),
      eigener DB-User mit minimalen Rechten.
- [ ] **HTTPS/HSTS am Proxy (Plesk)** aktiv; Zertifikat-Erneuerung automatisch.
- [ ] **GitHub-Actions-Secrets / Deploy-Key** mit minimalem Scope; `main`
      möglichst per Branch-Schutz absichern.
- [ ] **Backups** der MariaDB regelmäßig + Restore getestet.
- [ ] Verifizieren der Header live: `curl -I https://fair.neoprehn.de/accounts/login/`
      (HSTS, X-Frame-Options, nosniff, Referrer-Policy sichtbar).

## Empfehlungen / noch offen (eigene Slices)

- [x] **Registrierungs-Policy** – "Admin-Freigabe": Self-Registration bleibt
      aktiv, neue Konten starten aber mit `is_active=False` (Gruppe
      Betrachter wird trotzdem zugewiesen). Ein Administrator muss das Konto
      im Django-Admin aktivieren, bevor ein Login möglich ist.
- [x] **Brute-Force-Schutz** (`django-axes`): sperrt nach
      `AXES_FAILURE_LIMIT=5` Fehlversuchen (Username+IP) für
      `AXES_COOLOFF_TIME=1` Stunde – greift für `/accounts/login/` und
      `/admin/login/` gleichermaßen (gleicher Auth-Backend-Stack).
- [ ] **Content-Security-Policy (CSP):** derzeit viele Inline-Styles/-Skripte
      und CDN-Einbindungen (Bootstrap/Plotly). Eine wirksame CSP braucht
      Nonces/Refactoring – als eigener Slice (sonst nur zahnlos mit
      `unsafe-inline`).
- [x] **Dependency-Audit** (`pip-audit`) – siehe Abschnitt
      „Dependency-Audit" unten.

## Dependency-Audit (Stand 2026-06-12)

`pip-audit` über die installierten Pakete findet 4 Funde, alle in der
transitiven Abhängigkeit von `litellm` (optionaler KI-Assistent):

| Paket | Version | CVE | Fix-Version | Relevanz für fair-web |
|---|---|---|---|---|
| litellm | 1.83.7 | CVE-2026-40217 | 1.83.10 | Betrifft nur den `litellm`-**Proxy**-Endpoint `/guardrails/test_custom_code` (Sandbox-Escape, braucht Proxy-Admin-Credential). fair-web nutzt `litellm` nur als Library (`litellm.completion(...)`), kein Proxy-Server läuft. **Nicht ausnutzbar.** |
| aiohttp | 3.13.5 | CVE-2026-34993 | 3.14.0 | Betrifft `CookieJar.load()` mit nicht vertrauenswürdigen Dateien. Wird von fair-web/litellm nicht aufgerufen. **Nicht ausnutzbar.** |
| aiohttp | 3.13.5 | CVE-2026-47265 | 3.14.0 | Betrifft Requests mit explizitem `cookies`-Parameter bei Cross-Origin-Redirects. fair-web/litellm setzt keine Cookies auf KI-Provider-Requests (Auth per API-Key-Header). **Geringes Risiko.** |
| python-dotenv | 1.0.1 | CVE-2026-28684 | 1.2.2 | Betrifft `set_key()`/`unset_key()` (Symlink-Angriff beim Schreiben von `.env`). fair-web ruft diese Funktionen nicht auf, nur `load_dotenv()` zum Lesen. **Nicht ausnutzbar.** |

**Maßnahme:** `litellm>=1.83.10` (Fix für CVE-2026-40217 und transitiv
neueres `aiohttp`) setzt `Python <3.14` voraus – das Projekt läuft
aktuell auf **Python 3.14**. Ein hartes Pin auf neuere `aiohttp`-/
`python-dotenv`-Versionen erzeugt einen Konflikt mit `litellm`s exakten
Pins (`aiohttp==3.13.5`, `python-dotenv==1.0.1`). Da keiner der Funde im
Nutzungskontext von fair-web ausnutzbar ist, bewusst zurückgestellt bis
`litellm` Python 3.14 unterstützt bzw. die Pins lockert. Bei jedem
größeren `litellm`-Update erneut mit `pip-audit` prüfen.
