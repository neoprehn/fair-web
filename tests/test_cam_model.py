"""Tests für das CAM-Szenario-Datenmodell (Phase 5.1)."""

import pytest
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
def test_verlustklasse_pro_szenario_eindeutig():
    s = CamSzenario.objects.create(
        name="X", tef_low=1, tef_mode=2, tef_high=3,
        t_containment_low=1, t_containment_mode=2, t_containment_high=3,
        t_resilience_low=1, t_resilience_mode=2, t_resilience_high=3,
        concurrency_low=0.1, concurrency_mode=0.2, concurrency_high=0.3,
    )
    CamVerlustklasse.objects.create(szenario=s, klasse="early", low=1, mode=2, high=3)
    with pytest.raises(IntegrityError):
        CamVerlustklasse.objects.create(szenario=s, klasse="early", low=4, mode=5, high=6)


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
