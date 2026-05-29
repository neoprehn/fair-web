"""Views für das Starten und Verfolgen von Simulationsläufen."""

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.views.generic import DetailView

from apps.szenarien.models import Szenario

from .models import MetaLauf, Simulationslauf
from .services import starte_meta_async, starte_simulation_async


@require_POST
def simulation_starten(request, szenario_pk):
    """Legt einen Lauf an, startet die Berechnung im Hintergrund und leitet weiter."""
    szenario = get_object_or_404(Szenario, pk=szenario_pk)
    lauf = Simulationslauf.objects.create(
        szenario=szenario,
        n_simulations=szenario.n_simulations,
        random_seed=szenario.random_seed,
    )
    starte_simulation_async(lauf.pk)
    return redirect("berechnung:lauf", pk=lauf.pk)


class LaufDetailView(DetailView):
    model = Simulationslauf
    template_name = "berechnung/lauf.html"
    context_object_name = "lauf"


def lauf_status(request, pk):
    """JSON-Endpunkt für das Fortschritts-Polling."""
    lauf = get_object_or_404(Simulationslauf, pk=pk)
    return JsonResponse({"status": lauf.status, "fortschritt": lauf.fortschritt})


@require_POST
def meta_starten(request):
    """Startet einen gemeinsamen Lauf über mehrere ausgewählte Szenarien."""
    ids = request.POST.getlist("szenarien")
    szenarien = list(Szenario.objects.filter(pk__in=ids))
    if not szenarien:
        return redirect("szenarien:dashboard")

    lauf = MetaLauf.objects.create(
        n_simulations=max(sz.n_simulations for sz in szenarien),
        random_seed=42,
    )
    lauf.szenarien.set(szenarien)
    starte_meta_async(lauf.pk)
    return redirect("berechnung:meta_lauf", pk=lauf.pk)


class MetaLaufDetailView(DetailView):
    model = MetaLauf
    template_name = "berechnung/meta_lauf.html"
    context_object_name = "lauf"


def meta_status(request, pk):
    lauf = get_object_or_404(MetaLauf, pk=pk)
    return JsonResponse({"status": lauf.status, "fortschritt": lauf.fortschritt})
