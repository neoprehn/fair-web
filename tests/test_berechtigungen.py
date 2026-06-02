"""Tests für rollenbasierte Rechte (Phase 7, Slice 3)."""

import pytest
from django.contrib.auth.models import Group
from django.test import Client
from django.urls import reverse

from apps.berechnung import views as berechnung_views
from apps.szenarien.models import FaktorEingabe, Szenario


def _client_in_gruppe(django_user_model, gruppe):
    user = django_user_model.objects.create_user(
        username=f"u_{gruppe.lower()}", password="pw-test-12345"
    )
    user.groups.add(Group.objects.get(name=gruppe))
    c = Client()
    c.force_login(user)
    return c


def _post_lef_lm(**override):
    data = {
        "name": "Rollen-Test", "beschreibung": "", "n_simulations": 1000, "random_seed": 42,
        "LEF-verteilung": "pert", "LEF-low": "1", "LEF-mode": "3", "LEF-high": "6", "LEF-unsicherheit": "2",
        "LM-verteilung": "constant", "LM-constant": "4000", "LM-unsicherheit": "2",
    }
    data.update(override)
    return data


def _szenario_mit_faktoren():
    s = Szenario.objects.create(name="S", n_simulations=200)
    FaktorEingabe.objects.create(szenario=s, faktor="LEF", verteilung="pert",
                                 params={"low": 1, "mode": 3, "high": 6})
    FaktorEingabe.objects.create(szenario=s, faktor="LM", verteilung="constant",
                                 params={"constant": 4000})
    return s


@pytest.mark.django_db
def test_gruppen_existieren_mit_rechten():
    assert Group.objects.get(name="Analyst").permissions.filter(codename="add_szenario").exists()
    assert not Group.objects.get(name="Betrachter").permissions.filter(codename="add_szenario").exists()
    assert Group.objects.get(name="Betrachter").permissions.filter(codename="view_szenario").exists()
    assert Group.objects.get(name="Konfigurator").permissions.filter(
        codename="change_appkonfiguration").exists()


@pytest.mark.django_db
def test_betrachter_darf_nicht_anlegen(django_user_model):
    c = _client_in_gruppe(django_user_model, "Betrachter")
    assert c.get(reverse("szenarien:create")).status_code == 403


@pytest.mark.django_db
def test_betrachter_darf_nicht_simulieren(django_user_model):
    s = _szenario_mit_faktoren()
    c = _client_in_gruppe(django_user_model, "Betrachter")
    resp = c.post(reverse("berechnung:starten", kwargs={"szenario_pk": s.pk}))
    assert resp.status_code == 403


@pytest.mark.django_db
def test_betrachter_darf_ansehen(django_user_model):
    s = _szenario_mit_faktoren()
    c = _client_in_gruppe(django_user_model, "Betrachter")
    assert c.get(reverse("szenarien:dashboard")).status_code == 200
    assert c.get(reverse("szenarien:detail", kwargs={"pk": s.pk})).status_code == 200


@pytest.mark.django_db
def test_analyst_darf_anlegen(django_user_model):
    c = _client_in_gruppe(django_user_model, "Analyst")
    assert c.get(reverse("szenarien:create")).status_code == 200
    resp = c.post(reverse("szenarien:create"), data=_post_lef_lm(name="VonAnalyst"))
    assert resp.status_code == 302
    assert Szenario.objects.filter(name="VonAnalyst").exists()


@pytest.mark.django_db
def test_dashboard_ui_betrachter_ohne_aktionen(django_user_model):
    _szenario_mit_faktoren()
    c = _client_in_gruppe(django_user_model, "Betrachter")
    html = c.get(reverse("szenarien:dashboard")).content.decode()
    assert "Neues Szenario" not in html
    assert "gemeinsam berechnen" not in html
    assert "Bearbeiten" not in html


@pytest.mark.django_db
def test_dashboard_ui_analyst_mit_aktionen(django_user_model):
    _szenario_mit_faktoren()
    c = _client_in_gruppe(django_user_model, "Analyst")
    html = c.get(reverse("szenarien:dashboard")).content.decode()
    assert "Neues Szenario" in html
    assert "Bearbeiten" in html


@pytest.mark.django_db
def test_detail_ui_betrachter_ohne_berechnen(django_user_model):
    s = _szenario_mit_faktoren()
    c = _client_in_gruppe(django_user_model, "Betrachter")
    html = c.get(reverse("szenarien:detail", kwargs={"pk": s.pk})).content.decode()
    # Kein Berechnen-/Bearbeiten-/Loeschen-Knopf (Aktions-URLs fehlen).
    assert reverse("berechnung:starten", kwargs={"szenario_pk": s.pk}) not in html
    assert reverse("szenarien:update", kwargs={"pk": s.pk}) not in html
    assert reverse("szenarien:delete", kwargs={"pk": s.pk}) not in html


@pytest.mark.django_db
def test_analyst_darf_simulieren(django_user_model, monkeypatch):
    s = _szenario_mit_faktoren()
    monkeypatch.setattr(berechnung_views, "starte_simulation_async", lambda pk: None)
    c = _client_in_gruppe(django_user_model, "Analyst")
    resp = c.post(reverse("berechnung:starten", kwargs={"szenario_pk": s.pk}))
    assert resp.status_code == 302  # darf -> Lauf angelegt, Weiterleitung
