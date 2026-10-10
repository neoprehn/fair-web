# pyfair (neoprehn fork)

**FAIR risk model (Factor Analysis of Information Risk) in Python.** pyfair
automates FAIR Monte Carlo risk simulations through a simple API. fair-web
uses the **extended fork** [neoprehn/pyfair](https://github.com/neoprehn/pyfair)
(built out beyond the [original](https://pyfair.readthedocs.io/en/latest/)).

The foundation is the terminology of the Open Group standards
[Open FAIR™ Risk Taxonomy (O-RT)](https://publications.opengroup.org/c13k) and
[Open FAIR™ Risk Analysis (O-RA)](https://publications.opengroup.org/c13g).
"Open FAIR" is a trademark of The Open Group.

## Installation

As an editable package from the fork directory (this is how fair-web uses
it):

```bash
pip install -e ../fair
```

The original is available on PyPI (`pip install pyfair`) – the extended
feature set, however, requires the fork.

## Quickstart

```python
import pyfair

# Model 1 via LEF (PERT), primary loss (PERT) and secondary loss (constant)
model1 = pyfair.FairModel(name="Model 1", n_simulations=10_000)
model1.input_data('Loss Event Frequency', low=20, mode=100, high=900)
model1.input_data('Primary Loss', low=3_000_000, mode=3_500_000, high=5_000_000)
model1.input_data('Secondary Loss', constant=3_500_000)
model1.calculate_all()

# Model 2 via LEF (Normal) and loss magnitude LM (PERT)
model2 = pyfair.FairModel(name="Model 2", n_simulations=10_000)
model2.input_data('Loss Event Frequency', mean=.3, stdev=.1)
model2.input_data('Loss Magnitude', low=2_000_000_000, mode=3_000_000_000, high=5_000_000_000)
model2.calculate_all()

# Meta-model (sum of several models)
mm = pyfair.FairMetaModel(name='My Meta-Model', models=[model1, model2])
mm.calculate_all()

# Report (comparing model 2 vs. the meta-model)
fsr = pyfair.FairSimpleReport([model1, mm])
fsr.to_html('output.html')
```

## What the fork adds

Compared to the original pyfair, the fork additionally includes:

- A **structured input API** for `input_data`: `distribution`, `params`,
  `confidence`, `input_mode` – instead of only the short-form arguments.
- **Confidence mapping**: qualitative levels (`very_low` … `very_high`) are
  resolved into shape parameters (gamma/sigma/range/k) – centralized in
  `pyfair/utility/confidence_mapping.py`.
- **Beta confidence interval** as an input type: `low`/`high`/`confidence`
  are fitted to `mean`/`k` of the Beta distribution.
- Additional **distributions/parameters** and the ability to pass explicit
  shape parameters directly (used by fair-web for its editable confidence
  default values).

### Original vs. extended fork at a glance

| Feature | Original pyfair | Extended fork (`neoprehn/pyfair`) |
|---|---|---|
| **Input API** | short-form keywords only (`constant`; `mean`/`stdev`; `low`/`mode`/`high`/`gamma`) | additionally **structured**: `distribution` / `params` / `confidence` / `input_mode` (backward compatible) |
| **Distributions** | Constant, Normal, PERT | + **Lognormal**, **Poisson** (uncertain λ), **Beta** |
| **Qualitative confidence** | – | **confidence levels** `very_low … very_high` → automatic shape parameters (`k`/`sigma`/`range`/`gamma`), centralized & configurable |
| **Beta input** | – | `alpha`/`beta` **or** `mean`/`k` **or** **confidence interval** (`input_mode='confidence_interval'`) |
| **Meta-model mode** | sum only | **`sum`** (total risk) **and** **`compare`** (delta vs. baseline model) |
| **Risk tolerance** | – | risk tolerance as **constant / curve / distribution** with an **intersection point** on the LEC |
| **CSV export** | – | `export_results_csv(...)` with German separators (`;` / `,`) |
| **JSON round trip** | stores resolved parameters | preserves the **original input** (clean round trip, `confidence` is retained) |
| **Validation** | basic | stricter checks: 0–1 bounds per FAIR factor, ordered PERT triples, non-negativity, output clipping |

!!! info "Bottom line"
    The fork remains **API-compatible** with the original – existing scripts
    run unchanged – while adding the building blocks that matter for
    practical estimation: qualitative uncertainty, more distributions, a
    comparison mode and risk tolerance.

## Serialized model

A model can be saved/loaded as JSON:

```json
{
    "Loss Magnitude": { "mean": 100000, "stdev": 20000 },
    "Loss Event Frequency": { "low": 20, "mode": 90, "high": 95, "gamma": 4 },
    "name": "Example Model",
    "n_simulations": 10000,
    "random_seed": 42,
    "type": "FairModel"
}
```

## Full engine documentation

The API is described in its own chapters at pyfair's level of detail:

- [Installation](installation.md) · [Quickstart](schnellstart.md)
- [Building Models](modelle.md) – the `FairModel` API
- [Inputs & Distributions](eingaben.md) – legacy + structured API, all
  distributions, confidence mapping
- [Meta-Models](metamodelle.md) · [Reports](berichte.md) ·
  [Serialization & Database](serialisierung.md)

!!! note "Status"
    These chapters specifically describe the **neoprehn fork**. When in
    doubt, the authoritative reference is the
    [fork's source code](https://github.com/neoprehn/pyfair).
