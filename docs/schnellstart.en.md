# Quickstart

A complete FAIR model consists of three steps:

1. **Create the model** (`FairModel`),
2. **Enter the factors** (`input_data`),
3. **run the calculation** (`calculate_all`) and retrieve the results.

```python
import pyfair

# 1) Create the model
model = pyfair.FairModel(name="Data Loss", n_simulations=10_000)

# 2) Enter a cut through the FAIR tree:
#    Risk = Loss Event Frequency (LEF) x Loss Magnitude (LM)
model.input_data('Loss Event Frequency', low=20, mode=100, high=900)  # PERT
model.input_data('Loss Magnitude', mean=3_500_000, stdev=500_000)     # Normal

# 3) Calculate
model.calculate_all()

# Results as a pandas DataFrame (one row per simulation)
df = model.export_results()
print(df['Risk'].describe())
```

`input_data` accepts **full and short names** for the factors – `'LEF'`,
`'Loss Event Frequency'`, `'LM'`, `'Loss Magnitude'` etc. (see
[Building Models](modelle.md#factor-names-abbreviations)).

## Structured input (fork)

Instead of the legacy short form, every factor can be described through the
structured API with a distribution, parameters and a qualitative
**confidence** level:

```python
model = pyfair.FairModel(name="Insider", n_simulations=10_000)

model.input_data(
    'Loss Event Frequency',
    distribution='poisson',
    params={'lambda': 12},
    confidence='moderate',          # determines the spread (range)
)
model.input_data(
    'Loss Magnitude',
    distribution='lognormal',
    params={'mean': 250_000},
    confidence='low',               # determines sigma
)
model.calculate_all()
```

Details on all distributions and confidence mapping:
[Inputs & Distributions](eingaben.md).

## Multiple models: sum & compare

```python
total = pyfair.FairMetaModel(name="Portfolio", models=[model_a, model_b])
total.calculate_all()                        # mode='sum' (default)
total.export_results()['Risk']               # total risk = sum

comparison = pyfair.FairMetaModel(
    name="Before/After", models=[model_a, model_b],
    mode='compare', baseline_model=model_a.get_name(),
)
comparison.calculate_all()                   # Delta::- columns vs. baseline
```

More on this: [Meta-Models](metamodelle.md).

## Generating a report

```python
report = pyfair.FairSimpleReport([model, total], currency_prefix='€')
report.to_html('report.html')
```

More on this: [Reports](berichte.md).
