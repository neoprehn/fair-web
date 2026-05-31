"""Tests für Szenariovergleiche (Gruppe bestehender Szenarien, Compare/Add)."""

import pytest
from django.urls import reverse

from apps.berechnung import views as berechnung_views
from apps.berechnung.models import MetaLauf
from apps.szenarien.forms import VergleichForm
from apps.szenarien.models import FaktorEingabe, Szenario, Vergleich


def _szenario(name, lm_konstant=1000):
    s = Szenario.objects.create(name=name, n_simulations=300, random_seed=7)
    FaktorEingabe.objects.create(
        szenario=s, faktor="LEF", verteilung="pert",
        params={"low": 1, "mode": 3, "high": 6},
    )
    FaktorEingabe.objects.create(
        szenario=s, faktor="LM", verteilung="constant", params={"constant": lm_konstant},
    )
    return s


@pytest.mark.django_db
def test_vergleich_letzter_lauf():
    a, b = _szenario("A"), _szenario("B", 2000)
    v = Vergleich.objects.create(name="V1")
    v.szenarien.set([a, b])
    assert v.letzter_lauf is None
    lauf = MetaLauf.objects.create(vergleich=v, n_simulations=300, random_seed=42)
    lauf.szenarien.set([a, b])
    assert v.letzter_lauf == lauf


@pytest.mark.django_db
def test_vergleich_form_braucht_zwei():
    a, b = _szenario("A"), _szenario("B")
    f1 = VergleichForm(data={"name": "V", "n_simulations": "1000", "random_seed": "42",
                             "szenarien": [a.pk]})
    assert not f1.is_valid() and "szenarien" in f1.errors
    f2 = VergleichForm(data={"name": "V", "n_simulations": "1000", "random_seed": "42",
                             "szenarien": [a.pk, b.pk]})
    assert f2.is_valid(), f2.errors


@pytest.mark.django_db
def test_vergleich_form_nur_rechenbare_szenarien():
    a = _szenario("A")
    leer = Szenario.objects.create(name="Leer")  # kein gültiger Schnitt
    pks = set(VergleichForm().fields["szenarien"].queryset.values_list("pk", flat=True))
    assert a.pk in pks and leer.pk not in pks


@pytest.mark.django_db
def test_vergleich_create_view(client):
    a, b = _szenario("A"), _szenario("B")
    resp = client.post(reverse("szenarien:vergleich_create"),
                       data={"name": "Mein Vergleich", "n_simulations": "1000",
                             "random_seed": "42", "szenarien": [a.pk, b.pk]})
    assert resp.status_code == 302
    v = Vergleich.objects.get()
    assert v.name == "Mein Vergleich"
    assert set(v.szenarien.values_list("pk", flat=True)) == {a.pk, b.pk}


@pytest.mark.django_db
def test_vergleich_form_referenz_muss_enthalten_sein():
    a, b, c = _szenario("A"), _szenario("B"), _szenario("C")
    f = VergleichForm(data={"name": "V", "n_simulations": "1000", "random_seed": "42",
                            "szenarien": [a.pk, b.pk], "referenz_szenario": c.pk})
    assert not f.is_valid() and "referenz_szenario" in f.errors


@pytest.mark.django_db
def test_meta_detail_referenz_overlay_und_schnittpunkte(client):
    pytest.importorskip("pyfair")
    from apps.berechnung import services
    a, b = _szenario("A", 1000), _szenario("B", 2000)
    a.risikotoleranz = {"type": "constant", "value": 5000}
    a.save()
    v = Vergleich.objects.create(name="V", n_simulations=300, random_seed=42, referenz_szenario=a)
    v.szenarien.set([a, b])
    lauf = MetaLauf.objects.create(vergleich=v, n_simulations=300, random_seed=42)
    lauf.szenarien.set([a, b])
    services._run_meta(lauf.pk)

    resp = client.get(reverse("berechnung:meta_lauf", kwargs={"pk": lauf.pk}))
    assert resp.status_code == 200
    assert resp.context["referenz_overlay"]["kind"] == "vline"
    assert resp.context["referenz_name"] == "A"
    assert len(resp.context["vergleich_schnittpunkte"]) == 2


@pytest.mark.django_db
def test_vergleich_starten(client, monkeypatch):
    a, b = _szenario("A"), _szenario("B", 2000)
    v = Vergleich.objects.create(name="V", n_simulations=500, random_seed=9)
    v.szenarien.set([a, b])
    monkeypatch.setattr(berechnung_views, "starte_meta_async", lambda meta_id: None)

    resp = client.post(reverse("berechnung:vergleich_starten", kwargs={"pk": v.pk}))

    lauf = MetaLauf.objects.get()
    assert resp.status_code == 302
    assert resp.url == reverse("berechnung:meta_lauf", kwargs={"pk": lauf.pk})
    assert lauf.vergleich_id == v.pk
    assert lauf.n_simulations == 500 and lauf.random_seed == 9
    assert set(lauf.szenarien.values_list("pk", flat=True)) == {a.pk, b.pk}


@pytest.mark.django_db
def test_vergleich_starten_zu_wenige(client):
    a = _szenario("A")
    v = Vergleich.objects.create(name="V")
    v.szenarien.set([a])
    resp = client.post(reverse("berechnung:vergleich_starten", kwargs={"pk": v.pk}))
    assert resp.status_code == 302
    assert resp.url == reverse("szenarien:dashboard")
    assert not MetaLauf.objects.exists()
