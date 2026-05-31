"""Tests für das Risikotoleranz-Overlay der LEC-Kurve (Phase 5)."""

import numpy as np
import pytest

from apps.berechnung.views import _knoten_tabelle, schnittpunkt, toleranz_overlay
from apps.berechnung.services import _ergebnis_aus_sample, _histogramm


def _lec(xs, ys):
    return [{"verlust": x, "ueberschreitung": y} for x, y in zip(xs, ys)]


def test_overlay_konstant():
    assert toleranz_overlay({"type": "constant", "value": 50000}) == {"kind": "vline", "value": 50000}


def test_overlay_kurve():
    rt = {"type": "curve", "points": [{"loss": 1000, "level": 1.0}, {"loss": 5000, "level": 0.5}]}
    ov = toleranz_overlay(rt)
    assert ov["kind"] == "curve"
    assert ov["x"] == [1000, 5000] and ov["y"] == [1.0, 0.5]


def test_overlay_none():
    assert toleranz_overlay(None) is None


def test_overlay_verteilung():
    pytest.importorskip("pyfair")
    rt = {"type": "distribution", "distribution": "lognormal",
          "params": {"mean": 10000, "sigma": 0.5}, "samples": 2000}
    ov = toleranz_overlay(rt)
    assert ov["kind"] == "curve" and len(ov["x"]) > 0
    # Exceedance fällt monoton.
    assert ov["y"][0] >= ov["y"][-1]


def test_schnittpunkt_vline():
    # Fallende LEC von 1.0 auf 0.0 über 0..10000; vline bei 5000.
    lec = _lec(np.linspace(0, 10000, 11), np.linspace(1.0, 0.0, 11))
    sp = schnittpunkt(lec, {"kind": "vline", "value": 5000})
    assert sp["loss"] == 5000
    assert sp["tolerance"] == pytest.approx(0.5, abs=1e-6)


def test_schnittpunkt_kurve():
    # LEC fällt, Toleranzkurve steigt -> genau ein Schnittpunkt.
    lec = _lec(np.linspace(0, 10000, 11), np.linspace(1.0, 0.0, 11))
    ov = {"kind": "curve", "x": [0, 10000], "y": [0.0, 1.0]}
    sp = schnittpunkt(lec, ov)
    assert sp is not None
    assert sp["loss"] == pytest.approx(5000, rel=0.05)
    assert sp["tolerance"] == pytest.approx(0.5, abs=0.05)


def test_schnittpunkt_ohne_overlay():
    lec = _lec([0, 1], [1.0, 0.0])
    assert schnittpunkt(lec, None) is None
    assert schnittpunkt(None, {"kind": "vline", "value": 1}) is None


def test_perzentile_im_ergebnis():
    erg = _ergebnis_aus_sample(np.arange(1, 101, dtype=float))
    assert set(erg["perzentile"].keys()) == {"10", "20", "50", "80", "90", "95", "99"}
    # Monoton steigend über die Stufen.
    werte = [erg["perzentile"][s] for s in ("10", "20", "50", "80", "90", "95", "99")]
    assert werte == sorted(werte)


def test_histogramm_struktur():
    h = _histogramm(np.arange(0, 100, dtype=float), bins=10)
    assert len(h["x"]) == 10 and len(h["y"]) == 10
    assert sum(h["y"]) == 100  # jede Beobachtung in genau einem Bin
    assert h["breite"] == pytest.approx(99 / 10, rel=0.01)


def test_histogramm_leer():
    h = _histogramm(np.array([], dtype=float))
    assert h == {"x": [], "y": [], "breite": 0.0}


def test_knoten_tabelle_reihenfolge_und_format():
    knoten = {
        "Risk": {"status": "berechnet", "mittelwert": 12345.678, "stdev": 100.0,
                 "min": 0.0, "max": 99999.0, "p90": 50000.0, "p95": 70000.0},
        "POA": {"status": "eingabe", "mittelwert": 0.5, "stdev": 0.1, "min": 0.0,
                "max": 1.0, "p90": 0.7, "p95": 0.8, "verteilung": "beta",
                "params": {"mean": 0.5, "k": 10}, "confidence": "90%"},
    }
    zeilen = _knoten_tabelle(knoten)
    namen = [z["name"] for z in zeilen]
    # POA steht in _TABELLE_ORDER vor Risk.
    assert namen.index("Probability of Action") < namen.index("Risk (berechnet)")
    poa = next(z for z in zeilen if z["name"].startswith("Probability"))
    assert poa["verteilung"] == "beta" and poa["confidence"] == "90%"
    assert poa["mean"] == "0,5000"  # Wahrscheinlichkeit -> 4 Nachkommastellen
    risk = next(z for z in zeilen if z["name"].startswith("Risk"))
    assert risk["mean"] == "12.345,68"  # Geldwert -> Tausenderpunkt, 2 Dezimal
