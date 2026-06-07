"""Tests für Formulare und CRUD-Views der Szenarien (FAIR-Baum)."""

import pytest
from django.urls import reverse

from apps.szenarien.forms import FaktorEingabeForm
from apps.szenarien.models import Szenario


# ---------------------------------------------------------------------------
# FaktorEingabeForm (fester Faktor je Knoten, eingeschränkte Verteilungen)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_form_pert_baut_params():
    form = FaktorEingabeForm(
        data={"verteilung": "pert", "unsicherheit": 2, "low": 1, "mode": 3, "high": 6},
        faktor_code="LEF",
    )
    assert form.is_valid(), form.errors
    assert form.instance.params == {"low": 1, "mode": 3, "high": 6}
    assert form.instance.faktor == "LEF"


@pytest.mark.django_db
def test_form_constant_ignoriert_fremde_felder():
    form = FaktorEingabeForm(
        data={"verteilung": "constant", "unsicherheit": 2, "constant": 4000, "low": 99},
        faktor_code="LM",
    )
    assert form.is_valid(), form.errors
    assert form.instance.params == {"constant": 4000}


@pytest.mark.django_db
def test_form_meldet_falsche_pert_reihenfolge():
    form = FaktorEingabeForm(
        data={"verteilung": "pert", "unsicherheit": 2, "low": 10, "mode": 2, "high": 5},
        faktor_code="LEF",
    )
    assert not form.is_valid()


def test_form_verteilungen_je_typ_eingeschraenkt():
    # Wahrscheinlichkeit (VULN): keine Normalverteilung anbieten.
    vuln = FaktorEingabeForm(faktor_code="VULN")
    werte = [w for w, _ in vuln.fields["verteilung"].choices]
    assert "normal" not in werte and "pert" in werte
    # Häufigkeit (LEF): Normalverteilung erlaubt.
    lef = FaktorEingabeForm(faktor_code="LEF")
    assert "normal" in [w for w, _ in lef.fields["verteilung"].choices]


# ---------------------------------------------------------------------------
# CRUD-Views (Baum-Schnitt)
# ---------------------------------------------------------------------------

def _post_lef_lm(**override):
    """POST-Daten: Standard-Schnitt LEF + LM (Default-Modus 'direkt')."""
    data = {
        "name": "Phishing", "beschreibung": "", "n_simulations": 1000, "random_seed": 42,
        "LEF-verteilung": "pert", "LEF-low": "1", "LEF-mode": "3", "LEF-high": "6", "LEF-unsicherheit": "2",
        "LM-verteilung": "constant", "LM-constant": "4000", "LM-unsicherheit": "2",
    }
    data.update(override)
    return data


@pytest.mark.django_db
def test_dashboard_zeigt_szenarien(client):
    Szenario.objects.create(name="Vorhanden")
    resp = client.get(reverse("szenarien:dashboard"))
    assert resp.status_code == 200
    assert b"Vorhanden" in resp.content


@pytest.mark.django_db
def test_create_standard_schnitt_lef_lm(client):
    resp = client.post(reverse("szenarien:create"), data=_post_lef_lm())
    assert resp.status_code == 302
    s = Szenario.objects.get(name="Phishing")
    assert set(s.schnitt_codes()) == {"LEF", "LM"}
    assert s.fair_inputs()["Loss Magnitude"] == {
        "distribution": "constant", "params": {"constant": 4000.0},
    }


@pytest.mark.django_db
def test_create_aufgeschluesselter_schnitt(client):
    # LEF aufschlüsseln -> TEF + Vulnerability angeben; LM direkt.
    data = {
        "name": "Tief", "beschreibung": "", "n_simulations": 1000, "random_seed": 42,
        "modus-LEF": "aufschluesseln", "modus-TEF": "direkt", "modus-VULN": "direkt",
        "TEF-verteilung": "pert", "TEF-low": "1", "TEF-mode": "4", "TEF-high": "10", "TEF-unsicherheit": "2",
        "VULN-verteilung": "constant", "VULN-constant": "0,3", "VULN-unsicherheit": "2",
        "LM-verteilung": "constant", "LM-constant": "5000", "LM-unsicherheit": "2",
    }
    resp = client.post(reverse("szenarien:create"), data=data)
    assert resp.status_code == 302
    s = Szenario.objects.get(name="Tief")
    assert set(s.schnitt_codes()) == {"TEF", "VULN", "LM"}
    assert s.schnitt_ist_gueltig()


