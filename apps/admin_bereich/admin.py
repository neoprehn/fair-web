from django.contrib import admin

from .forms import AppKonfigurationForm
from .models import AppKonfiguration


@admin.register(AppKonfiguration)
class AppKonfigurationAdmin(admin.ModelAdmin):
    """Singleton-Konfiguration: kein Hinzufügen/Löschen, nur Bearbeiten.

    Die Unternehmens-Risikotoleranz wird über einen eigenen Editor im
    Change-Form-Template erfasst (gleiche Logik wie in der Szenarioeingabe)
    und in ``save_model`` aus den ``rt_*``-POST-Feldern zusammengebaut.
    """

    form = AppKonfigurationForm
    change_form_template = "admin/admin_bereich/appkonfiguration/change_form.html"
    fieldsets = (
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

    def save_model(self, request, obj, form, change):
        from apps.szenarien.views import risikotoleranz_aus_post

        obj.unternehmens_risikotoleranz = risikotoleranz_aus_post(request.POST)
        super().save_model(request, obj, form, change)
