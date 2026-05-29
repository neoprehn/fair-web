from django.contrib import admin

from .models import MetaLauf, Simulationslauf


@admin.register(Simulationslauf)
class SimulationslaufAdmin(admin.ModelAdmin):
    list_display = ("id", "szenario", "status", "fortschritt", "erstellt_am")
    list_filter = ("status",)
    readonly_fields = ("ergebnis", "erstellt_am", "aktualisiert_am")


@admin.register(MetaLauf)
class MetaLaufAdmin(admin.ModelAdmin):
    list_display = ("id", "status", "fortschritt", "erstellt_am")
    list_filter = ("status",)
    filter_horizontal = ("szenarien",)
    readonly_fields = ("ergebnis", "erstellt_am", "aktualisiert_am")
