from django.contrib import admin

from .models import CamControl, CamStage, CamSzenario, CamVerlustklasse


class CamControlInline(admin.StackedInline):
    model = CamControl
    extra = 0
    max_num = 1


class CamStageInline(admin.TabularInline):
    model = CamStage
    extra = 0


class CamVerlustklasseInline(admin.TabularInline):
    model = CamVerlustklasse
    extra = 0


@admin.register(CamSzenario)
class CamSzenarioAdmin(admin.ModelAdmin):
    list_display = ("name", "n_simulations", "random_seed", "geaendert_am")
    search_fields = ("name", "beschreibung")
    inlines = [CamControlInline, CamStageInline, CamVerlustklasseInline]
