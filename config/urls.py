from django.contrib import admin
from django.contrib.auth.views import LoginView
from django.urls import include, path

from apps.konten.forms import BootstrapAuthenticationForm

urlpatterns = [
    path("admin/", admin.site.urls),
    # Eigene Login-Seite (Bootstrap-Form) vor den Standard-Auth-Routen.
    path("accounts/login/",
         LoginView.as_view(authentication_form=BootstrapAuthenticationForm),
         name="login"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("berechnung/", include("apps.berechnung.urls")),
    path("", include("apps.szenarien.urls")),
]
