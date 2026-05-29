"""Tests für Formulare und CRUD-Views der Szenarien (Phase 3)."""

import pytest
from django.urls import reverse

from apps.szenarien.forms import FaktorEingabeForm
from apps.szenarien.models import FaktorEingabe, Szenario


# ---------------------------------------------------------------------------
# FaktorEingabeForm (Verteilungs-Parameter -> params)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_form_pert_baut_params():
    form = FaktorEingabeForm(
        data={"faktor": "LEF", "verteilung": "pert", "low": 1, "mode": 3, "high": 6}
    )
    assert form.is_valid(), form.errors
    assert form.instance.params == {"low": 1, "mode": 3, "high": 6}


@pytest.mark.django_db
def test_form_constant_ignoriert_fremde_felder():
    form = FaktorEingabeForm(
        data={"faktor": "LM", "verteilung": "constant", "constant": 4000, "low": 99}
    )
    assert form.is_valid(), form.errors
    assert form.instance.params == {"constant": 4000}


@pytest.mark.django_db
def test_form_meldet_fehlenden_pflichtparameter():
    form = FaktorEingabeForm(
        data={"faktor": "LEF", "verteilung": "normal", "mean": 5}  # stdev fehlt
    )
    assert not form.is_valid()
    assert "stdev" in str(form.errors)


@pytest.mark.django_db
def test_form_meldet_falsche_pert_reihenfolge():
    form = FaktorEingabeForm(
        data={"faktor": "LEF", "verteilung": "pert", "low": 10, "mode": 2, "high": 5}
    )
    assert not form.is_valid()


# ---------------------------------------------------------------------------
# CRUD-Views
# ---------------------------------------------------------------------------

def _post_data(**szenario_felder):
    """Baut POST-Daten für Szenario-Formular inkl. Faktor-Formset (Prefix 'faktoren')."""
    data = {
        "name": "Phishing",
        "beschreibung": "",
        "n_simulations": 1000,
        "random_seed": 42,
        "faktoren-TOTAL_FORMS": "2",
        "faktoren-INITIAL_FORMS": "0",
        "faktoren-MIN_NUM_FORMS": "0",
        "faktoren-MAX_NUM_FORMS": "2",
        "faktoren-0-faktor": "LEF",
        "faktoren-0-verteilung": "pert",
        "faktoren-0-low": "1",
        "faktoren-0-mode": "3",
        "faktoren-0-high": "6",
        "faktoren-1-faktor": "LM",
        "faktoren-1-verteilung": "constant",
        "faktoren-1-constant": "4000",
    }
    data.update(szenario_felder)
    return data


@pytest.mark.django_db
def test_dashboard_zeigt_szenarien(client):
    Szenario.objects.create(name="Vorhanden")
    resp = client.get(reverse("szenarien:dashboard"))
    assert resp.status_code == 200
    assert b"Vorhanden" in resp.content


@pytest.mark.django_db
def test_create_legt_szenario_mit_faktoren_an(client):
    resp = client.post(reverse("szenarien:create"), data=_post_data())
    assert resp.status_code == 302
    szenario = Szenario.objects.get(name="Phishing")
    assert szenario.faktoren.count() == 2
    assert szenario.fair_inputs()["Loss Magnitude"] == {
        "distribution": "constant",
        "params": {"constant": 4000.0},
    }


@pytest.mark.django_db
def test_create_mit_fehler_speichert_nichts(client):
    daten = _post_data()
    daten["faktoren-0-high"] = "0"  # high < mode -> ungültige PERT
    resp = client.post(reverse("szenarien:create"), data=daten)
    assert resp.status_code == 200  # Formular neu gerendert
    assert not Szenario.objects.filter(name="Phishing").exists()


@pytest.mark.django_db
def test_detail_view(client):
    s = Szenario.objects.create(name="Detail")
    resp = client.get(reverse("szenarien:detail", kwargs={"pk": s.pk}))
    assert resp.status_code == 200
    assert b"Detail" in resp.content


@pytest.mark.django_db
def test_update_aendert_szenario(client):
    s = Szenario.objects.create(name="Alt")
    daten = _post_data(name="Neu")
    daten["faktoren-INITIAL_FORMS"] = "0"
    resp = client.post(reverse("szenarien:update", kwargs={"pk": s.pk}), data=daten)
    assert resp.status_code == 302
    s.refresh_from_db()
    assert s.name == "Neu"
    assert s.faktoren.count() == 2


@pytest.mark.django_db
def test_delete_entfernt_szenario(client):
    s = Szenario.objects.create(name="Weg")
    resp = client.post(reverse("szenarien:delete", kwargs={"pk": s.pk}))
    assert resp.status_code == 302
    assert not Szenario.objects.filter(pk=s.pk).exists()
