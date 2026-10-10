# Building Models

The central class is `FairModel`. Each instance represents **one** FAIR
model with its own dependency tree, input parser and calculation engine.

## Constructor

```python
FairModel(name, n_simulations=10_000, random_seed=42,
          model_uuid=None, creation_date=None)
```

| Parameter | Meaning |
|---|---|
| `name` | Human-readable name. |
| `n_simulations` | Number of Monte Carlo iterations (more = more accurate, slower). |
| `random_seed` | Seed for reproducibility – same seed → same result. |
| `model_uuid`, `creation_date` | Assigned automatically. |

!!! warning "UUID/date"
    Don't set `model_uuid` and `creation_date` yourself – they're only meant
    for JSON deserialization and can otherwise break things.

## Entering factors

A FAIR model is populated by entering a **cut** through the
[FAIR tree](fair-taxonomie.md): break each branch down until you can
estimate the factor. You only need to enter the **leaves of your cut** – the
engine calculates upward to `Risk`.

```python
model.input_data(target, **kwargs)
```

`target` is the factor name, `kwargs` the distribution parameters. All input
types are described in detail under
[Inputs & Distributions](eingaben.md). `input_data` returns the model, so
it's **chainable**:

```python
(model
    .input_data('Loss Event Frequency', low=10, mode=20, high=100)
    .input_data('Loss Magnitude', constant=50_000)
    .calculate_all())
```

### Further input methods

| Method | Purpose |
|---|---|
| `input_data(target, **kwargs)` | A single factor (legacy or structured). |
| `bulk_import_data(dict)` | Multiple factors at once (`{target: params}`). |
| `input_multi_data(target, dict)` | Multiple items that aggregate into one factor (mainly secondary losses). |
| `input_raw_data(target, array)` | Feed a ready-made sample directly (length = `n_simulations`). |

```python
model.bulk_import_data({
    'Loss Event Frequency': {'mean': 90, 'stdev': 10},
    'Loss Magnitude': {'constant': 4_000},
})
```

`input_multi_data` for multi-part secondary losses (e.g. reputation + legal):

```python
model.input_multi_data('Secondary Loss', {
    'Reputation': {
        'Secondary Loss Event Frequency': {'constant': 0.4},
        'Secondary Loss Event Magnitude': {'low': 10_000, 'mode': 20_000, 'high': 100_000},
    },
    'Legal': {
        'Secondary Loss Event Frequency': {'constant': 0.2},
        'Secondary Loss Event Magnitude': {'low': 5_000, 'mode': 15_000, 'high': 60_000},
    },
})
```

!!! warning "Raw data"
    `input_raw_data` stores the complete array **uncompressed** in the model
    JSON (it can't be reproduced from parameters). This can bloat serialized
    models significantly.

## Calculating

```python
model.calculate_all()
```

Calculates all still-open nodes. If the required inputs are incomplete, a
`FairException` is raised with the node statuses. You can check this in
advance with:

```python
model.calculation_completed()   # bool
model.get_node_statuses()       # pandas.Series: node -> status
```

Possible statuses include `Supplied` (entered), `Calculable` (can be
calculated), `Calculated` (done) and `Required` (still missing).

### Vulnerability ordering

Internally, `Vulnerability` is calculated from **Threat Capability** (TC)
and **Control Strength** (CS) (TC vs. RS/CS) – the engine automatically
handles the correct ordering.

## Exporting results

| Method | Returns |
|---|---|
| `export_results()` | `pandas.DataFrame` – one column per factor, one row per simulation. |
| `export_results_csv(output_path=None, sep=';', decimal=',', index=False)` | Writes the result table as CSV (default German separators) and returns the path. |
| `export_params()` | Resolved input parameters (dictionary). |

```python
df = model.export_results()
df['Risk'].quantile([0.5, 0.9, 0.95])     # median, P90, P95
model.export_results_csv('results.csv')
```

## Factor names & abbreviations

`input_data` understands full and short names (case-insensitive):

| Factor | Abbreviations |
|---|---|
| Loss Event Frequency | `LEF` |
| Threat Event Frequency | `TEF` |
| Vulnerability | `V`, `S`, `Susceptibility` |
| Contact Frequency | `C`, `CF` |
| Probability of Action | `A`, `PoA`, `POA` |
| Threat Capability | `TC` |
| Control Strength | `CS` |
| Loss Magnitude | `LM` |
| Primary Loss | `PL` |
| Secondary Loss | `SL` |
| Secondary Loss Event Frequency | `SLEF` |
| Secondary Loss Event Magnitude | `SLEM` |

## Inspection

| Method | Returns |
|---|---|
| `get_name()` | Model name. |
| `get_uuid()` | Unique model ID. |
| `get_node_statuses()` | Status per node. |
| `calculation_completed()` | Whether all dependencies are satisfied. |

Saving/loading as JSON is covered in
[Serialization & Database](serialisierung.md).
