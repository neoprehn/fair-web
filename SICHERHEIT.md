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

- [ ] **Registrierungs-Policy** entscheiden: aktuell kann sich jeder ein
      Betrachter-Konto anlegen und sieht (geteilter Arbeitsbereich) alle
      Szenarien. Optionen: Self-Registration aus, Admin-Freigabe, oder
      E-Mail-Domain-Allowlist. (bewusst zurückgestellt)
- [ ] **Brute-Force-Schutz** für Login/Registrierung/`/admin/`
      (z. B. `django-axes`) oder Admin per IP am Proxy einschränken.
- [ ] **Content-Security-Policy (CSP):** derzeit viele Inline-Styles/-Skripte
      und CDN-Einbindungen (Bootstrap/Plotly). Eine wirksame CSP braucht
      Nonces/Refactoring – als eigener Slice (sonst nur zahnlos mit
      `unsafe-inline`).
- [ ] **Dependency-Audit** (`pip-audit` / `pip list --outdated`) und
      Aktualisierungen einplanen.
