from django.urls import path

from .views import (
    CamSzenarioCreateView,
    CamSzenarioDeleteView,
    CamSzenarioDetailView,
    CamSzenarioListView,
    CamSzenarioUpdateView,
)

app_name = "cam"

urlpatterns = [
    path("", CamSzenarioListView.as_view(), name="dashboard"),
    path("neu/", CamSzenarioCreateView.as_view(), name="create"),
    path("<int:pk>/", CamSzenarioDetailView.as_view(), name="detail"),
    path("<int:pk>/bearbeiten/", CamSzenarioUpdateView.as_view(), name="update"),
    path("<int:pk>/loeschen/", CamSzenarioDeleteView.as_view(), name="delete"),
]
