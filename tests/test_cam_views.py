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
        data[f"{klasse}-klasse"] = klasse
        data[f"{klasse}-verteilung"] = vk["verteilung"]
        data.update({f"{klasse}-{k}": str(v) for k, v in vk["params"].items()})
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
def test_create_formular_ist_leer(client):
    resp = client.get(reverse("cam:create"))
    assert resp.status_code == 200
    # Kein Auto-Vorbelegen mehr mit dem Ransomware-Beispiel – leeres Formular.
    # ("Initial Access" wird hier bewusst nicht geprüft: das ist jetzt auch eine
    # MITRE-ATT&CK-Tactic-Option im attack_tactic-Dropdown, kollidiert also mit dem
    # gleichnamigen Stufennamen aus dem Beispiel - "Priv Escalation"/"Data Staging"
    # sind dagegen eindeutig nur Beispiel-Stufennamen.)
    assert b"Priv Escalation" not in resp.content
    assert b"Data Staging" not in resp.content
    assert b"EDR / Anti-Malware" not in resp.content


@pytest.mark.django_db
def test_create_formular_zeigt_reiter_und_kill_chain_anker(client):
    resp = client.get(reverse("cam:create"))
    assert resp.status_code == 200
    for label in (b"Prevention", b"Detection", b"Verlustklassen"):
        assert label in resp.content
    for n in range(1, 7):
        assert f'id="stage-{n}"'.encode() in resp.content


@pytest.mark.django_db
def test_create_formular_zeigt_kill_chain_als_cytoscape_graph(client):
    """Kill-Chain ist ein interaktiver Cytoscape-Graph (vendored), kein statisches SVG
    mehr - draggable Knoten, Kanten mit Infos (siehe cam_tree.to_cytoscape_elements)."""
    resp = client.get(reverse("cam:create"))
    html = resp.content.decode()
    assert resp.status_code == 200
    assert "vendor/cytoscape/cytoscape.min.js" in html
    assert 'id="cam-chain-graph"' in html
    assert 'id="chain-elements-data"' in html
    assert "cam-chain-svg" not in html  # altes statisches SVG ist weg


@pytest.mark.django_db
def test_create_formular_zeigt_mitre_attack_ansicht_umschalter(client):
    """Zweite Ansicht neben der Kill-Chain: Umschalter + Vollansicht-Button, sowie
    die attack_tactic-Auswahl je Stufe (CamStageForm, siehe models.CamStage.AttackTactic)."""
    resp = client.get(reverse("cam:create"))
    html = resp.content.decode()
    assert resp.status_code == 200
    assert 'id="cam-view-chain"' in html
    assert 'id="cam-view-attack"' in html
    assert 'id="cam-chain-fullscreen"' in html
    assert 'id="cam-chain-wrap"' in html
    # Je Stufe eine attack_tactic-Auswahl (6 Stufen -> 6 Select-Felder im Formular).
    assert html.count('name="stage1-attack_tactic"') == 1
    assert html.count('name="stage6-attack_tactic"') == 1
    assert "Lateral Movement" in html  # Tactic-Label, kommt aus CamStage.AttackTactic.choices


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
    assert stufe1.attack_tactic == "TA0001"  # MITRE ATT&CK-Zuordnung rundet mit durch

    voller_schaden = s.verlustklassen.get(klasse="full_impact")
    assert voller_schaden.params["low"] == 1_000_000


@pytest.mark.django_db
def test_mitre_attack_ansicht_platziert_stufen_nach_tactic_spalte(client):
    """End-to-end: die im Ransomware-Beispiel hinterlegten attack_tactic-Werte landen
    korrekt als attack_position in chain_elements (siehe cam_tree.attack_position)."""
    import json
    import re

    from apps.cam import cam_tree

    resp = client.post(reverse("cam:create"), data=_post_ransomware(name="ATT&CK Test"))
    assert resp.status_code == 302
    s = CamSzenario.objects.get(name="ATT&CK Test")

    resp = client.get(reverse("cam:update", kwargs={"pk": s.pk}))
    html = resp.content.decode()
    m = re.search(r'<script id="chain-elements-data"[^>]*>(.*?)</script>', html, re.S)
    elements = json.loads(m.group(1))
    stage1 = next(el["data"] for el in elements if el["data"].get("id") == "stage1")  # Initial Access -> TA0001
    stage4 = next(el["data"] for el in elements if el["data"].get("id") == "stage4")  # Lateral Movement -> TA0008

    assert stage1["attack_position"] == cam_tree.attack_position("TA0001")
    assert stage4["attack_position"] == cam_tree.attack_position("TA0008")
    # Lateral Movement (TA0008) kommt in der ATT&CK-Spaltenreihenfolge nach Initial Access (TA0001).
    assert stage4["attack_position"]["x"] > stage1["attack_position"]["x"]


@pytest.mark.django_db
def test_verlustklasse_akzeptiert_nicht_pert_verteilung(client):
    """Verlustklassen sind nicht mehr PERT-fest - eine Klasse per Formular auf
    Normal statt PERT umstellen muss ebenso speichern wie die anderen vier."""
    resp = client.post(reverse("cam:create"), data=_post_ransomware(
        name="Normal-Verlustklasse Test",
        **{"early-verteilung": "normal", "early-mean": "9000", "early-stdev": "2000"},
    ))
    assert resp.status_code == 302, resp.context["form"].errors if resp.status_code == 200 else None

    s = CamSzenario.objects.get(name="Normal-Verlustklasse Test")
    early = s.verlustklassen.get(klasse="early")
    assert early.verteilung == "normal"
    assert early.params == {"mean": 9000.0, "stdev": 2000.0}


@pytest.mark.django_db
def test_detail_zeigt_stufen_und_verlustklassen(client):
    client.post(reverse("cam:create"), data=_post_ransomware(name="Detail Test"))
    s = CamSzenario.objects.get(name="Detail Test")
    resp = client.get(reverse("cam:detail", kwargs={"pk": s.pk}))
    assert resp.status_code == 200
    assert b"Lateral Movement" in resp.content
    assert b"EDR / Anti-Malware" in resp.content


@pytest.mark.django_db
def test_detail_zeigt_annahmen_und_vorschau_button_je_verlustklasse(client):
    """Analog zur FAIR-Szenario-Detailseite: pro Verlustklasse ein Annahmen-Knopf
    (Modal mit Freitext) UND ein separater Vorschau-Knopf (Modal mit Verteilungskurve) -
    zwei getrennte UI-Elemente, nicht nur der reine Parameter-Text."""
    resp = client.post(reverse("cam:create"), data=_post_ransomware(
        name="Vorschau Test",
        **{"early-annahmen": "Branchenwert aus Incident-Statistik."},
    ))
    assert resp.status_code == 302
    s = CamSzenario.objects.get(name="Vorschau Test")

    resp = client.get(reverse("cam:detail", kwargs={"pk": s.pk}))
    html = resp.content.decode()
    assert resp.status_code == 200
    assert html.count("annahmen-modal") >= 5  # ein Annahmen-Knopf je Verlustklasse (+ das Modal selbst)
    assert html.count("vorschau-btn") == 5  # ein Vorschau-Knopf je Verlustklasse
    assert "Branchenwert aus Incident-Statistik." in html
    assert "verteilung-chart" in html

    early = s.verlustklassen.get(klasse="early")
    vorschau = resp.context["verteilung_vorschau"][f"vk{early.pk}"]
    assert vorschau is not None
    assert len(vorschau["x"]) > 0
    assert vorschau["mittelwert"] > 0


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
