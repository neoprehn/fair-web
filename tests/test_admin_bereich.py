"""Tests für die globale App-Konfiguration (Phase 7, Slice 1)."""

import pytest
from django.urls import reverse

from apps.admin_bereich.models import AppKonfiguration
from apps.szenarien.forms import SzenarioForm
from apps.szenarien.models import Szenario


def _post(**override):
    data = {
        "name": "Phishing", "beschreibung": "", "n_simulations": 1000, "random_seed": 42,
        "LEF-verteilung": "pert", "LEF-low": "1", "LEF-mode": "3", "LEF-high": "6", "LEF-unsicherheit": "2",
        "LM-verteilung": "constant", "LM-constant": "4000", "LM-unsicherheit": "2",
    }
    data.update(override)
    return data


@pytest.mark.django_db
def test_konfiguration_singleton():
    a = AppKonfiguration.load()
    a.standard_seed = 11
    a.save()
    b = AppKonfiguration.load()
    assert a.pk == b.pk == 1
    assert b.standard_seed == 11
    assert AppKonfiguration.objects.count() == 1


@pytest.mark.django_db
def test_form_deaktiviert_globale_felder():
    k = AppKonfiguration.load()
    k.seed_global = True
    k.n_simulations_global = True
    k.save()
    f = SzenarioForm()
    assert f.fields["random_seed"].disabled
    assert f.fields["n_simulations"].disabled


@pytest.mark.django_db
def test_create_erzwingt_globalen_seed_und_anzahl(client):
    k = AppKonfiguration.load()
    k.standard_seed = 777
    k.standard_n_simulations = 5000
    k.seed_global = True
    k.n_simulations_global = True
    k.save()

    resp = client.post(reverse("szenarien:create"),
                       data=_post(name="G", random_seed=5, n_simulations=99))
    assert resp.status_code == 302
    s = Szenario.objects.get(name="G")
    assert s.random_seed == 777
    assert s.n_simulations == 5000


@pytest.mark.django_db
def test_create_erzwingt_globale_risikotoleranz(client):
    k = AppKonfiguration.load()
    k.unternehmens_risikotoleranz = {"type": "constant", "value": 99000}
    k.risikotoleranz_global = True
    k.save()

    resp = client.post(reverse("szenarien:create"),
                       data=_post(name="RT", rt_type="constant", rt_value="123"))
    assert resp.status_code == 302
    s = Szenario.objects.get(name="RT")
    assert s.risikotoleranz == {"type": "constant", "value": 99000}


@pytest.mark.django_db
def test_create_ohne_global_nutzt_eingaben(client):
    # Default-Konfiguration: nichts global -> eigene Werte greifen.
    resp = client.post(reverse("szenarien:create"),
                       data=_post(name="Eigen", random_seed=7, n_simulations=2000,
                                  rt_type="constant", rt_value="5000"))
    assert resp.status_code == 302
    s = Szenario.objects.get(name="Eigen")
    assert s.random_seed == 7 and s.n_simulations == 2000
    assert s.risikotoleranz == {"type": "constant", "value": 5000.0}
