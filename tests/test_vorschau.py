"""Tests für die Live-LEC-Vorschau (schnelle Mini-Simulation aus Formulardaten)."""

import pytest
from django.urls import reverse

from apps.szenarien import fair_tree
from apps.szenarien.fair_confidence import UNSICHERHEIT_MIN


def test_simuliere_vorschau_inputs():
    pytest.importorskip("pyfair")
    from apps.berechnung.services import simuliere_vorschau

    inputs = {
        "Loss Event Frequency": {"distribution": "pert",
                                 "params": {"low": 1, "mode": 3, "high": 6}},
        "Loss Magnitude": {"distribution": "constant", "params": {"constant": 4000}},
    }
    erg = simuliere_vorschau(inputs, n_simulations=800)
    assert erg["lec"] and erg["lec"][0]["ueberschreitung"] >= erg["lec"][-1]["ueberschreitung"]
    assert set(erg["perzentile"]) == {"10", "20", "50", "80", "90", "95", "99"}


def test_simuliere_vorschau_leer():
    pytest.importorskip("pyfair")
    from apps.berechnung.services import simuliere_vorschau

    with pytest.raises(ValueError):
        simuliere_vorschau({})


def _post_direkt():
    """Minimaler gültiger Schnitt: LEF (PERT) × LM (konstant), alles 'direkt'."""
    post = {f"modus-{c}": "direkt" for c in fair_tree.NICHT_BLATT}
    post.update({
        "LEF-verteilung": "pert", "LEF-low": "1", "LEF-mode": "3", "LEF-high": "6",
        "LEF-unsicherheit": str(UNSICHERHEIT_MIN), "LEF-beta_mode": "mean_k",
        "LM-verteilung": "constant", "LM-constant": "4000",
        "LM-unsicherheit": str(UNSICHERHEIT_MIN), "LM-beta_mode": "mean_k",
    })
    return post


@pytest.mark.django_db
def test_vorschau_endpoint_ok(client):
    pytest.importorskip("pyfair")
    resp = client.post(reverse("szenarien:lec_vorschau"), _post_direkt())
    assert resp.status_code == 200
    d = resp.json()
    assert d["ok"] is True
    assert d["lec"] and "perzentile" in d


@pytest.mark.django_db
def test_vorschau_endpoint_unvollstaendig(client):
    # Kein gültiger Schnitt / keine Faktorwerte -> ok:false mit Fehlertext.
    resp = client.post(reverse("szenarien:lec_vorschau"), {})
    assert resp.status_code == 200
    d = resp.json()
    assert d["ok"] is False and d["fehler"]


def test_vorschau_get_nicht_erlaubt(client):
    assert client.get(reverse("szenarien:lec_vorschau")).status_code == 405
