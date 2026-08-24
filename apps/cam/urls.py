from django.urls import path

from .views import (
    CamLaufDetailView,
    CamSzenarioCreateView,
    CamSzenarioDeleteView,
    CamSzenarioDetailView,
    CamSzenarioListView,
    CamSzenarioUpdateView,
    cam_lauf_status,
    cam_simulation_starten,
)

app_name = "cam"

urlpatterns = [
    path("", CamSzenarioListView.as_view(), name="dashboard"),
    path("neu/", CamSzenarioCreateView.as_view(), name="create"),
    path("<int:pk>/", CamSzenarioDetailView.as_view(), name="detail"),
    path("<int:pk>/bearbeiten/", CamSzenarioUpdateView.as_view(), name="update"),
    path("<int:pk>/loeschen/", CamSzenarioDeleteView.as_view(), name="delete"),
    path("<int:pk>/starten/", cam_simulation_starten, name="starten"),
    path("lauf/<int:pk>/", CamLaufDetailView.as_view(), name="lauf"),
    path("lauf/<int:pk>/status/", cam_lauf_status, name="status"),
]
