from django.urls import path

from .views import (
    LaufDetailView,
    MetaLaufDetailView,
    lauf_status,
    meta_starten,
    meta_status,
    simulation_starten,
)

app_name = "berechnung"

urlpatterns = [
    path("szenario/<int:szenario_pk>/starten/", simulation_starten, name="starten"),
    path("lauf/<int:pk>/", LaufDetailView.as_view(), name="lauf"),
    path("lauf/<int:pk>/status/", lauf_status, name="status"),
    path("meta/starten/", meta_starten, name="meta_starten"),
    path("meta/<int:pk>/", MetaLaufDetailView.as_view(), name="meta_lauf"),
    path("meta/<int:pk>/status/", meta_status, name="meta_status"),
]
