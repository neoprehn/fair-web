"""Konfidenz-/Unsicherheits-Tabelle – Spiegel von pyfair.

Die eigentliche Quelle der Wahrheit ist ``pyfair.utility.confidence_mapping``.
pyfair ist zur Laufzeit der Web-App aber nicht installiert (nur als Engine in
Phase 4), darum halten wir hier eine Kopie für Anzeige + Validierung vor.
``tests/test_confidence_sync.py`` stellt sicher, dass die Kopie identisch bleibt.
"""

# pyfair-Konfidenzstufen -> Formparameter je Verteilung
CONFIDENCE_DEFAULTS = {
    "very_low": {"beta": {"k": 4}, "lognormal": {"sigma": 0.25}, "poisson": {"range": 2.5}, "pert": {"gamma": 10}},
    "low": {"beta": {"k": 7}, "lognormal": {"sigma": 0.4}, "poisson": {"range": 0.75}, "pert": {"gamma": 8}},
    "moderate": {"beta": {"k": 15}, "lognormal": {"sigma": 0.6}, "poisson": {"range": 0.4}, "pert": {"gamma": 4}},
    "high": {"beta": {"k": 40}, "lognormal": {"sigma": 0.9}, "poisson": {"range": 0.25}, "pert": {"gamma": 3}},
    "very_high": {"beta": {"k": 100}, "lognormal": {"sigma": 1.2}, "poisson": {"range": 0.15}, "pert": {"gamma": 2}},
}

# Verteilungen mit Konfidenz-Formparameter (nur hier ist der Slider sinnvoll).
CONFIDENCE_DISTRIBUTIONS = ("pert", "lognormal", "poisson", "beta")

# Unsicherheits-Slider: 0 = niedrigste Unsicherheit ... 4 = höchste.
# Invertiert zur pyfair-"confidence" (wenig Unsicherheit = hohe Konfidenz).
UNSICHERHEIT_TO_CONFIDENCE = ["very_high", "high", "moderate", "low", "very_low"]
UNSICHERHEIT_LABELS = ["sehr niedrig", "niedrig", "mittel", "hoch", "sehr hoch"]
UNSICHERHEIT_DEFAULT = 2  # entspricht "moderate"
UNSICHERHEIT_MIN = 0
UNSICHERHEIT_MAX = 4
