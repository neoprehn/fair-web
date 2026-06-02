"""WSGI config for fair-web.

Produktion: nginx (TLS) → Apache → gunicorn (Unix-Socket). Über den
Apache-Hop kommt ``X-Forwarded-Proto`` nicht zuverlässig bei Django an, daher
würde ``request.is_secure()`` False liefern (Redirect-Schleife bei aktivem
SSL-Redirect). Da gunicorn ausschließlich hinter dem TLS-terminierenden Proxy
am Socket erreichbar ist, erzwingen wir das https-Schema – aber **nur**, wenn
die HTTPS-Härtung bewusst eingeschaltet ist (`SECURE_HTTPS=True`).
"""

import os

from django.core.wsgi import get_wsgi_application


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")


def _force_https_wrapper(app):
    from django.conf import settings

    def wrapped(environ, start_response):
        if getattr(settings, "SECURE_HTTPS", False):
            environ["HTTP_X_FORWARDED_PROTO"] = "https"
            environ["wsgi.url_scheme"] = "https"
        return app(environ, start_response)

    return wrapped


application = _force_https_wrapper(get_wsgi_application())
