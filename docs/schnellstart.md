# Schnellstart

Ein vollständiges FAIR-Modell besteht aus drei Schritten:

1. **Modell anlegen** (`FairModel`),
2. **Faktoren eingeben** (`input_data`),
3. **rechnen** (`calculate_all`) und Ergebnisse abrufen.

```python
import pyfair

# 1) Modell anlegen
model = pyfair.FairModel(name="Datenverlust", n_simulations=10_000)

# 2) Einen Schnitt durch den FAIR-Baum eingeben:
#    Risk = Loss Event Frequency (LEF) × Loss Magnitude (LM)
model.input_data('Loss Event Frequency', low=20, mode=100, high=900)  # PERT
model.input_data('Loss Magnitude', mean=3_500_000, stdev=500_000)     # Normal

# 3) Rechnen
model.calculate_all()

# Ergebnisse als pandas-DataFrame (eine Zeile je Simulation)
df = model.export_results()
print(df['Risk'].describe())
```

`input_data` akzeptiert **Voll- und Kurznamen** der Faktoren – `'LEF'`,
`'Loss Event Frequency'`, `'LM'`, `'Loss Magnitude'` usw. (siehe
[Modelle erstellen](modelle.md#faktornamen-abkurzungen)).

## Strukturierte Eingabe (Fork)

Statt der Legacy-Kurzform kann jeder Faktor über die strukturierte API mit
Verteilung, Parametern und einer qualitativen **Konfidenz** beschrieben werden:

```python
model = pyfair.FairModel(name="Insider", n_simulations=10_000)

model.input_data(
    'Loss Event Frequency',
    distribution='poisson',
    params={'lambda': 12},
    confidence='moderate',          # bestimmt die Streubreite (range)
)
model.input_data(
    'Loss Magnitude',
    distribution='lognormal',
    params={'mean': 250_000},
    confidence='low',               # bestimmt sigma
)
model.calculate_all()
```

Details zu allen Verteilungen und zum Konfidenz-Mapping:
[Eingaben & Verteilungen](eingaben.md).

## Mehrere Modelle: Summe & Vergleich

```python
gesamt = pyfair.FairMetaModel(name="Portfolio", models=[model_a, model_b])
gesamt.calculate_all()                       # mode='sum' (Standard)
gesamt.export_results()['Risk']              # Gesamtrisiko = Summe

vergleich = pyfair.FairMetaModel(
    name="Vorher/Nachher", models=[model_a, model_b],
    mode='compare', baseline_model=model_a.get_name(),
)
vergleich.calculate_all()                    # Delta::-Spalten gegen Baseline
```

Mehr dazu: [Meta-Modelle](metamodelle.md).

## Bericht erzeugen

```python
report = pyfair.FairSimpleReport([model, gesamt], currency_prefix='€')
report.to_html('bericht.html')
```

Mehr dazu: [Berichte](berichte.md).
