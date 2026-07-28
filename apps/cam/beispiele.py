"""Referenz-Datensatz: das Ransomware-Beispiel aus pyfair-cam.

1:1 übertragen aus ``pyfair-cam/examples/ransomware_scenario.py`` (KB-Quelle:
``04_Detection_Response_Measurement.md``, "Worked Example: Ransomware
Attack"). Wird von den Tests (``tests/test_cam_views.py``) als vollständiger
POST-Payload genutzt. Neue CAM-Szenarien starten mit leerem Formular; wer das
Beispiel in der App braucht, legt es einmal manuell an (oder klont ein
bestehendes Szenario).
"""

RANSOMWARE_BEISPIEL = {
    "szenario": {
        "name": "Ransomware Szenario",
        "beschreibung": (
            "Sechsstufige Kill Chain (Initial Access bis Execution) mit EDR/"
            "Anti-Malware-Control auf der Frequenz-Seite. Beispiel aus der "
            "FAIR-CAM Knowledge Base."
        ),
        "n_simulations": 20_000,
        "random_seed": 42,
        "tef_low": 5, "tef_mode": 10, "tef_high": 20,
        "t_containment_low": 1, "t_containment_mode": 3, "t_containment_high": 10,
        "t_resilience_low": 2, "t_resilience_mode": 7, "t_resilience_high": 21,
        "concurrency_low": 0.2, "concurrency_mode": 0.4, "concurrency_high": 0.6,
    },
    "control": {
        "name": "EDR / Anti-Malware",
        "intended_efficacy_low": 0.70, "intended_efficacy_mode": 0.85, "intended_efficacy_high": 0.95,
        "variant_efficacy_low": 0.02, "variant_efficacy_mode": 0.10, "variant_efficacy_high": 0.25,
        "variance_frequency_lambda": 4, "variance_frequency_range": 0.4,
        "variance_duration_low": 2, "variance_duration_mode": 5, "variance_duration_high": 10,
        "coverage_low": 0.85, "coverage_mode": 0.95, "coverage_high": 0.99,
    },
    "stages": [
        {
            "reihenfolge": 1, "name": "Initial Access",
            "coverage": 0.95, "visibility": 0.70, "vis_reliability": 0.95,
            "recognition": 0.40, "rec_reliability": 0.90, "monitoring_cadence": 0.042,
            "mon_reliability": 0.95, "duration": 0.25, "progression_probability": 0.90,
            "review_independence": 0.40, "outcome_class": "early",
        },
        {
            "reihenfolge": 2, "name": "Persistence",
            "coverage": 0.98, "visibility": 0.85, "vis_reliability": 0.95,
            "recognition": 0.60, "rec_reliability": 0.92, "monitoring_cadence": 0.042,
            "mon_reliability": 0.95, "duration": 0.50, "progression_probability": 0.85,
            "review_independence": 0.55, "outcome_class": "early",
        },
        {
            "reihenfolge": 3, "name": "Priv Escalation",
            "coverage": 0.96, "visibility": 0.80, "vis_reliability": 0.94,
            "recognition": 0.75, "rec_reliability": 0.90, "monitoring_cadence": 0.042,
            "mon_reliability": 0.94, "duration": 0.50, "progression_probability": 0.80,
            "review_independence": 0.60, "outcome_class": "mid",
        },
        {
            "reihenfolge": 4, "name": "Lateral Movement",
            "coverage": 0.92, "visibility": 0.90, "vis_reliability": 0.96,
            "recognition": 0.65, "rec_reliability": 0.88, "monitoring_cadence": 0.042,
            "mon_reliability": 0.92, "duration": 1.00, "progression_probability": 0.75,
            "review_independence": 0.65, "outcome_class": "mid",
        },
        {
            "reihenfolge": 5, "name": "Data Staging",
            "coverage": 0.88, "visibility": 0.75, "vis_reliability": 0.92,
            "recognition": 0.55, "rec_reliability": 0.85, "monitoring_cadence": 0.042,
            "mon_reliability": 0.90, "duration": 0.75, "progression_probability": 0.70,
            "review_independence": 0.50, "outcome_class": "late",
        },
        {
            "reihenfolge": 6, "name": "Execution",
            "coverage": 0.85, "visibility": 0.60, "vis_reliability": 0.90,
            "recognition": 0.45, "rec_reliability": 0.80, "monitoring_cadence": 0.042,
            "mon_reliability": 0.88, "duration": 0.25, "progression_probability": 0.95,
            "review_independence": 0.45, "outcome_class": "late",
        },
    ],
    "verlustklassen": [
        {"klasse": "early", "low": 2_000, "mode": 8_000, "high": 30_000},
        {"klasse": "mid", "low": 25_000, "mode": 75_000, "high": 250_000},
        {"klasse": "late", "low": 200_000, "mode": 500_000, "high": 2_000_000},
        {"klasse": "full_impact", "low": 1_000_000, "mode": 3_000_000, "high": 5_000_000},
        {"klasse": "attacker_fails", "low": 2_000, "mode": 5_000, "high": 15_000},
    ],
}
