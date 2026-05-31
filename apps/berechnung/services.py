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

from apps.szenarien import fair_tree


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
        # VaR-Stufen (Perzentile des Jahresschadens).
        "perzentile": {str(p): perz(p) for p in (10, 20, 50, 80, 90, 95, 99)},
        "lec": lec,
    }


def _histogramm(arr, bins=40):
    """Histogramm (Balken) aus einem Sample: Balkenmitten + Häufigkeiten."""
    import numpy as np

    arr = np.asarray(arr, dtype=float)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        return {"x": [], "y": [], "breite": 0.0}
    counts, kanten = np.histogram(arr, bins=bins)
    mitten = (kanten[:-1] + kanten[1:]) / 2.0
    breite = float(kanten[1] - kanten[0]) if len(kanten) > 1 else 0.0
    return {"x": [float(m) for m in mitten],
            "y": [int(c) for c in counts],
            "breite": breite}


def _knoten_stats(df, szenario):
    """Statistik je berechnetem FAIR-Knoten (für Ergebnis-Baum + Tabelle).

    Berechnete Knoten: Mittelwert/StdAbw/Min/Max/P90/P95. Eingabe-Knoten
    zusätzlich Verteilung/Parameter/Konfidenz (für Tooltip + Tabelle).
    """
    import numpy as np
    from apps.szenarien.fair_confidence import CONFIDENCE_DISTRIBUTIONS

    eingaben = {f.faktor: f for f in szenario.faktoren.all()}
    knoten = {}
    for spalte in df.columns:
        serie = df[spalte].dropna()
        if serie.empty:
            continue
        code = "Risk" if spalte == "Risk" else fair_tree.CODE_FUER_NAME.get(spalte)
        if code is None:
            continue
        arr = serie.to_numpy()
        eintrag = {
            "status": "eingabe" if code in eingaben else "berechnet",
            "mittelwert": float(arr.mean()),
            "stdev": float(arr.std()),
            "min": float(arr.min()),
            "max": float(arr.max()),
            "p90": float(np.percentile(arr, 90)),
            "p95": float(np.percentile(arr, 95)),
        }
        if code in eingaben:
            fe = eingaben[code]
            eintrag["verteilung"] = fe.verteilung
            eintrag["params"] = fe.params
            eintrag["confidence"] = fe.confidence_level if fe.verteilung in CONFIDENCE_DISTRIBUTIONS and fe.verteilung != "beta" else None
            eintrag["angreifertyp"] = fe.angreifertyp
        knoten[code] = eintrag
    return knoten


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
    import pandas as pd
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
        teile.append(model.export_results())  # alle Knoten-Spalten

        erzeugt += n
        i += 1
        if fortschritt:
            fortschritt(min(100, round(erzeugt / n_simulations * 100)))

    combined = pd.concat(teile, ignore_index=True)
    ergebnis = _ergebnis_aus_sample(combined["Risk"].to_numpy())
    ergebnis["knoten"] = _knoten_stats(combined, szenario)
    # Histogramme für die Auswertungs-Grafiken.
    ergebnis["verteilung_hist"] = _histogramm(combined["Risk"].to_numpy())
    lef_spalte = fair_tree.target("LEF")  # "Loss Event Frequency"
    if lef_spalte in combined.columns:
        ergebnis["haeufigkeit_hist"] = _histogramm(combined[lef_spalte].to_numpy())
    return ergebnis


def simuliere_meta(szenarien, n_simulations, random_seed, fortschritt=None):
    """Gemeinsamer Lauf über mehrere Szenarien (Gesamtrisiko = Summe).

    Baut je Szenario ein FairModel (eigener Seed → unabhängige Ziehungen,
    gleiche ``n_simulations``) und summiert via ``FairMetaModel``. Liefert
    ``{"gesamt": <kennzahlen>, "szenarien": [{pk, name, stats}, ...]}``.
    """
    import pyfair

    szenarien = list(szenarien)
    if not szenarien:
        raise ValueError("Keine Szenarien ausgewählt.")

    models = []
    keys = []
    n = len(szenarien)
    for i, sz in enumerate(szenarien):
        inputs = sz.fair_inputs()
        if not inputs:
            raise ValueError(f"Szenario „{sz.name}“ hat keine FAIR-Faktoren.")
        key = f"{sz.name}__{sz.pk}"  # eindeutiger Spaltenname im MetaModel
        model = pyfair.FairModel(
            name=key, n_simulations=n_simulations, random_seed=random_seed + i
        )
        for target, kwargs in inputs.items():
            model.input_data(target, **kwargs)
        models.append(model)
        keys.append((sz, key))
        if fortschritt:
            # +1, damit die abschließende Meta-Rechnung noch Platz hat.
            fortschritt(round((i + 1) / (n + 1) * 100))

    meta = pyfair.FairMetaModel(name="Gesamt", models=models, mode="sum")
    meta.calculate_all()
    df = meta.export_results()

    ergebnis = {
        "gesamt": _ergebnis_aus_sample(df["Risk"].to_numpy()),
        "szenarien": [
            {"pk": sz.pk, "name": sz.name, "stats": _ergebnis_aus_sample(df[key].to_numpy())}
            for sz, key in keys
        ],
    }
    if fortschritt:
        fortschritt(100)
    return ergebnis


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


def starte_meta_async(meta_id):
    """Startet einen Meta-Lauf im Hintergrund-Thread."""
    thread = threading.Thread(target=_thread_target_meta, args=(meta_id,), daemon=True)
    thread.start()
    return thread


def _thread_target_meta(meta_id):
    try:
        _run_meta(meta_id)
    finally:
        connection.close()


def _run_meta(meta_id):
    """Führt einen Meta-Lauf aus und pflegt Status/Fortschritt (synchron, testbar)."""
    from .models import MetaLauf, Simulationslauf

    try:
        lauf = MetaLauf.objects.get(pk=meta_id)
        lauf.status = Simulationslauf.Status.LAEUFT
        lauf.fortschritt = 0
        lauf.save(update_fields=["status", "fortschritt", "aktualisiert_am"])

        def melde(prozent):
            MetaLauf.objects.filter(pk=meta_id).update(fortschritt=prozent)

        ergebnis = simuliere_meta(
            lauf.szenarien.all(), lauf.n_simulations, lauf.random_seed, fortschritt=melde
        )

        lauf.status = Simulationslauf.Status.FERTIG
        lauf.fortschritt = 100
        lauf.ergebnis = ergebnis
        lauf.save(update_fields=["status", "fortschritt", "ergebnis", "aktualisiert_am"])
    except Exception as exc:  # noqa: BLE001
        MetaLauf.objects.filter(pk=meta_id).update(
            status=Simulationslauf.Status.FEHLER, fehler_text=str(exc)
        )
