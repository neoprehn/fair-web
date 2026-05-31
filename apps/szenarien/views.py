"""Views für die Szenario-Verwaltung (CRUD).

Ein Szenario wird zusammen mit seinen Faktor-Eingaben (LEF + LM) über ein
Inline-Formset angelegt und bearbeitet.
"""

import json

from django.db import transaction
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from . import fair_tree
from .fair_confidence import (
    CONFIDENCE_DEFAULTS,
    CONFIDENCE_DISTRIBUTIONS,
    UNSICHERHEIT_LABELS,
    UNSICHERHEIT_TO_CONFIDENCE,
)
from .forms import FaktorEingabeForm, SzenarioForm, VergleichForm
from .models import Angreifertyp, FaktorEingabe, Szenario, Vergleich


def risikotoleranz_aus_post(post):
    """Baut die Risikotoleranz (kontextbasiert) aus den POST-Feldern.

    Modul-Funktion, damit sowohl das Form-Mixin als auch der Live-Vorschau-
    Endpoint dieselbe Logik nutzen.
    """
    from django.utils.formats import sanitize_separators

    typ = post.get("rt_type")

    def zahl(name):
        v = post.get(name, "")
        return float(sanitize_separators(v)) if v not in ("", None) else None

    try:
        if typ == "constant":
            v = zahl("rt_value")
            return {"type": "constant", "value": v} if v is not None else None
        if typ == "distribution":
            dist = post.get("rt_dist") or "pert"
            felder = {
                "pert": [("low", "rt_pert_low"), ("mode", "rt_pert_mode"),
                         ("high", "rt_pert_high"), ("gamma", "rt_pert_gamma")],
                "lognormal": [("mean", "rt_ln_mean"), ("sigma", "rt_ln_sigma")],
                "normal": [("mean", "rt_no_mean"), ("stdev", "rt_no_stdev")],
            }.get(dist, [])
            params = {k: zahl(feld) for k, feld in felder if zahl(feld) is not None}
            if not params:
                return None
            samples = post.get("rt_samples")
            return {"type": "distribution", "distribution": dist, "params": params,
                    "samples": int(samples) if samples else 20000}
        if typ == "curve":
            punkte = json.loads(post.get("rt_curve") or "[]")
            punkte = [{"loss": float(sanitize_separators(str(p["loss"]))),
                       "level": float(sanitize_separators(str(p["level"])))}
                      for p in punkte
                      if str(p.get("loss", "")) != "" and str(p.get("level", "")) != ""]
            return {"type": "curve", "points": punkte} if punkte else None
    except (ValueError, TypeError, KeyError):
        return None
    return None


# Konfiguration für das Slider-JS (Single Source: fair_confidence).
# Wird im Template via {{ ...|json_script }} ausgegeben.
_CONFIDENCE_CONFIG = {
    "defaults": CONFIDENCE_DEFAULTS,
    "distributions": list(CONFIDENCE_DISTRIBUTIONS),
    "unsicherheitToConfidence": UNSICHERHEIT_TO_CONFIDENCE,
    "labels": UNSICHERHEIT_LABELS,
}


class SzenarioListView(ListView):
    model = Szenario
    template_name = "szenarien/dashboard.html"
    context_object_name = "szenarien"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["vergleiche"] = Vergleich.objects.prefetch_related("szenarien", "laeufe")
        return context


class SzenarioDetailView(DetailView):
    model = Szenario
    template_name = "szenarien/detail.html"
    context_object_name = "szenario"


