"""Tests für die CRUD-Views der CAM-Szenarien (Ransomware-Vorlage, Phase 5.1)."""

import pytest
from django.urls import reverse

from apps.cam.beispiele import RANSOMWARE_BEISPIEL
from apps.cam.models import CamSzenario


def _post_ransomware(**override):
    """POST-Daten fürs komplette Ransomware-Beispiel (alle Prefixe)."""
    b = RANSOMWARE_BEISPIEL
    data = {k: str(v) for k, v in b["szenario"].items()}
    data.update({f"control-{k}": str(v) for k, v in b["control"].items()})
    for stage in b["stages"]:
        n = stage["reihenfolge"]
        data.update({f"stage{n}-{k}": str(v) for k, v in stage.items()})
    for vk in b["verlustklassen"]:
        klasse = vk["klasse"]
        data.update({f"{klasse}-{k}": str(v) for k, v in vk.items()})
    data.update(override)
    return data


@pytest.mark.django_db
def test_dashboard_zeigt_cam_szenarien(client):
    CamSzenario.objects.create(
        name="Vorhanden", tef_low=1, tef_mode=2, tef_high=3,
        t_containment_low=1, t_containment_mode=2, t_containment_high=3,
        t_resilience_low=1, t_resilience_mode=2, t_resilience_high=3,
        concurrency_low=0.1, concurrency_mode=0.2, concurrency_high=0.3,
    )
    resp = client.get(reverse("cam:dashboard"))
    assert resp.status_code == 200
    assert b"Vorhanden" in resp.content


@pytest.mark.django_db
def test_create_formular_vorbelegt_mit_ransomware_beispiel(client):
    resp = client.get(reverse("cam:create"))
    assert resp.status_code == 200
    assert b"Initial Access" in resp.content
    assert b"EDR / Anti-Malware" in resp.content


@pytest.mark.django_db
def test_create_speichert_alle_stufen_klassen_und_control(client):
    resp = client.post(reverse("cam:create"), data=_post_ransomware(name="Ransomware Test"))
    assert resp.status_code == 302, resp.context["form"].errors if resp.status_code == 200 else None

    s = CamSzenario.objects.get(name="Ransomware Test")
    assert s.stages.count() == 6
    assert s.verlustklassen.count() == 5
    assert hasattr(s, "control")
    assert s.control.name == "EDR / Anti-Malware"

    stufe1 = s.stages.get(reihenfolge=1)
    assert stufe1.name == "Initial Access"
    assert stufe1.outcome_class == "early"

    voller_schaden = s.verlustklassen.get(klasse="full_impact")
    assert voller_schaden.low == 1_000_000


@pytest.mark.django_db
def test_detail_zeigt_stufen_und_verlustklassen(client):
    client.post(reverse("cam:create"), data=_post_ransomware(name="Detail Test"))
    s = CamSzenario.objects.get(name="Detail Test")
    resp = client.get(reverse("cam:detail", kwargs={"pk": s.pk}))
    assert resp.status_code == 200
    assert b"Lateral Movement" in resp.content
    assert b"EDR / Anti-Malware" in resp.content


@pytest.mark.django_db
def test_update_aendert_bestehende_werte_statt_zu_duplizieren(client):
    client.post(reverse("cam:create"), data=_post_ransomware(name="Update Test"))
    s = CamSzenario.objects.get(name="Update Test")

    resp = client.post(
        reverse("cam:update", kwargs={"pk": s.pk}),
        data=_post_ransomware(name="Update Test (geändert)"),
    )
    assert resp.status_code == 302
    s.refresh_from_db()
    assert s.name == "Update Test (geändert)"
    # Update-in-place: weiterhin genau 6 Stufen / 5 Verlustklassen, keine Duplikate.
    assert s.stages.count() == 6
    assert s.verlustklassen.count() == 5


@pytest.mark.django_db
def test_delete_entfernt_cam_szenario(client):
    client.post(reverse("cam:create"), data=_post_ransomware(name="Lösch Test"))
    s = CamSzenario.objects.get(name="Lösch Test")
    resp = client.post(reverse("cam:delete", kwargs={"pk": s.pk}))
    assert resp.status_code == 302
    assert not CamSzenario.objects.filter(pk=s.pk).exists()


@pytest.mark.django_db
def test_ohne_berechtigung_kein_zugriff_auf_create(client, django_user_model):
    from django.test import Client

    anon_user = django_user_model.objects.create_user(username="ohne_rechte", password="pw-test-12345")
    anon_client = Client()
    anon_client.force_login(anon_user)
    resp = anon_client.get(reverse("cam:create"))
    assert resp.status_code == 403