@pytest.mark.django_db
def test_create_wahrscheinlichkeit_ueber_eins_fehler(client):
    data = {
        "name": "Ungueltig", "beschreibung": "", "n_simulations": 1000, "random_seed": 42,
        "modus-LEF": "aufschluesseln", "modus-TEF": "direkt", "modus-VULN": "direkt",
        "TEF-verteilung": "constant", "TEF-constant": "5", "TEF-unsicherheit": "2",
        "VULN-verteilung": "constant", "VULN-constant": "1,5", "VULN-unsicherheit": "2",  # > 1
        "LM-verteilung": "constant", "LM-constant": "5000", "LM-unsicherheit": "2",
    }
    resp = client.post(reverse("szenarien:create"), data=data)
    assert resp.status_code == 200  # neu gerendert
    assert not Szenario.objects.filter(name="Ungueltig").exists()


@pytest.mark.django_db
def test_detail_view(client):
    s = Szenario.objects.create(name="Detail")
    resp = client.get(reverse("szenarien:detail", kwargs={"pk": s.pk}))
    assert resp.status_code == 200
    assert b"Detail" in resp.content


@pytest.mark.django_db
def test_update_wechselt_schnitt(client):
    s = Szenario.objects.create(name="Alt")
    resp = client.post(reverse("szenarien:update", kwargs={"pk": s.pk}), data=_post_lef_lm(name="Neu"))
    assert resp.status_code == 302
    s.refresh_from_db()
    assert s.name == "Neu"
    assert set(s.schnitt_codes()) == {"LEF", "LM"}


@pytest.mark.django_db
def test_create_deutsche_zahlen(client):
    # Tausenderpunkt + Komma-Dezimal müssen geparst werden.
    data = _post_lef_lm(name="DE")
    data["LM-constant"] = "1.000.000"   # eine Million
    data["LEF-mode"] = "3,5"            # Komma-Dezimal
    resp = client.post(reverse("szenarien:create"), data=data)
    assert resp.status_code == 302
    s = Szenario.objects.get(name="DE")
    assert s.faktoren.get(faktor="LM").params == {"constant": 1000000.0}
    assert s.faktoren.get(faktor="LEF").params["mode"] == 3.5


@pytest.mark.django_db
def test_klonen_erzeugt_kopie(client):
    client.post(reverse("szenarien:create"), data=_post_lef_lm(name="Orig"))
    orig = Szenario.objects.get(name="Orig")
    resp = client.post(reverse("szenarien:clone", kwargs={"pk": orig.pk}))
    assert resp.status_code == 302
    klon = Szenario.objects.get(name="Orig (Kopie)")
    assert klon.pk != orig.pk
    assert klon.faktoren.count() == orig.faktoren.count() == 2
    assert resp.url == reverse("szenarien:update", kwargs={"pk": klon.pk})


@pytest.mark.django_db
def test_speichern_als_neu_legt_neues_an_original_bleibt(client):
    client.post(reverse("szenarien:create"), data=_post_lef_lm(name="Basis"))
    orig = Szenario.objects.get(name="Basis")
    n_vorher = Szenario.objects.count()
    resp = client.post(reverse("szenarien:update", kwargs={"pk": orig.pk}),
                       data=_post_lef_lm(name="Variante", speichern_als_neu="1"))
    assert resp.status_code == 302
    assert Szenario.objects.count() == n_vorher + 1
    neu = Szenario.objects.get(name="Variante")
    assert neu.pk != orig.pk
    orig.refresh_from_db()
    assert orig.name == "Basis"


@pytest.mark.django_db
def test_delete_entfernt_szenario(client):
    s = Szenario.objects.create(name="Weg")
    resp = client.post(reverse("szenarien:delete", kwargs={"pk": s.pk}))
    assert resp.status_code == 302
    assert not Szenario.objects.filter(pk=s.pk).exists()
