"""Tests für Szenariocluster (organisatorische Gruppen)."""

import pytest
from django.contrib.auth.models import Group
from django.test import Client
from django.urls import reverse

from apps.szenarien.models import Cluster, Szenario


def _client_in_gruppe(django_user_model, gruppe):
    user = django_user_model.objects.create_user(
        username=f"u_{gruppe.lower()}", password="pw-test-12345"
    )
    user.groups.add(Group.objects.get(name=gruppe))
    c = Client()
    c.force_login(user)
    return c


@pytest.mark.django_db
def test_cluster_anlegen(client):
    a = Szenario.objects.create(name="A")
    b = Szenario.objects.create(name="B")
    resp = client.post(reverse("szenarien:cluster_create"),
                       data={"name": "Projekt X", "beschreibung": "", "szenarien": [a.pk, b.pk]})
    assert resp.status_code == 302
    c = Cluster.objects.get(name="Projekt X")
    assert set(c.szenarien.values_list("pk", flat=True)) == {a.pk, b.pk}
    assert set(a.cluster.values_list("pk", flat=True)) == {c.pk}


@pytest.mark.django_db
def test_dashboard_filtert_nach_cluster(client):
    a = Szenario.objects.create(name="Drin")
    Szenario.objects.create(name="Draussen")
    c = Cluster.objects.create(name="Nur-A")
    c.szenarien.add(a)
    html = client.get(reverse("szenarien:dashboard") + f"?cluster={c.pk}").content.decode()
    assert "Drin" in html
    assert "Draussen" not in html


@pytest.mark.django_db
def test_betrachter_darf_keinen_cluster_anlegen(django_user_model):
    c = _client_in_gruppe(django_user_model, "Betrachter")
    assert c.get(reverse("szenarien:cluster_create")).status_code == 403


@pytest.mark.django_db
def test_analyst_darf_cluster_anlegen(django_user_model):
    c = _client_in_gruppe(django_user_model, "Analyst")
    assert c.get(reverse("szenarien:cluster_create")).status_code == 200
