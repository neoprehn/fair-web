"""Konten: Selbstregistrierung.

Neue Nutzer werden automatisch der Gruppe „Betrachter" zugeordnet (die
konkreten Rechte der Gruppe folgen in einem späteren Slice) und direkt
angemeldet.
"""

from django.contrib.auth import login
from django.contrib.auth.models import Group
from django.shortcuts import redirect, render

from .forms import RegistrierForm

BETRACHTER_GRUPPE = "Betrachter"


def registrieren(request):
    if request.user.is_authenticated:
        return redirect("/")
    if request.method == "POST":
        form = RegistrierForm(request.POST)
        if form.is_valid():
            user = form.save()
            gruppe, _ = Group.objects.get_or_create(name=BETRACHTER_GRUPPE)
            user.groups.add(gruppe)
            login(request, user)
            return redirect("/")
    else:
        form = RegistrierForm()
    return render(request, "registration/registrieren.html", {"form": form})
