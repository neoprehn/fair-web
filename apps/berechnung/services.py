"""Monte-Carlo-Engine und asynchroner Runner (Variante A).

``simuliere`` ist eine reine, testbare Funktion: sie rechnet die FAIR-
Simulation in mehreren Batches (für den Fortschritt) und liefert ein
Ergebnis-Dict (Kennzahlen + LEC-Kurve). ``starte_simulation_async`` führt
das in einem Hintergrund-Thread aus und schreibt den Fortschritt in den
``Simulationslauf``. Der Wechsel auf Celery (Variante B) würde nur diesen
Runner ersetzen – Engine, Modell und Polling bleiben gleich.
"""

import threading

from django.db import connection


def _ergebnis_aus_sample(sample):
    """Kennzahlen + (heruntergerechnete) LEC-Kurve aus den Verlustwerten."""
    import numpy as np

    sample = np.sort(np.asarray(sample, dtype=float))
    n = int(sample.size)

    def perz(p):
        return float(np.percentile(sample, p))

    # Loss Exceedance Curve: P(Verlust >= x), auf ~100 Punkte reduziert.
    punkte = min(100, n)
    idx = np.linspace(0, n - 1, punkte).astype(int)
    lec = [
        {"verlust": float(sample[k]), "ueberschreitung": float(1.0 - k / n)}
        for k in idx
    ]

    return {
        "n": n,
        "mittelwert": float(sample.mean()),
        "median": perz(50),
        "min": float(sample.min()),
        "max": float(sample.max()),
        "p10": perz(10),
        "p90": perz(90),
        "p95": perz(95),
        "p99": perz(99),
        "lec": lec,
    }


def simuliere(szenario, n_simulations, random_seed, batches=20, fortschritt=None):
    """Chunked Monte-Carlo-Simulation für ein Szenario.

    Parameters
    ----------
    szenario : Szenario
        Liefert die FAIR-Eingaben via ``fair_inputs()``.
    n_simulations, random_seed : int
        Gesamtzahl der Iterationen und Basis-Seed.
    batches : int
        In so viele Häppchen wird zerlegt (nur für die Fortschrittsanzeige;
        die Iterationen sind unabhängig, das Zusammenführen ist statistisch
        sauber – je Batch ein eigener Seed).
    fortschritt : callable(int) | None
        Wird nach jedem Batch mit dem Prozentwert (0–100) aufgerufen.
    """
    import numpy as np
    import pyfair

    inputs = szenario.fair_inputs()
    if not inputs:
        raise ValueError("Szenario hat keine FAIR-Faktoren – nichts zu berechnen.")
    pro_batch = max(1, n_simulations // batches)

    teile = []
    erzeugt = 0
    i = 0
    while erzeugt < n_simulations:
        n = min(pro_batch, n_simulations - erzeugt)
        model = pyfair.FairModel(
            name=szenario.name, n_simulations=n, random_seed=random_seed + i
        )
        for target, kwargs in inputs.items():
            model.input_data(target, **kwargs)
        model.calculate_all()
        teile.append(model.export_results()["Risk"].to_numpy())

        erzeugt += n
        i += 1
        if fortschritt:
            fortschritt(min(100, round(erzeugt / n_simulations * 100)))

    sample = np.concatenate(teile)
    return _ergebnis_aus_sample(sample)


def starte_simulation_async(lauf_id):
    """Startet die Berechnung in einem Hintergrund-Thread (nicht blockierend)."""
    thread = threading.Thread(target=_thread_target, args=(lauf_id,), daemon=True)
    thread.start()
    return thread


def _thread_target(lauf_id):
    """Thread-Hülle um _run_simulation: schließt am Ende die Thread-DB-Verbindung."""
    try:
        _run_simulation(lauf_id)
    finally:
        connection.close()


def _run_simulation(lauf_id):
    """Führt die Simulation aus und pflegt Status/Fortschritt (synchron, testbar)."""
    from .models import Simulationslauf

    try:
        lauf = Simulationslauf.objects.get(pk=lauf_id)
        lauf.status = Simulationslauf.Status.LAEUFT
        lauf.fortschritt = 0
        lauf.save(update_fields=["status", "fortschritt", "aktualisiert_am"])

        def melde(prozent):
            Simulationslauf.objects.filter(pk=lauf_id).update(fortschritt=prozent)

        ergebnis = simuliere(
            lauf.szenario, lauf.n_simulations, lauf.random_seed, fortschritt=melde
        )

        lauf.status = Simulationslauf.Status.FERTIG
        lauf.fortschritt = 100
        lauf.ergebnis = ergebnis
        lauf.save(update_fields=["status", "fortschritt", "ergebnis", "aktualisiert_am"])
    except Exception as exc:  # noqa: BLE001 – Fehler im Lauf festhalten, nicht crashen
        Simulationslauf.objects.filter(pk=lauf_id).update(
            status=Simulationslauf.Status.FEHLER, fehler_text=str(exc)
        )
