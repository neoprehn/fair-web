"""Konvertierung CamSzenario -> pyfair-cam-Modell + asynchroner Runner.

``_build_model`` übersetzt die Django-Objekte eines Szenarios 1:1 in ein
``pyfair_cam.FairCamModel`` (Feldnamen spiegeln die pyfair-cam-API bewusst,
siehe ``models.py``-Docstring). ``simuliere_cam`` ist eine reine, testbare
Funktion, die simuliert und ein Ergebnis-Dict liefert; sie nutzt dafür die
generischen (nicht FAIR-spezifischen) Kennzahlen-/LEC-/Histogramm-Helfer aus
``apps.berechnung.services``, damit das Ergebnis-JSON-Schema identisch bleibt
und ``cam/lauf.html`` dieselbe Plotly-JS-Logik wie ``berechnung/lauf.html``
wiederverwenden kann.

``starte_cam_simulation_async`` führt das in einem Hintergrund-Thread aus,
analog zu ``apps.berechnung.services`` (Variante A, siehe dortiger Docstring).
Anders als dort gibt es hier kein Batch-Fortschritts-Hook, weil
``FairCamSimulator`` keinen chunked Lauf anbietet – der Fortschritt springt
entsprechend von 0 direkt auf 100.
"""

import threading

import numpy as np
from django.db import connection

from apps.berechnung.services import _ergebnis_aus_sample, _histogramm

from .models import CamControl


def _build_model(szenario):
    """Baut ein ``FairCamModel`` aus einem ``CamSzenario`` samt Control/Stufen/Verlustklassen."""
    from pyfair_cam import (
        BetaPert,
        DetectionResponseFactor,
        FairCamModel,
        Poisson,
        ResistiveControl,
        Stage,
    )

    model = FairCamModel(name=szenario.name, n_simulations=szenario.n_simulations)
    model.input_threat_frequency(
        BetaPert(szenario.tef_low, szenario.tef_mode, szenario.tef_high)
    )

    try:
        control = szenario.control
    except CamControl.DoesNotExist:
        raise ValueError("CAM-Szenario hat kein Resistive Control – nichts zu berechnen.")

    model.add_resistive_control(
        ResistiveControl(
            name=control.name,
            intended_efficacy=BetaPert(
                control.intended_efficacy_low, control.intended_efficacy_mode, control.intended_efficacy_high
            ),
            variant_efficacy=BetaPert(
                control.variant_efficacy_low, control.variant_efficacy_mode, control.variant_efficacy_high
            ),
            variance_frequency=Poisson(
                lam=control.variance_frequency_lambda, range_=control.variance_frequency_range
            ),
            variance_duration=BetaPert(
                control.variance_duration_low, control.variance_duration_mode, control.variance_duration_high
            ),
            coverage=BetaPert(control.coverage_low, control.coverage_mode, control.coverage_high),
        )
    )

    stages_qs = list(szenario.stages.order_by("reihenfolge"))
    stages = [
        Stage(
            name=s.name,
            coverage=s.coverage,
            visibility=s.visibility,
            vis_reliability=s.vis_reliability,
            recognition=s.recognition,
            rec_reliability=s.rec_reliability,
            monitoring_cadence=s.monitoring_cadence,
            mon_reliability=s.mon_reliability,
            duration=s.duration,
            progression_probability=s.progression_probability,
            review_independence=s.review_independence,
        )
        for s in stages_qs
    ]
    stage_outcome_map = {s.reihenfolge: s.outcome_class for s in stages_qs}
    verlust = {v.klasse: BetaPert(v.low, v.mode, v.high) for v in szenario.verlustklassen.all()}

    model.set_detection_response(
        DetectionResponseFactor(
            name=f"{szenario.name} – Kill-Chain",
            stages=stages,
            stage_outcome_map=stage_outcome_map,
            loss_distributions=verlust,
            t_containment=BetaPert(
                szenario.t_containment_low, szenario.t_containment_mode, szenario.t_containment_high
            ),
            t_resilience=BetaPert(
                szenario.t_resilience_low, szenario.t_resilience_mode, szenario.t_resilience_high
            ),
            concurrency=BetaPert(
                szenario.concurrency_low, szenario.concurrency_mode, szenario.concurrency_high
            ),
        )
    )
    return model


def simuliere_cam(szenario, n_simulations, random_seed):
    """Baut das Modell, simuliert und liefert ein Ergebnis-Dict (Kennzahlen + LEC + Histogramme)."""
    from pyfair_cam import FairCamSimulator

    model = _build_model(szenario)
    simulator = FairCamSimulator(n_simulations=n_simulations, seed=random_seed)
    simulator.run(model)
    risk = simulator.get_results()

    ergebnis = _ergebnis_aus_sample(risk)
    ergebnis["verteilung_hist"] = _histogramm(risk)

    components = simulator.get_components()
    for feld, key in (("tef_mittel", "tef"), ("susceptibility_mittel", "susceptibility"), ("lef_mittel", "lef")):
        arr = components.get(key)
        if arr is not None:
            ergebnis[feld] = float(np.mean(arr))

    outcome = components.get("outcome_class")
    if outcome is not None:
        werte, counts = np.unique(outcome, return_counts=True)
        ergebnis["outcome_verteilung"] = {
            "klassen": [str(w) for w in werte.tolist()],
            "anzahl": [int(c) for c in counts.tolist()],
        }

    detected = components.get("detected_at_stage")
    if detected is not None:
        n_stages = szenario.stages.count()
        ergebnis["stage_erkennung"] = {
            "stufe": list(range(1, n_stages + 1)),
            "anteil": [float(np.mean(detected == i)) for i in range(1, n_stages + 1)],
        }
    return ergebnis


def starte_cam_simulation_async(lauf_id):
    """Startet die Berechnung in einem Hintergrund-Thread (nicht blockierend)."""
    thread = threading.Thread(target=_thread_target, args=(lauf_id,), daemon=True)
    thread.start()
    return thread


def _thread_target(lauf_id):
    """Thread-Hülle um _run_cam_simulation: schließt am Ende die Thread-DB-Verbindung."""
    try:
        _run_cam_simulation(lauf_id)
    finally:
        connection.close()


def _run_cam_simulation(lauf_id):
    """Führt die Simulation aus und pflegt Status/Fortschritt (synchron, testbar)."""
    from .models import CamSimulationslauf

    try:
        lauf = CamSimulationslauf.objects.get(pk=lauf_id)
        lauf.status = CamSimulationslauf.Status.LAEUFT
        lauf.save(update_fields=["status", "aktualisiert_am"])

        ergebnis = simuliere_cam(lauf.szenario, lauf.n_simulations, lauf.random_seed)

        lauf.status = CamSimulationslauf.Status.FERTIG
        lauf.fortschritt = 100
        lauf.ergebnis = ergebnis
        lauf.save(update_fields=["status", "fortschritt", "ergebnis", "aktualisiert_am"])
    except Exception as exc:  # noqa: BLE001 – Fehler im Lauf festhalten, nicht crashen
        CamSimulationslauf.objects.filter(pk=lauf_id).update(
            status=CamSimulationslauf.Status.FEHLER, fehler_text=str(exc)
        )
