# pyfair (neoprehn-Fork)

**FAIR-Risikomodell (Factor Analysis of Information Risk) in Python.** pyfair
automatisiert FAIR-Monte-Carlo-Risikosimulationen über eine einfache API.
fair-web nutzt den **erweiterten Fork** [neoprehn/pyfair](https://github.com/neoprehn/pyfair)
(gegenüber dem [Original](https://pyfair.readthedocs.io/en/latest/) ausgebaut).

Grundlage sind die Begriffe der Open-Group-Standards
[Open FAIR™ Risk Taxonomy (O-RT)](https://publications.opengroup.org/c13k) und
[Open FAIR™ Risk Analysis (O-RA)](https://publications.opengroup.org/c13g).
„Open FAIR" ist eine Marke der Open Group.

## Installation

Als editierbares Paket aus dem Fork-Verzeichnis (so wird es in fair-web genutzt):

```bash
pip install -e ../fair
```

Das Original ist auf PyPI verfügbar (`pip install pyfair`) – für den erweiterten
Funktionsumfang ist jedoch der Fork nötig.

## Schnellstart

```python
import pyfair

# Modell 1 über LEF (PERT), Primärverlust (PERT) und Sekundärverlust (konstant)
model1 = pyfair.FairModel(name="Modell 1", n_simulations=10_000)
model1.input_data('Loss Event Frequency', low=20, mode=100, high=900)
model1.input_data('Primary Loss', low=3_000_000, mode=3_500_000, high=5_000_000)
model1.input_data('Secondary Loss', constant=3_500_000)
model1.calculate_all()

# Modell 2 über LEF (Normal) und Schadenshöhe LM (PERT)
model2 = pyfair.FairModel(name="Modell 2", n_simulations=10_000)
model2.input_data('Loss Event Frequency', mean=.3, stdev=.1)
model2.input_data('Loss Magnitude', low=2_000_000_000, mode=3_000_000_000, high=5_000_000_000)
model2.calculate_all()

# Meta-Modell (Summe mehrerer Modelle)
mm = pyfair.FairMetaModel(name='Mein Meta-Modell', models=[model1, model2])
mm.calculate_all()

# Bericht (Vergleich Modell 2 vs. Meta-Modell)
fsr = pyfair.FairSimpleReport([model1, mm])
fsr.to_html('output.html')
```

## Erweiterungen des Forks

Gegenüber dem Original-pyfair zusätzlich enthalten:

- **Strukturierte Eingabe-API** für `input_data`: `distribution`, `params`,
  `confidence`, `input_mode` – statt nur der Kurzform-Argumente.
- **Konfidenz-Mapping**: qualitative Stufen (`very_low` … `very_high`) werden
  zu Formparametern (gamma/sigma/range/k) aufgelöst – zentral in
  `pyfair/utility/confidence_mapping.py`.
- **Beta-Konfidenzintervall** als Eingabeart: `low`/`high`/`confidence` werden
  zu `mean`/`k` der Beta-Verteilung gefittet.
- Zusätzliche **Verteilungen/Parameter** und die Möglichkeit, explizite
  Formparameter direkt zu übergeben (nutzt fair-web für die editierbaren
  Konfidenz-Vorschlagswerte).

### Original vs. erweiterter Fork im Überblick

| Funktion | Original pyfair | Erweiterter Fork (`neoprehn/pyfair`) |
|---|---|---|
| **Eingabe-API** | nur Kurzform-Schlüsselwörter (`constant`; `mean`/`stdev`; `low`/`mode`/`high`/`gamma`) | zusätzlich **strukturiert**: `distribution` / `params` / `confidence` / `input_mode` (abwärtskompatibel) |
| **Verteilungen** | Constant, Normal, PERT | + **Lognormal**, **Poisson** (unsicheres λ), **Beta** |
| **Qualitative Konfidenz** | – | **Konfidenz-Stufen** `very_low … very_high` → automatische Formparameter (`k`/`sigma`/`range`/`gamma`), zentral & konfigurierbar |
| **Beta-Eingabe** | – | `alpha`/`beta` **oder** `mean`/`k` **oder** **Konfidenzintervall** (`input_mode='confidence_interval'`) |
| **Meta-Modell-Modus** | nur Summe | **`sum`** (Gesamtrisiko) **und** **`compare`** (Delta gegen Baseline-Modell) |
| **Risikotoleranz** | – | Risikotoleranz als **Konstante / Kurve / Verteilung** mit **Schnittpunkt** auf der LEC |
| **CSV-Export** | – | `export_results_csv(...)` mit deutschen Trennzeichen (`;` / `,`) |
| **JSON-Roundtrip** | speichert aufgelöste Parameter | bewahrt die **ursprüngliche Eingabe** (sauberer Roundtrip, `confidence` bleibt erhalten) |
| **Validierung** | grundlegend | strengere Prüfungen: 0–1-Grenzen je FAIR-Faktor, geordnete PERT-Tripel, Nicht-Negativität, Output-Clipping |

!!! info "Fazit"
    Der Fork bleibt **API-kompatibel** zum Original – bestehende Skripte laufen
    unverändert –, ergänzt aber die für praxisnahe Schätzungen wichtigen
    Bausteine: qualitative Unsicherheit, mehr Verteilungen, Vergleichsmodus und
    Risikotoleranz.

## Serialisiertes Modell

Ein Modell lässt sich als JSON speichern/laden:

```json
{
    "Loss Magnitude": { "mean": 100000, "stdev": 20000 },
    "Loss Event Frequency": { "low": 20, "mode": 90, "high": 95, "gamma": 4 },
    "name": "Beispiel-Modell",
    "n_simulations": 10000,
    "random_seed": 42,
    "type": "FairModel"
}
```

## Ausführliche Engine-Doku

Die API ist in eigenen Kapiteln auf pyfair-Detailgrad beschrieben:

- [Installation](installation.md) · [Schnellstart](schnellstart.md)
- [Modelle erstellen](modelle.md) – die `FairModel`-API
- [Eingaben & Verteilungen](eingaben.md) – Legacy + strukturierte API, alle
  Verteilungen, Konfidenz-Mapping
- [Meta-Modelle](metamodelle.md) · [Berichte](berichte.md) ·
  [Serialisierung & Datenbank](serialisierung.md)

!!! note "Stand"
    Diese Kapitel beschreiben gezielt den **neoprehn-Fork**. Eine vollständige
    englische Fassung (DE/EN) ist in Arbeit. Maßgebliche Referenz bei
    Unklarheiten: der [Quellcode des Forks](https://github.com/neoprehn/pyfair).
