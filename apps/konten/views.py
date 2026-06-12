"""Konten: Selbstregistrierung.

Neue Nutzer werden automatisch der Gruppe „Betrachter" zugeordnet (die
konkreten Rechte der Gruppe folgen in einem späteren Slice). Konten
starten **inaktiv** (``is_active=False``) und müssen von einem
Administrator im Django-Admin freigeschaltet werden, bevor ein Login
möglich ist.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.shortcuts import redirect, render

from .forms import KIEinstellungForm, RegistrierForm
from .models import KIEinstellung

BETRACHTER_GRUPPE = "Betrachter"


def registrieren(request):
    if request.user.is_authenticated:
        return redirect("/")
    if request.method == "POST":
        form = RegistrierForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            gruppe, _ = Group.objects.get_or_create(name=BETRACHTER_GRUPPE)
            user.groups.add(gruppe)
            messages.success(
                request,
                "Konto angelegt. Ein Administrator muss es noch freischalten, "
                "bevor du dich anmelden kannst.",
            )
            return redirect("login")
    else:
        form = RegistrierForm()
    return render(request, "registration/registrieren.html", {"form": form})


@login_required
def ki_einstellungen(request):
    """Pro-Nutzer-Konfiguration des optionalen KI-Assistenten."""
    instance, _ = KIEinstellung.objects.get_or_create(user=request.user)
    if request.method == "POST":
        form = KIEinstellungForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, "KI-Einstellungen gespeichert.")
            return redirect("konten:ki_einstellungen")
    else:
        form = KIEinstellungForm(instance=instance)
    return render(request, "registration/ki_einstellungen.html", {
        "form": form, "ki_einstellung": instance,
    })
