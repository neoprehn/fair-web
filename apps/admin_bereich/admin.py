from django.contrib import admin

from .forms import AppKonfigurationForm
from .models import AppKonfiguration

# Konfidenzstufen (Code, Label) und Verteilungen (Code, Label, pyfair-Param).
KONFIDENZ_STUFEN = [
    ("very_low", "sehr niedrig"), ("low", "niedrig"), ("moderate", "mittel"),
    ("high", "hoch"), ("very_high", "sehr hoch"),
]
KONFIDENZ_DISTS = [
    ("pert", "PERT", "gamma"), ("lognormal", "Lognormal", "sigma"),
    ("poisson", "Poisson", "range"), ("beta", "Beta", "k"),
]


@admin.register(AppKonfiguration)
class AppKonfigurationAdmin(admin.ModelAdmin):
    """Singleton-Konfiguration: kein Hinzufügen/Löschen, nur Bearbeiten.

    Risikotoleranz und Konfidenz-Vorschlagswerte werden über eigene Editoren
    im Change-Form-Template erfasst und in ``save_model`` zusammengebaut.
    """

    form = AppKonfigurationForm
    change_form_template = "admin/admin_bereich/appkonfiguration/change_form.html"
    fieldsets = (
        ("Währung & Format", {"fields": ("waehrung",)}),
        ("Standard-Seed", {"fields": ("standard_seed", "seed_global")}),
        ("Simulationsanzahl", {"fields": ("standard_n_simulations", "n_simulations_global")}),
        ("Unternehmens-Risikotoleranz", {
            "fields": ("risikotoleranz_global", "geaendert_am"),
            "description": "Den Risikotoleranz-Editor findest du unterhalb der Felder.",
        }),
    )
    readonly_fields = ("geaendert_am",)

    def has_add_permission(self, request):
        return not AppKonfiguration.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def change_view(self, request, object_id, form_url="", extra_context=None):
        from apps.szenarien.fair_confidence import aktuelle_konfidenz_defaults

        defaults = aktuelle_konfidenz_defaults()
        rows = []
        for lvl, lbl in KONFIDENZ_STUFEN:
            cells = [
                {"name": f"kd_{lvl}_{dist}",
                 "value": defaults.get(lvl, {}).get(dist, {}).get(param, "")}
                for dist, _dl, param in KONFIDENZ_DISTS
            ]
            rows.append({"label": lbl, "cells": cells})
        extra_context = extra_context or {}
        extra_context["kd_rows"] = rows
        extra_context["kd_header"] = [f"{dl} ({param})" for _d, dl, param in KONFIDENZ_DISTS]
        return super().change_view(request, object_id, form_url, extra_context)

    def save_model(self, request, obj, form, change):
        from apps.szenarien.views import risikotoleranz_aus_post

        obj.unternehmens_risikotoleranz = risikotoleranz_aus_post(request.POST)
        obj.konfidenz_defaults = self._konfidenz_aus_post(request.POST)
        super().save_model(request, obj, form, change)

    @staticmethod
    def _konfidenz_aus_post(post):
        out = {}
        for lvl, _lbl in KONFIDENZ_STUFEN:
            out[lvl] = {}
            for dist, _dl, param in KONFIDENZ_DISTS:
                v = post.get(f"kd_{lvl}_{dist}", "")
                if v not in ("", None):
                    try:
                        out[lvl][dist] = {param: float(v)}
                    except ValueError:
                        pass
        return out
