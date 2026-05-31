"""Views für das Starten und Verfolgen von Simulationsläufen."""

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.views.generic import DetailView

from apps.szenarien import fair_tree
from apps.szenarien.models import Szenario, Vergleich

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


def _de(v, dezimal=2):
    """Deutsches Zahlenformat (Tausenderpunkt, Komma-Dezimal)."""
    if v is None:
        return ""
    return f"{v:,.{dezimal}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _param_de(v):
    """Parameterwert 'wie eingegeben' – ohne künstliche Nachkommastellen.

    Ganzzahlen ohne Dezimalstellen (mit Tausenderpunkt), sonst Komma-Dezimal
    mit abgeschnittenen Null-Endstellen.
    """
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return str(v)
    v = float(v)
    if v.is_integer():
        return f"{int(v):,}".replace(",", ".")
    s = f"{v:.6f}".rstrip("0").rstrip(".")
    ganz, _, dez = s.partition(".")
    vorz = "-" if ganz.startswith("-") else ""
    ganz = f"{abs(int(ganz)):,}".replace(",", ".")
    return vorz + ganz + ("," + dez if dez else "")


def _formatiere_wert(code, wert):
    """Wahrscheinlichkeiten mit 2 Nachkommastellen, sonst ganzzahlig (Tausenderpunkt)."""
    if code != "Risk" and fair_tree.typ(code) == "probability":
        return f"{wert:.2f}".replace(".", ",")
    return f"{wert:,.0f}".replace(",", ".")


def _node_tooltip(code, info):
    """SVG-Tooltip-Text (5 Nachkommastellen)."""
    if not info:
        return "nicht genutzt"
    if info["status"] == "eingabe":
        zeilen = ["Eingabe · Verteilung: " + info.get("verteilung", "")]
        for k, v in (info.get("params") or {}).items():
            zeilen.append(f"{k} = {_de(v, 5) if isinstance(v, (int, float)) else v}")
        if info.get("confidence"):
            zeilen.append("Konfidenz: " + info["confidence"])
        if info.get("angreifertyp"):
            zeilen.append("Angreifertyp: " + info["angreifertyp"])
        return "\n".join(zeilen)
    return (f"berechnet\nMittelwert: {_de(info['mittelwert'], 5)}\n"
            f"Std.-Abw.: {_de(info['stdev'], 5)}\n"
            f"P90: {_de(info['p90'], 5)}\nP95: {_de(info['p95'], 5)}")


_TABELLE_ORDER = ["LEF", "TEF", "CF", "POA", "VULN", "TC", "CS",
                  "LM", "PL", "SL", "SLEF", "SLEM", "Risk"]


def _knoten_tabelle(knoten):
    """Zeilen für die pyfair-ähnliche Tabelle (Target/Verteilung/Params/… + P90/P95)."""
    zeilen = []
    for code in _TABELLE_ORDER:
        info = knoten.get(code)
        if not info:
            continue
        name = "Risk" if code == "Risk" else fair_tree.target(code)
        if info["status"] == "berechnet":
            name += " (berechnet)"
        params = [
            f"{k} = {_param_de(v)}"
            for k, v in (info.get("params") or {}).items()
        ]
        wahrscheinlich = code != "Risk" and fair_tree.typ(code) == "probability"
        dez = 4 if wahrscheinlich else 2
        zeilen.append({
            "name": name, "verteilung": info.get("verteilung", ""),
            "params": params, "confidence": info.get("confidence") or "",
            "mean": _de(info["mittelwert"], dez), "stdev": _de(info["stdev"], dez),
            "min": _de(info["min"], dez), "max": _de(info["max"], dez),
            "p90": _de(info["p90"], dez), "p95": _de(info["p95"], dez),
        })
    return zeilen


def schnittpunkt(lec, overlay):
    """Schnittpunkt LEC × Risikotoleranz: {"loss": €, "tolerance": Anteil 0–1} oder None."""
    if not lec or not overlay:
        return None
    try:
        import numpy as np
        lx = np.array([p["verlust"] for p in lec], dtype=float)
        ly = np.array([p["ueberschreitung"] for p in lec], dtype=float)
        if overlay["kind"] == "vline":
            v = float(overlay["value"])
            return {"loss": v, "tolerance": float(np.interp(v, lx, ly))}
        tx = np.array(overlay["x"], dtype=float)
        ty = np.array(overlay["y"], dtype=float)
        order = np.argsort(tx)
        tx, ty = tx[order], ty[order]
        xs = np.linspace(max(lx.min(), tx.min()), min(lx.max(), tx.max()), 400)
        if xs[0] >= xs[-1]:
            return None
        diff = np.interp(xs, lx, ly) - np.interp(xs, tx, ty)
        wechsel = np.where(np.diff(np.sign(diff)) != 0)[0]
        if not len(wechsel):
            return None
        i = wechsel[0]
        x0, x1, d0, d1 = xs[i], xs[i + 1], diff[i], diff[i + 1]
        xc = x0 - d0 * (x1 - x0) / (d1 - d0) if d1 != d0 else x0
        return {"loss": float(xc), "tolerance": float(np.interp(xc, lx, ly))}
    except Exception:  # noqa: BLE001
        return None


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
            n["tooltip"] = _node_tooltip(n["code"], info)
        context["svg_nodes"] = nodes
        context["svg_edges"] = edges
        ov = toleranz_overlay(self.object.szenario.risikotoleranz)
        context["toleranz_overlay"] = ov
        context["knoten_tabelle"] = _knoten_tabelle(knoten)
        if self.object.ist_fertig and self.object.ergebnis:
            context["schnittpunkt"] = schnittpunkt(self.object.ergebnis.get("lec"), ov)
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


@require_POST
def vergleich_starten(request, pk):
    """Startet einen Meta-Lauf für die Szenarien eines gespeicherten Vergleichs."""
    vergleich = get_object_or_404(Vergleich, pk=pk)
    szenarien = list(vergleich.szenarien.all())
    if len(szenarien) < 2:
        return redirect("szenarien:dashboard")

    lauf = MetaLauf.objects.create(
        vergleich=vergleich,
        n_simulations=vergleich.n_simulations,
        random_seed=vergleich.random_seed,
    )
    lauf.szenarien.set(szenarien)
    starte_meta_async(lauf.pk)
    return redirect("berechnung:meta_lauf", pk=lauf.pk)


class MetaLaufDetailView(DetailView):
    model = MetaLauf
    template_name = "berechnung/meta_lauf.html"
    context_object_name = "lauf"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lauf = self.object
        overlay = None
        schnittpunkte = []
        ref = lauf.vergleich.referenz_szenario if lauf.vergleich else None
        if lauf.ist_fertig and lauf.ergebnis and ref:
            overlay = toleranz_overlay(ref.risikotoleranz)
            for s in lauf.ergebnis.get("szenarien", []):
                sp = schnittpunkt(s.get("stats", {}).get("lec"), overlay)
                schnittpunkte.append({"name": s.get("name"), "schnittpunkt": sp})
        context["referenz_overlay"] = overlay
        context["referenz_name"] = ref.name if ref else None
        context["vergleich_schnittpunkte"] = schnittpunkte
        return context


def meta_status(request, pk):
    lauf = get_object_or_404(MetaLauf, pk=pk)
    return JsonResponse({"status": lauf.status, "fortschritt": lauf.fortschritt})
