"""Stellt Währungssymbol + Locale für alle Templates bereit."""


def waehrung(request):
    try:
        from .models import AppKonfiguration
        k = AppKonfiguration.load()
        return {
            "waehrung_symbol": k.symbol,
            "waehrung_locale": k.js_locale,
            "waehrung": k.waehrung,
        }
    except Exception:  # noqa: BLE001
        return {"waehrung_symbol": "€", "waehrung_locale": "de-DE", "waehrung": "EUR"}
