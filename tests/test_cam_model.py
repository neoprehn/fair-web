"""Tests für das CAM-Szenario-Datenmodell (Phase 5.1)."""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.cam.models import CamControl, CamSzenario, CamStage, CamVerlustklasse


@pytest.mark.django_db
def test_szenario_str_und_defaults():
    s = CamSzenario.objects.create(
        name="Test-Szenario",
        tef_low=5, tef_mode=10, tef_high=20,
        t_containment_low=1, t_containment_mode=3, t_containment_high=10,
        t_resilience_low=2, t_resilience_mode=7, t_resilience_high=21,
        concurrency_low=0.2, concurrency_mode=0.4, concurrency_high=0.6,
    )
    assert str(s) == "Test-Szenario"
    assert s.n_simulations == 20_000
    assert s.random_seed == 42


@pytest.mark.django_db
def test_stufe_reihenfolge_pro_szenario_eindeutig():
    s = CamSzenario.objects.create(
        name="X", tef_low=1, tef_mode=2, tef_high=3,
        t_containment_low=1, t_containment_mode=2, t_containment_high=3,
        t_resilience_low=1, t_resilience_mode=2, t_resilience_high=3,
        concurrency_low=0.1, concurrency_mode=0.2, concurrency_high=0.3,
    )
    CamStage.objects.create(
        szenario=s, reihenfolge=1, name="Stufe A",
        coverage=0.9, visibility=0.9, vis_reliability=0.9,
        recognition=0.9, rec_reliability=0.9, monitoring_cadence=0.1,
        mon_reliability=0.9, duration=0.5, progression_probability=0.9,
        review_independence=0.5, outcome_class=CamStage.OutcomeKlasse.EARLY,
    )
    with pytest.raises(IntegrityError):
        CamStage.objects.create(
            szenario=s, reihenfolge=1, name="Stufe B (Duplikat)",
            coverage=0.9, visibility=0.9, vis_reliability=0.9,
            recognition=0.9, rec_reliability=0.9, monitoring_cadence=0.1,
            mon_reliability=0.9, duration=0.5, progression_probability=0.9,
            review_independence=0.5, outcome_class=CamStage.OutcomeKlasse.MID,
        )


@pytest.mark.django_db
def test_verlustklasse_sortierung_folgt_kill_chain_nicht_einfuegereihenfolge():
    """Reihenfolge ist Früh -> Mittel -> Spät -> Voller Schaden -> Angreifer scheitert,
    unabhängig davon, in welcher Reihenfolge die Zeilen angelegt wurden."""
    s = CamSzenario.objects.create(
        name="X", tef_low=1, tef_mode=2, tef_high=3,
        t_containment_low=1, t_containment_mode=2, t_containment_high=3,
        t_resilience_low=1, t_resilience_mode=2, t_resilience_high=3,
        concurrency_low=0.1, concurrency_mode=0.2, concurrency_high=0.3,
    )
    # Bewusst in "falscher" (nicht Kill-Chain-)Reihenfolge angelegt.
    for klasse in ("attacker_fails", "late", "early", "full_impact", "mid"):
        CamVerlustklasse.objects.create(
            szenario=s, klasse=klasse, verteilung="pert", params={"low": 1, "mode": 2, "high": 3}
        )
    assert list(s.verlustklassen.values_list("klasse", flat=True)) == [
        "early", "mid", "late", "full_impact", "attacker_fails",
    ]


@pytest.mark.django_db
def test_verlustklasse_pro_szenario_eindeutig():
    s = CamSzenario.objects.create(
        name="X", tef_low=1, tef_mode=2, tef_high=3,
        t_containment_low=1, t_containment_mode=2, t_containment_high=3,
        t_resilience_low=1, t_resilience_mode=2, t_resilience_high=3,
        concurrency_low=0.1, concurrency_mode=0.2, concurrency_high=0.3,
    )
    CamVerlustklasse.objects.create(
        szenario=s, klasse="early", verteilung="pert", params={"low": 1, "mode": 2, "high": 3}
    )
    with pytest.raises(IntegrityError):
        CamVerlustklasse.objects.create(
            szenario=s, klasse="early", verteilung="pert", params={"low": 4, "mode": 5, "high": 6}
        )


