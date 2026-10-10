# Meta-Models (Compare & Sum)

`FairMetaModel` combines **multiple** `FairModel` instances – either as a
**sum** (total risk of a portfolio) or as a **comparison** against a baseline
model.

## Constructor

```python
FairMetaModel(name, models, mode='sum', baseline_model=None,
              model_uuid=None, creation_date=None)
```

| Parameter | Meaning |
|---|---|
| `name` | Name of the meta-model. |
| `models` | List of `FairModel` (or `FairMetaModel`). |
| `mode` | `'sum'` (default) or `'compare'`. |
| `baseline_model` | **Only for** `mode='compare'`: name of a component model (`model.get_name()`). |

The component models are automatically calculated on load – you don't need
to call `calculate_all()` on them beforehand yourself.

## Mode `sum` – total risk

Sums the `Risk` of all components row-wise into a total distribution.

```python
total = pyfair.FairMetaModel(name="Portfolio", models=[m1, m2, m3])
total.calculate_all()

df = total.export_results()
df['Risk']            # column 'Risk' = sum across all models
```

!!! warning "Same number of simulations"
    The sum is formed row-wise. All component models must have the same
    `n_simulations` – otherwise `NaN` values result and a `FairException`
    is raised.

## Mode `compare` – difference from the baseline

Produces a **delta column** per component against the baseline model
(`component − baseline`). Ideal for "before/after" or control comparisons.

```python
comparison = pyfair.FairMetaModel(
    name="With/without control",
    models=[without_control, with_control],
    mode='compare',
    baseline_model=without_control.get_name(),
)
comparison.calculate_all()

df = comparison.export_results()
# columns of the non-baseline models: 'Delta::<model name>'
```

Negative delta values mean **less** risk than the baseline.

## Results & inspection

| Method | Returns |
|---|---|
| `export_results()` | `DataFrame`: with a `Risk` column for `sum`, with `Delta::` columns for `compare`. |
| `export_params()` | Parameters of all component models. |
| `get_name()`, `get_uuid()` | Name / ID. |
| `calculation_completed()` | Whether the aggregation has been computed. |

## In fair-web

The web app maps `FairMetaModel` to a **scenario comparison**: group and
jointly calculate multiple scenarios via the **"Compare"** tab – the result
view toggles between **Compare** (LECs overlaid) and **Add** (total risk
sum). See [Usage](bedienung.md#comparing-scenarios).

Serialization of meta-models: [Serialization & Database](serialisierung.md).
