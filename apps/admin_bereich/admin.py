from django.contrib import admin

from .models import AppKonfiguration


@admin.register(AppKonfiguration)
class AppKonfigurationAdmin(admin.ModelAdmin):
    """Singleton-Konfiguration: kein Hinzufügen/Löschen, nur Bearbeiten."""

    fieldsets = (
        ("Standard-Seed", {"fields": ("standard_seed", "seed_global")}),
        ("Simulationsanzahl", {"fields": ("standard_n_simulations", "n_simulations_global")}),
        ("Unternehmens-Risikotoleranz", {"fields": ("unternehmens_risikotoleranz", "risikotoleranz_global")}),
    )
    readonly_fields = ("geaendert_am",)

    def has_add_permission(self, request):
        return not AppKonfiguration.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