@pytest.mark.django_db
def test_verlustklasse_to_distribution_je_verteilung():
    """Jede der vier erlaubten Verteilungen (magnitude-Typ, siehe
    fair_tree.DISTS_BY_TYP["magnitude"]) muss auf das richtige pyfair_cam-
    Distribution-Objekt mit den richtigen Parametern abbilden."""
    pytest.importorskip("pyfair_cam")
    from pyfair_cam import BetaPert, LogNormal, Normal, PointEstimate

    pert = CamVerlustklasse(verteilung="pert", params={"low": 1_000, "mode": 2_000, "high": 5_000})
    dist = pert.to_distribution()
    assert isinstance(dist, BetaPert)
    assert (dist.low, dist.mode, dist.high) == (1_000, 2_000, 5_000)

    lognormal = CamVerlustklasse(verteilung="lognormal", params={"mean": 50_000, "stdev": 10_000})
    dist = lognormal.to_distribution()
    assert isinstance(dist, LogNormal)
    assert (dist.mean, dist.stdev) == (50_000, 10_000)

    normal = CamVerlustklasse(verteilung="normal", params={"mean": 50_000, "stdev": 10_000})
    dist = normal.to_distribution()
    assert isinstance(dist, Normal)
    assert (dist.mean, dist.stdev) == (50_000, 10_000)

    constant = CamVerlustklasse(verteilung="constant", params={"constant": 42_000})
    dist = constant.to_distribution()
    assert isinstance(dist, PointEstimate)
    assert dist.value == 42_000


@pytest.mark.django_db
def test_verlustklasse_clean_meldet_fehlende_pflichtparameter():
    unvollstaendig = CamVerlustklasse(verteilung="lognormal", params={"mean": 50_000})
    with pytest.raises(ValidationError):
        unvollstaendig.clean()

    falsche_pert_reihenfolge = CamVerlustklasse(
        verteilung="pert", params={"low": 10, "mode": 5, "high": 20}
    )
    with pytest.raises(ValidationError):
        falsche_pert_reihenfolge.clean()


@pytest.mark.django_db
def test_control_ist_oneto_one_pro_szenario():
    s = CamSzenario.objects.create(
        name="X", tef_low=1, tef_mode=2, tef_high=3,
        t_containment_low=1, t_containment_mode=2, t_containment_high=3,
        t_resilience_low=1, t_resilience_mode=2, t_resilience_high=3,
        concurrency_low=0.1, concurrency_mode=0.2, concurrency_high=0.3,
    )
    CamControl.objects.create(
        szenario=s, name="Control 1",
        intended_efficacy_low=0.7, intended_efficacy_mode=0.8, intended_efficacy_high=0.9,
        variant_efficacy_low=0.1, variant_efficacy_mode=0.2, variant_efficacy_high=0.3,
        variance_frequency_lambda=4, variance_frequency_range=0.4,
        variance_duration_low=2, variance_duration_mode=5, variance_duration_high=10,
        coverage_low=0.8, coverage_mode=0.9, coverage_high=0.99,
    )
    with pytest.raises(IntegrityError):
        CamControl.objects.create(
            szenario=s, name="Control 2 (Duplikat)",
            intended_efficacy_low=0.7, intended_efficacy_mode=0.8, intended_efficacy_high=0.9,
            variant_efficacy_low=0.1, variant_efficacy_mode=0.2, variant_efficacy_high=0.3,
            variance_frequency_lambda=4, variance_frequency_range=0.4,
            variance_duration_low=2, variance_duration_mode=5, variance_duration_high=10,
            coverage_low=0.8, coverage_mode=0.9, coverage_high=0.99,
        )
