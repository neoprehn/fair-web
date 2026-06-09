from django.contrib import admin

from .models import Angreifertyp, Cluster, FaktorEingabe, Szenario, Vergleich


@admin.register(Cluster)
class ClusterAdmin(admin.ModelAdmin):
    list_display = ("name", "geaendert_am")
    filter_horizontal = ("szenarien",)
    search_fields = ("name",)


@admin.register(Angreifertyp)
class AngreifertypAdmin(admin.ModelAdmin):
    list_display = ("name", "low", "mode", "high", "reihenfolge")
    list_editable = ("low", "mode", "high", "reihenfolge")
    ordering = ("reihenfolge", "name")


class FaktorEingabeInline(admin.TabularInline):
    model = FaktorEingabe
    extra = 1


@admin.register(Szenario)
class SzenarioAdmin(admin.ModelAdmin):
    list_display = ("name", "n_simulations", "random_seed", "geaendert_am")
    search_fields = ("name", "beschreibung")
    inlines = [FaktorEingabeInline]


@admin.register(FaktorEingabe)
class FaktorEingabeAdmin(admin.ModelAdmin):
    list_display = ("szenario", "faktor", "verteilung")
    list_filter = ("faktor", "verteilung")


@admin.register(Vergleich)
class VergleichAdmin(admin.ModelAdmin):
    list_display = ("name", "referenz_szenario", "n_simulations", "geaendert_am")
    filter_horizontal = ("szenarien",)
    search_fields = ("name",)