class _SzenarioFormMixin:
    """Anlegen/Bearbeiten mit freiem FAIR-Baum-Schnitt.

    Pro Knoten ein FaktorEingabeForm (Prefix = Code). Welche Knoten
    gespeichert werden, bestimmt der „Schnitt" aus den Modus-Umschaltern.
    """

    model = Szenario
    form_class = SzenarioForm
    template_name = "szenarien/form.html"

    def _bestehende(self):
        if self.object:
            return {f.faktor: f for f in self.object.faktoren.all()}
        return {}

    def _node_forms(self, data=None):
        bestehend = self._bestehende()
        forms = {}
        for code, _tiefe in fair_tree.traversal():
            inst = bestehend.get(code) or FaktorEingabe(faktor=code)
            forms[code] = FaktorEingabeForm(data, instance=inst, prefix=code, faktor_code=code)
        return forms

    def _modus_aus_post(self):
        return {c: self.request.POST.get(f"modus-{c}", "direkt") for c in fair_tree.NICHT_BLATT}

    def _risikotoleranz_aus_post(self):
        return risikotoleranz_aus_post(self.request.POST)

    def _node_dict(self, code, node_forms, modus):
        """Rekursiver Knoten für die Baum-Darstellung."""
        kinder = fair_tree.CHILDREN.get(code, [])
        return {
            "code": code,
            "abbr": fair_tree.abbr(code),
            "name": fair_tree.target(code),
            "ist_blatt": fair_tree.ist_blatt(code),
            "modus": modus.get(code, "direkt"),
            "form": node_forms[code],
            # Unterste Ebene: wenn alle Kinder Blätter sind, gestapelt darstellen.
            "kinder_sind_blaetter": bool(kinder) and all(fair_tree.ist_blatt(k) for k in kinder),
            "children": [self._node_dict(kind, node_forms, modus) for kind in kinder],
        }

    def _baum_kontext(self, node_forms, modus):
        return {
            "baum_lef": self._node_dict("LEF", node_forms, modus),
            "baum_lm": self._node_dict("LM", node_forms, modus),
        }

    def get_context_data(self, **kwargs):
        from apps.admin_bereich.models import AppKonfiguration

        context = super().get_context_data(**kwargs)
        context["confidence_config"] = _CONFIDENCE_CONFIG
        context["angreifertypen"] = Angreifertyp.objects.all()
        context["konfig"] = AppKonfiguration.load()
        context["risikotoleranz"] = self.object.risikotoleranz if self.object else None
        context["svg_nodes"], context["svg_edges"] = fair_tree.svg_layout()
        if "baum_lef" not in context:
            if self.request.method == "POST":
                node_forms = self._node_forms(self.request.POST)
                modus = self._modus_aus_post()
            else:
                node_forms = self._node_forms()
                modus = (
                    fair_tree.modus_aus_codes(self.object.schnitt_codes())
                    if self.object
                    else {c: "direkt" for c in fair_tree.NICHT_BLATT}
                )
            context.update(self._baum_kontext(node_forms, modus))
        return context

    def form_valid(self, form):
        modus = self._modus_aus_post()
        frontier = fair_tree.frontier_aus_modus(modus)
        node_forms = self._node_forms(self.request.POST)
        frontier_forms = {code: node_forms[code] for code in frontier}

        alle_ok = all(f.is_valid() for f in frontier_forms.values())
        schnitt_ok = fair_tree.schnitt_ist_gueltig(frontier)
        if not (alle_ok and schnitt_ok):
            context = self.get_context_data(form=form, **self._baum_kontext(node_forms, modus))
            if not schnitt_ok:
                context["schnitt_fehler"] = (
                    "Bitte einen vollständigen, rechenbaren Schnitt angeben "
                    "(jeder Ast bis zu einer Eingabe heruntergebrochen)."
                )
            return self.render_to_response(context)

        from apps.admin_bereich.models import AppKonfiguration
        konfig = AppKonfiguration.load()
        with transaction.atomic():
            self.object = form.save()
            if konfig.seed_global:
                self.object.random_seed = konfig.standard_seed
            if konfig.n_simulations_global:
                self.object.n_simulations = konfig.standard_n_simulations
            if konfig.risikotoleranz_global:
                self.object.risikotoleranz = konfig.unternehmens_risikotoleranz
            else:
                self.object.risikotoleranz = self._risikotoleranz_aus_post()
            self.object.save(update_fields=["risikotoleranz", "random_seed", "n_simulations"])
            self.object.faktoren.all().delete()
            for code, f in frontier_forms.items():
                eingabe = f.save(commit=False)
                eingabe.szenario = self.object
                eingabe.faktor = code
                eingabe.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy("szenarien:detail", kwargs={"pk": self.object.pk})


class SzenarioCreateView(_SzenarioFormMixin, CreateView):
    pass


class SzenarioUpdateView(_SzenarioFormMixin, UpdateView):
    pass


class SzenarioDeleteView(DeleteView):
    model = Szenario
    template_name = "szenarien/confirm_delete.html"
    context_object_name = "szenario"
    success_url = reverse_lazy("szenarien:dashboard")


class _VergleichFormMixin:
    model = Vergleich
    form_class = VergleichForm
    template_name = "szenarien/vergleich_form.html"

    def get_success_url(self):
        return reverse_lazy("szenarien:dashboard")


class VergleichCreateView(_VergleichFormMixin, CreateView):
    pass


class VergleichUpdateView(_VergleichFormMixin, UpdateView):
    pass


class VergleichDeleteView(DeleteView):
    model = Vergleich
    template_name = "szenarien/vergleich_confirm_delete.html"
    context_object_name = "vergleich"
    success_url = reverse_lazy("szenarien:dashboard")


def _inputs_aus_post(post):
    """Validiert den Schnitt + die Frontier-Faktoren aus POST und liefert
    ein pyfair-``inputs``-Dict – oder ``(None, fehlertext)``.
    """
    modus = {c: post.get(f"modus-{c}", "direkt") for c in fair_tree.NICHT_BLATT}
    frontier = fair_tree.frontier_aus_modus(modus)
    if not fair_tree.schnitt_ist_gueltig(frontier):
        return None, "Schnitt unvollständig – jeden Ast bis zu einer Eingabe herunterbrechen."
    inputs = {}
    for code in frontier:
        f = FaktorEingabeForm(post, instance=FaktorEingabe(faktor=code),
                              prefix=code, faktor_code=code)
        if not f.is_valid():
            return None, f"Faktor {fair_tree.abbr(code)} noch unvollständig."
        inst = f.instance
        inputs[inst.fair_target] = inst.to_fair_kwargs()
    return inputs, None


@require_POST
def lec_vorschau(request):
    """Live-Vorschau: schnelle Mini-Simulation + LEC/Toleranz aus dem aktuellen
    (ungespeicherten) Formularzustand. Antwortet als JSON."""
    from apps.berechnung.services import simuliere_vorschau
    from apps.berechnung.views import schnittpunkt, toleranz_overlay

    from apps.admin_bereich.models import AppKonfiguration

    inputs, fehler = _inputs_aus_post(request.POST)
    if inputs is None:
        return JsonResponse({"ok": False, "fehler": fehler})
    try:
        erg = simuliere_vorschau(inputs, n_simulations=1500)
    except Exception as exc:  # noqa: BLE001 – Vorschau soll nie 500en
        return JsonResponse({"ok": False, "fehler": str(exc)})

    konfig = AppKonfiguration.load()
    rt = konfig.unternehmens_risikotoleranz if konfig.risikotoleranz_global else risikotoleranz_aus_post(request.POST)
    overlay = toleranz_overlay(rt)
    return JsonResponse({
        "ok": True,
        "lec": erg["lec"],
        "perzentile": erg["perzentile"],
        "p90": erg["p90"],
        "overlay": overlay,
        "schnittpunkt": schnittpunkt(erg["lec"], overlay),
    })
