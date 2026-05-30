"""Tests für die kontextbasierte Risikotoleranz (Konstant/Kurve/Verteilung)."""

import pytest
from django.urls import reverse

from apps.szenarien.models import Szenario


def _post(name, **rt):
    data = {
        "name": name, "beschreibung": "", "n_simulations": 1000, "random_seed": 42,
        "LEF-verteilung": "pert", "LEF-low": "1", "LEF-mode": "3", "LEF-high": "6", "LEF-unsicherheit": "2",
        "LM-verteilung": "constant", "LM-constant": "4000", "LM-unsicherheit": "2",
    }
    data.update(rt)
    return data


@pytest.mark.django_db
def test_konstante_toleranz(client):
    client.post(reverse("szenarien:create"), data=_post("K", rt_type="constant", rt_value="50000"))
    s = Szenario.objects.get(name="K")
    assert s.risikotoleranz == {"type": "constant", "value": 50000.0}


@pytest.mark.django_db
def test_verteilungs_toleranz_lognormal(client):
    client.post(reverse("szenarien:create"), data=_post(
        "V", rt_type="distribution", rt_dist="lognormal",
        rt_ln_mean="10000", rt_ln_sigma="0.5", rt_samples="20000"))
    s = Szenario.objects.get(name="V")
    assert s.risikotoleranz == {
        "type": "distribution", "distribution": "lognormal",
        "params": {"mean": 10000.0, "sigma": 0.5}, "samples": 20000,
    }


@pytest.mark.django_db
def test_kurven_toleranz(client):
    client.post(reverse("szenarien:create"), data=_post(
        "Kurve", rt_type="curve",
        rt_curve='[{"loss":"1000","level":"1.0"},{"loss":"5000","level":"0.5"}]'))
    s = Szenario.objects.get(name="Kurve")
    assert s.risikotoleranz == {
        "type": "curve",
        "points": [{"loss": 1000.0, "level": 1.0}, {"loss": 5000.0, "level": 0.5}],
    }


@pytest.mark.django_db
def test_keine_toleranz(client):
    client.post(reverse("szenarien:create"), data=_post("Ohne"))
    s = Szenario.objects.get(name="Ohne")
    assert s.risikotoleranz is None
