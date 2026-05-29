from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("berechnung/", include("apps.berechnung.urls")),
    path("", include("apps.szenarien.urls")),
]
