from django.urls import path

from .views import (
    SzenarioCreateView,
    SzenarioDeleteView,
    SzenarioDetailView,
    SzenarioListView,
    SzenarioUpdateView,
    lec_vorschau,
)

app_name = "szenarien"

urlpatterns = [
    path("", SzenarioListView.as_view(), name="dashboard"),
    path("neu/", SzenarioCreateView.as_view(), name="create"),
    path("lec-vorschau/", lec_vorschau, name="lec_vorschau"),
    path("<int:pk>/", SzenarioDetailView.as_view(), name="detail"),
    path("<int:pk>/bearbeiten/", SzenarioUpdateView.as_view(), name="update"),
    path("<int:pk>/loeschen/", SzenarioDeleteView.as_view(), name="delete"),
]
