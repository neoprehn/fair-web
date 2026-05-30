"""Views für das Starten und Verfolgen von Simulationsläufen."""

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.views.generic import DetailView

from apps.szenarien import fair_tree
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


def _formatiere_wert(code, wert):
    """Wahrscheinlichkeiten mit 2 Nachkommastellen, sonst ganzzahlig (Tausenderpunkt)."""
    if code != "Risk" and fair_tree.typ(code) == "probability":
        return f"{wert:.2f}".replace(".", ",")
    return f"{wert:,.0f}".replace(",", ".")


def toleranz_overlay(rt):
    """Risikotoleranz in eine Overlay-Form fürs LEC-Chart bringen.

    Returns dict je Typ:
      constant      -> {"kind": "vline", "value": ...}
      curve         -> {"kind": "curve", "x": [...], "y": [...]}
      distribution  -> {"kind": "curve", ...}  (Exceedance der gesampleten Verteilung)
    """
    if not rt:
        return None
    typ = rt.get("type")
    if typ == "constant":
        return {"kind": "vline", "value": rt.get("value")}
    if typ == "curve":
        pts = rt.get("points", [])
        return {"kind": "curve", "x": [p["loss"] for p in pts], "y": [p["level"] for p in pts]}
    if typ == "distribution":
        try:
            import numpy as np
            from pyfair.model.model_input import FairDataInput
            n = int(rt.get("samples") or 20000)
            sample = np.sort(FairDataInput().generate(
                "Toleranz", n, distribution=rt["distribution"], params=rt["params"]))
            m = len(sample)
            idx = np.linspace(0, m - 1, min(120, m)).astype(int)
            return {"kind": "curve",
                    "x": [float(sample[i]) for i in idx],
                    "y": [float(1.0 - i / m) for i in idx]}
        except Exception:  # noqa: BLE001 – Overlay ist optional, nie die Seite kippen
            return None
    return None


class LaufDetailView(DetailView):
    model = Simulationslauf
    template_name = "berechnung/lauf.html"
    context_object_name = "lauf"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        nodes, edges = fair_tree.svg_layout()
        knoten = {}
        if self.object.ist_fertig and self.object.ergebnis:
            knoten = self.object.ergebnis.get("knoten", {})
        for n in nodes:
            info = knoten.get(n["code"])
            n["status"] = info["status"] if info else "unused"
            n["wert"] = _formatiere_wert(n["code"], info["mittelwert"]) if info else None
        context["svg_nodes"] = nodes
        context["svg_edges"] = edges
        context["toleranz_overlay"] = toleranz_overlay(self.object.szenario.risikotoleranz)
        return context


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
