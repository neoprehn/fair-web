"""Tests für die erweiterten Verteilungen (Beta/Poisson/Lognormal) je Faktortyp."""

import pytest

from apps.szenarien.forms import FaktorEingabeForm
from apps.szenarien.models import FaktorEingabe, Szenario


@pytest.mark.django_db
def test_beta_mittelwert_k():
    form = FaktorEingabeForm(
        data={"verteilung": "beta", "unsicherheit": 2, "beta_mode": "mean_k",
              "beta_mean": 0.3, "beta_k": 15},
        faktor_code="VULN",
    )
    assert form.is_valid(), form.errors
    assert form.instance.params == {"mean": 0.3, "k": 15}
    assert "confidence" not in form.instance.to_fair_kwargs()


@pytest.mark.django_db
def test_beta_konfidenzintervall():
    form = FaktorEingabeForm(
        data={"verteilung": "beta", "unsicherheit": 2, "beta_mode": "ci",
              "beta_low": 0.2, "beta_high": 0.6, "beta_confidence": 90},
        faktor_code="VULN",
    )
    assert form.is_valid(), form.errors
    assert form.instance.params == {"low": 0.2, "high": 0.6, "confidence": 0.9}
    kw = form.instance.to_fair_kwargs()
    assert kw["input_mode"] == "confidence_interval"


@pytest.mark.django_db
def test_beta_mittelwert_ueber_eins_fehler():
    form = FaktorEingabeForm(
        data={"verteilung": "beta", "unsicherheit": 2, "beta_mode": "mean_k",
              "beta_mean": 1.5, "beta_k": 15},
        faktor_code="VULN",
    )
    assert not form.is_valid()


@pytest.mark.django_db
def test_lognormal_betrag():
    form = FaktorEingabeForm(
        data={"verteilung": "lognormal", "unsicherheit": 2, "ln_mean": 50000},
        faktor_code="LM",
    )
    assert form.is_valid(), form.errors
    assert form.instance.params == {"mean": 50000}


def test_erlaubte_verteilungen_je_typ():
    vuln = [w for w, _ in FaktorEingabeForm(faktor_code="VULN").fields["verteilung"].choices]
    lef = [w for w, _ in FaktorEingabeForm(faktor_code="LEF").fields["verteilung"].choices]
    lm = [w for w, _ in FaktorEingabeForm(faktor_code="LM").fields["verteilung"].choices]
    assert "beta" in vuln and "normal" not in vuln and "lognormal" not in vuln
    assert "pert" in lef and "beta" not in lef and "poisson" not in lef  # Poisson entfernt
    assert "lognormal" in lm and "poisson" not in lm


@pytest.mark.django_db
def test_neue_verteilungen_rechnen_in_pyfair():
    """End-to-End: Beta/Lognormal müssen in pyfair durchlaufen."""
    pytest.importorskip("pyfair")
    from apps.berechnung.services import simuliere

    s = Szenario.objects.create(name="Mix", n_simulations=300)
    FaktorEingabe.objects.create(szenario=s, faktor="TEF", verteilung="pert",
                                 params={"low": 1, "mode": 4, "high": 10}, unsicherheit=2)
    FaktorEingabe.objects.create(szenario=s, faktor="VULN", verteilung="beta",
                                 params={"mean": 0.3, "k": 15}, unsicherheit=2)
    FaktorEingabe.objects.create(szenario=s, faktor="LM", verteilung="lognormal",
                                 params={"mean": 50000}, unsicherheit=2)
    assert s.schnitt_ist_gueltig()
    ergebnis = simuliere(s, 300, 42, batches=2)
    assert ergebnis["n"] == 300 and ergebnis["mittelwert"] > 0
