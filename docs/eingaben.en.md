# Inputs & Distributions

Every FAIR factor is entered as a **distribution** that the Monte Carlo
simulation draws from. pyfair (fork) supports two input styles, which can be
freely mixed.

## Two input styles

### 1. Legacy (short-form keywords)

pyfair infers the distribution from the combination of keywords used:

| Keywords | Distribution |
|---|---|
| `constant` | Constant |
| `mean`, `stdev` | Normal |
| `low`, `mode`, `high` (`gamma` optional) | PERT |

```python
model.input_data('Loss Magnitude', mean=20_000, stdev=5_000)        # Normal
model.input_data('Loss Event Frequency', low=10, mode=20, high=100)  # PERT
model.input_data('Secondary Loss', constant=3_500)                   # Constant
```

### 2. Structured (fork)

Explicit via `distribution`, `params` and optionally `confidence` /
`input_mode`:

```python
model.input_data(
    'Threat Capability',
    distribution='beta',
    params={'mean': 0.3},
    confidence='moderate',
)
```

| Argument | Meaning |
|---|---|
| `distribution` | `'constant'`, `'normal'`, `'pert'`, `'lognormal'`, `'poisson'`, `'beta'`. |
| `params` | Dictionary of distribution parameters (see below). |
| `confidence` | Qualitative spread: `very_low`, `low`, `moderate`, `high`, `very_high`. |
| `input_mode` | Special input type (currently only `confidence_interval` for `beta`). |

!!! note "Additive & backward compatible"
    The structured API complements the legacy form, it doesn't replace it.
    Existing models keep working unchanged.

## The distributions in detail

### Constant

A fixed value for all iterations.

```python
params={'constant': 50_000}
# Legacy: constant=50_000
```

### Normal

A normal distribution around `mean` with spread `stdev`.

```python
params={'mean': 20_000, 'stdev': 5_000}
# Legacy: mean=20_000, stdev=5_000
```

### PERT (Beta-PERT)

A three-point estimate `low`/`mode`/`high` with shape parameter `gamma`
(default `4`; higher `gamma` = more peaked around `mode`). Requires
`low ≤ mode ≤ high`.

```python
params={'low': 10, 'mode': 20, 'high': 100}          # gamma default 4
params={'low': 10, 'mode': 20, 'high': 100, 'gamma': 8}
# Legacy: low=10, mode=20, high=100, gamma=8
```

### Lognormal

A skewed distribution for loss magnitudes. **`mean`** is the arithmetic
mean on the original scale, **`sigma`** the spread of the underlying normal
distribution. `mean` must be > 0.

```python
params={'mean': 250_000, 'sigma': 0.6}
```

`sigma` can also be set via `confidence` (default `0.6`).

### Poisson

Count frequencies with an **uncertain** `lambda`. `range` spreads `lambda`
symmetrically before drawing:

```
lambda_sample ~ Uniform(lambda · (1 − range), lambda · (1 + range))
variates      ~ Poisson(lambda_sample)
```

```python
params={'lambda': 12, 'range': 0.4}
```

`range` can be set via `confidence` (default `0.4`).

### Beta

For **probabilities / 0–1 factors**. Two parameterizations:

- `alpha` / `beta` – directly, **or**
- `mean` / `k` – with `alpha = mean·k`, `beta = (1−mean)·k`. `k` is the
  "concentration" (higher `k` = narrower). `mean` must lie in [0, 1].

```python
params={'mean': 0.3, 'k': 15}     # k default 15
params={'alpha': 2, 'beta': 5}
```

`k` can be set via `confidence`.

## Confidence mapping

`confidence` replaces the **shape parameter** of the respective distribution
with a stored value. Each distribution has exactly one such parameter:

| Distribution | Shape parameter | Default (without `confidence`) |
|---|---|---|
| `beta` | `k` | 15 |
| `lognormal` | `sigma` | 0.6 |
| `poisson` | `range` | 0.4 |
| `pert` | `gamma` | 4 |

With `confidence`, these values result (higher confidence = narrower
spread; for `poisson` a smaller `range` is narrower, and the `lognormal`
table is deliberately calibrated this way):

| confidence | beta `k` | lognormal `sigma` | poisson `range` | pert `gamma` |
|---|---|---|---|---|
| `very_low` | 4 | 0.25 | 2.5 | 10 |
| `low` | 7 | 0.4 | 0.75 | 8 |
| `moderate` | 15 | 0.6 | 0.4 | 4 |
| `high` | 40 | 0.9 | 0.25 | 3 |
| `very_high` | 100 | 1.2 | 0.15 | 2 |

```python
# Confidence instead of an explicit shape parameter:
model.input_data('Primary Loss', distribution='lognormal',
                 params={'mean': 100_000}, confidence='high')   # sigma = 0.9
```

!!! warning "Not both at once"
    `confidence` and the explicit shape parameter of the same distribution
    are mutually exclusive. `confidence='high'` **and**
    `params={'sigma': 0.5}` for the same input raises a `FairException`.

The tables are defined centrally in
`pyfair/utility/confidence_mapping.py` – fair-web makes the default values
editable in the app configuration.

## Beta confidence interval (`input_mode`)

Instead of `mean`/`k`, a Beta distribution can be fitted from a **central
confidence interval** over [0, 1]. pyfair resolves `mean`/`k` from it:

```python
model.input_data(
    'Threat Capability',
    distribution='beta',
    input_mode='confidence_interval',
    params={'low': 0.2, 'high': 0.6, 'confidence': 0.9},
)
```

Meaning: "With 90% probability, the factor lies between 0.2 and 0.6."
Conditions: `0 ≤ low < high ≤ 1` and `0 < confidence < 1`; `mean`/`k`/
`alpha`/`beta` must **not** be given additionally in that case.

## Value ranges & clipping

Four factors are **probabilities** and must lie in [0, 1] – input
parameters outside [0, 1] are rejected, and the generated samples are
clipped to [0, 1]:

> **Probability of Action**, **Vulnerability**, **Control Strength**,
> **Threat Capability**

All other factors are clipped to **≥ 0** (no negative
frequencies/losses). pyfair additionally checks that numeric parameters
aren't negative and that PERT triples are ordered (`low ≤ mode ≤ high`).
