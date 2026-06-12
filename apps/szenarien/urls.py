from django.urls import path

from .views import (
    ClusterCreateView,
    ClusterDeleteView,
    ClusterUpdateView,
    SzenarioCreateView,
    SzenarioDeleteView,
    SzenarioDetailView,
    SzenarioListView,
    SzenarioUpdateView,
    VergleichCreateView,
    VergleichDeleteView,
    VergleichListView,
    VergleichUpdateView,
    ki_vorschlag,
    lec_vorschau,
    szenario_klonen,
)

app_name = "szenarien"

urlpatterns = [
    path("", SzenarioListView.as_view(), name="dashboard"),
    path("neu/", SzenarioCreateView.as_view(), name="create"),
    path("lec-vorschau/", lec_vorschau, name="lec_vorschau"),
    path("ki-vorschlag/", ki_vorschlag, name="ki_vorschlag"),
    path("vergleiche/", VergleichListView.as_view(), name="vergleich_list"),
    path("vergleich/neu/", VergleichCreateView.as_view(), name="vergleich_create"),
    path("vergleich/<int:pk>/bearbeiten/", VergleichUpdateView.as_view(), name="vergleich_update"),
    path("vergleich/<int:pk>/loeschen/", VergleichDeleteView.as_view(), name="vergleich_delete"),
    path("cluster/neu/", ClusterCreateView.as_view(), name="cluster_create"),
    path("cluster/<int:pk>/bearbeiten/", ClusterUpdateView.as_view(), name="cluster_update"),
    path("cluster/<int:pk>/loeschen/", ClusterDeleteView.as_view(), name="cluster_delete"),
    path("<int:pk>/", SzenarioDetailView.as_view(), name="detail"),
    path("<int:pk>/bearbeiten/", SzenarioUpdateView.as_view(), name="update"),
    path("<int:pk>/klonen/", szenario_klonen, name="clone"),
    path("<int:pk>/loeschen/", SzenarioDeleteView.as_view(), name="delete"),
]
