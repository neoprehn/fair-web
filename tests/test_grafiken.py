"""Tests für das Risikotoleranz-Overlay der LEC-Kurve (Phase 5)."""

import pytest

from apps.berechnung.views import toleranz_overlay


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
