# Reports

`FairSimpleReport` generates a self-contained **HTML report** with key
figures, a distribution histogram and a **Loss Exceedance Curve (LEC)** for
one or more models.

## Constructor

```python
FairSimpleReport(model_or_models, currency_prefix='$', risk_tolerance=None)
```

| Parameter | Meaning |
|---|---|
| `model_or_models` | A `FairModel`/`FairMetaModel` **or** a list of them. |
| `currency_prefix` | Currency symbol used in the tables/charts (e.g. `'€'`). |
| `risk_tolerance` | Optional risk tolerance drawn onto the LEC. |

## Generating HTML

```python
report = pyfair.FairSimpleReport([model, gesamt], currency_prefix='€')
report.to_html('report.html')
```

```python
to_html(output_path, export_csv=False, csv_dir=None)
```

With `export_csv=True`, the underlying data is additionally exported as CSV
(target directory `csv_dir`).

## Generating CSV

```python
to_csv(output_dir='.', sep=';', decimal=',', index=False)
```

Writes the result tables as CSV (default: German separators – semicolon as
the column separator, comma as the decimal separator).

## Report contents

- **Risk Summary** – key figures per model (mean, spread, min/max …),
  currency amounts with `currency_prefix`, probabilities as decimals.
- **Distribution histogram** of the overall risk.
- **Loss Exceedance Curve** – probability of exceeding a loss ≥ X; optionally
  with `risk_tolerance` drawn in.

!!! tip "Comparing multiple models"
    Passing a list (e.g. a single model **and** a meta-model) plots their
    curves together – useful for comparing individual vs. aggregate risk.

In fair-web these analyses are integrated directly into the scenario and
comparison views (LEC, VaR, histograms, node detail table), see
[Usage](bedienung.md#simulation-results).
