from django.contrib import admin
from django.contrib.auth.views import LoginView
from django.urls import include, path
from django.views.generic import TemplateView

from apps.konten.forms import BootstrapAuthenticationForm
from apps.szenarien.views import StartseiteView

# Admin-Branding + „Website anzeigen"-Ziel (Rücklink zur App).
admin.site.site_header = "fair-web – Verwaltung"
admin.site.site_title = "fair-web Verwaltung"
admin.site.index_title = "Verwaltung"
admin.site.site_url = "/"

urlpatterns = [
    path("admin/", admin.site.urls),
    # Eigene Login-Seite (Bootstrap-Form) vor den Standard-Auth-Routen.
    path("accounts/login/",
         LoginView.as_view(authentication_form=BootstrapAuthenticationForm),
         name="login"),
    path("accounts/", include("apps.konten.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
    path("berechnung/", include("apps.berechnung.urls")),
    path("szenarien/", include("apps.szenarien.urls")),
    path("hilfe/", TemplateView.as_view(template_name="hilfe.html"), name="hilfe"),
    path("", StartseiteView.as_view(), name="start"),
]
