"""Tests für das Szenario-Datenmodell (Phase 3)."""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.szenarien.models import FaktorEingabe, Szenario


# ---------------------------------------------------------------------------
# Reine Logik (ohne DB)
# ---------------------------------------------------------------------------

def test_fair_target_mapping():
    lef = FaktorEingabe(faktor=FaktorEingabe.Faktor.LEF)
    lm = FaktorEingabe(faktor=FaktorEingabe.Faktor.LM)
    assert lef.fair_target == "Loss Event Frequency"
    assert lm.fair_target == "Loss Magnitude"


def test_to_fair_kwargs_strukturierte_api():
    faktor = FaktorEingabe(
        faktor=FaktorEingabe.Faktor.LM,
        verteilung=FaktorEingabe.Verteilung.PERT,
        params={"low": 1000, "mode": 5000, "high": 20000},
    )
    assert faktor.to_fair_kwargs() == {
        "distribution": "pert",
        # Default-Unsicherheit (Stufe 2 = moderate) -> gamma 4 explizit in params.
        "params": {"low": 1000, "mode": 5000, "high": 20000, "gamma": 4},
    }


def test_clean_meldet_fehlende_pflichtparameter():
    faktor = FaktorEingabe(
        faktor=FaktorEingabe.Faktor.LEF,
        verteilung=FaktorEingabe.Verteilung.NORMAL,
        params={"mean": 5},  # stdev fehlt
    )
    with pytest.raises(ValidationError) as exc:
        faktor.clean()
    assert "stdev" in str(exc.value)


def test_clean_meldet_falsche_pert_reihenfolge():
    faktor = FaktorEingabe(
        faktor=FaktorEingabe.Faktor.LEF,
        verteilung=FaktorEingabe.Verteilung.PERT,
        params={"low": 10, "mode": 2, "high": 5},  # mode < low
    )
    with pytest.raises(ValidationError):
        faktor.clean()


def test_clean_akzeptiert_gueltige_pert():
    faktor = FaktorEingabe(
        faktor=FaktorEingabe.Faktor.LEF,
        verteilung=FaktorEingabe.Verteilung.PERT,
        params={"low": 1, "mode": 3, "high": 10},
    )
    faktor.clean()  # darf nicht werfen


# ---------------------------------------------------------------------------
# momente() - Grundlage für den "Kennwerte"-Aggregationsmodus (Slice 3)
# ---------------------------------------------------------------------------

def test_momente_constant():
    faktor = FaktorEingabe(faktor="LM", verteilung="constant", params={"constant": 4000})
    assert faktor.momente() == (4000.0, 0.0)


def test_momente_normal():
    faktor = FaktorEingabe(faktor="LM", verteilung="normal", params={"mean": 5000, "stdev": 200})
    mean, var = faktor.momente()
    assert mean == pytest.approx(5000)
    assert var == pytest.approx(200 ** 2)


def test_momente_lognormal():
    # Ohne Konfidenz-Override: sigma kommt aus der (moderate = Default-Unsicherheit) Konfidenztabelle.
    faktor = FaktorEingabe(faktor="LM", verteilung="lognormal", params={"mean": 5000})
    mean, var = faktor.momente()
    kwargs = faktor.to_fair_kwargs()
    sigma = kwargs["params"]["sigma"]
    assert mean == pytest.approx(5000)
    import math
    assert var == pytest.approx((math.exp(sigma ** 2) - 1) * 5000 ** 2)


def test_momente_pert_gegen_pyfair_nachgerechnet():
    """Regressionswert: pyfairs FairBetaPert weicht von der Lehrbuch-PERT-Varianzformel ab
    (nachgerechnet: (mean-low)(high-mean)/(gamma+3) ergibt 1.607.143, pyfairs tatsächliche
    Beta-Kurve 1.361.111 für dieselben Parameter) - momente() muss der tatsächlichen
    pyfair-Kurve folgen, nicht der Lehrbuchformel."""
    pytest.importorskip("pyfair")
    faktor = FaktorEingabe(
        faktor="LM", verteilung="pert", params={"low": 1000, "mode": 3000, "high": 8000, "gamma": 4},
    )
    mean, var = faktor.momente()
    assert mean == pytest.approx(3500.0)
    assert var == pytest.approx(1_361_111.11, rel=1e-4)


# ---------------------------------------------------------------------------
# Mit Datenbank
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_szenario_str_und_defaults():
    s = Szenario.objects.create(name="Ransomware")
    assert str(s) == "Ransomware"
    assert s.n_simulations == 10_000
    assert s.random_seed == 42


@pytest.mark.django_db
def test_fair_inputs_sammelt_alle_faktoren():
    s = Szenario.objects.create(name="Datenverlust")
    FaktorEingabe.objects.create(
        szenario=s,
        faktor=FaktorEingabe.Faktor.LEF,
        verteilung=FaktorEingabe.Verteilung.PERT,
        params={"low": 1, "mode": 3, "high": 6},
    )
    FaktorEingabe.objects.create(
        szenario=s,
        faktor=FaktorEingabe.Faktor.LM,
        verteilung=FaktorEingabe.Verteilung.CONSTANT,
        params={"constant": 4000},
    )
    inputs = s.fair_inputs()
    assert inputs == {
        "Loss Event Frequency": {
            "distribution": "pert",
            # PERT moderate -> gamma 4 explizit in params (kein "confidence" mehr).
            "params": {"low": 1, "mode": 3, "high": 6, "gamma": 4},
        },
        "Loss Magnitude": {
            "distribution": "constant",
            "params": {"constant": 4000},  # Konstant ohne Konfidenz
        },
    }


@pytest.mark.django_db
def test_ein_faktor_pro_szenario_eindeutig():
    s = Szenario.objects.create(name="Doppelt")
    FaktorEingabe.objects.create(
        szenario=s, faktor=FaktorEingabe.Faktor.LEF, params={"low": 1, "mode": 2, "high": 3}
    )
    with pytest.raises(IntegrityError):
        FaktorEingabe.objects.create(
            szenario=s, faktor=FaktorEingabe.Faktor.LEF, params={"low": 1, "mode": 2, "high": 3}
        )


# ---------------------------------------------------------------------------
# Integration mit pyfair (übersprungen, falls pyfair nicht installiert)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_fair_inputs_erzeugen_lauffaehiges_pyfair_modell():
    pyfair = pytest.importorskip("pyfair")

    s = Szenario.objects.create(name="Integration", n_simulations=1000)
    FaktorEingabe.objects.create(
        szenario=s,
        faktor=FaktorEingabe.Faktor.LEF,
        verteilung=FaktorEingabe.Verteilung.PERT,
        params={"low": 1, "mode": 3, "high": 6},
    )
    FaktorEingabe.objects.create(
        szenario=s,
        faktor=FaktorEingabe.Faktor.LM,
        verteilung=FaktorEingabe.Verteilung.CONSTANT,
        params={"constant": 4000},
    )

    model = pyfair.FairModel(name=s.name, n_simulations=s.n_simulations)
    for target, kwargs in s.fair_inputs().items():
        model.input_data(target, **kwargs)
    model.calculate_all()

    results = model.export_results()
    assert len(results) == 1000
