from django.urls import path

from . import views

app_name = "konten"

urlpatterns = [
    path("registrieren/", views.registrieren, name="registrieren"),
    path("ki-einstellungen/", views.ki_einstellungen, name="ki_einstellungen"),
]
