"""Tests für die Unsicherheits-/Konfidenz-Anbindung (Phase 3, Slider).

Sichert insbesondere ab, dass unsere Kopie der Konfidenz-Tabelle identisch
mit pyfair bleibt (Single Source of Truth = pyfair).
"""

import pytest

from apps.szenarien import fair_confidence
from apps.szenarien.models import FaktorEingabe


def test_unsicherheit_mappt_invertiert_auf_confidence():
    f = FaktorEingabe(verteilung="pert")
    f.unsicherheit = 0
    assert f.confidence_level == "very_high"   # wenig Unsicherheit -> hohe Konfidenz
    f.unsicherheit = 2
    assert f.confidence_level == "moderate"
    f.unsicherheit = 4
    assert f.confidence_level == "very_low"    # viel Unsicherheit -> niedrige Konfidenz


def test_to_fair_kwargs_nur_confidence_distributionen():
    pert = FaktorEingabe(verteilung="pert", params={"low": 1, "mode": 2, "high": 3})
    assert pert.to_fair_kwargs()["confidence"] == "moderate"

    konstant = FaktorEingabe(verteilung="constant", params={"constant": 5})
    assert "confidence" not in konstant.to_fair_kwargs()

    normal = FaktorEingabe(verteilung="normal", params={"mean": 1, "stdev": 1})
    assert "confidence" not in normal.to_fair_kwargs()


def test_confidence_shape_aufloesung():
    pert = FaktorEingabe(verteilung="pert")
    pert.unsicherheit = 2  # moderate -> gamma 4
    assert pert.confidence_shape == {"gamma": 4}

    konstant = FaktorEingabe(verteilung="constant")
    assert konstant.confidence_shape is None


def test_kopie_stimmt_mit_pyfair_ueberein():
    """Unsere Tabelle muss exakt pyfair entsprechen."""
    cm = pytest.importorskip("pyfair.utility.confidence_mapping")
    assert fair_confidence.CONFIDENCE_DEFAULTS == cm.get_confidence_defaults()
    assert set(fair_confidence.CONFIDENCE_DISTRIBUTIONS) == set(
        cm.get_distribution_defaults().keys()
    )
