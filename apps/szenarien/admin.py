from django.contrib import admin

from .models import FaktorEingabe, Szenario


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
