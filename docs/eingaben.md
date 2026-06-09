# Eingaben & Verteilungen

Jeder FAIR-Faktor wird als **Verteilung** eingegeben, aus der die
Monte-Carlo-Simulation zieht. pyfair (Fork) kennt dafür zwei Eingabestile, die
sich beliebig mischen lassen.

## Zwei Eingabestile

### 1. Legacy (Kurzform-Schlüsselwörter)

Aus der Kombination der Schlüsselwörter leitet pyfair die Verteilung ab:

| Schlüsselwörter | Verteilung |
|---|---|
| `constant` | Konstante |
| `mean`, `stdev` | Normal |
| `low`, `mode`, `high` (`gamma` optional) | PERT |

```python
model.input_data('Loss Magnitude', mean=20_000, stdev=5_000)        # Normal
model.input_data('Loss Event Frequency', low=10, mode=20, high=100)  # PERT
model.input_data('Secondary Loss', constant=3_500)                   # Konstante
```

### 2. Strukturiert (Fork)

Explizit über `distribution`, `params` und optional `confidence` / `input_mode`:

```python
model.input_data(
    'Threat Capability',
    distribution='beta',
    params={'mean': 0.3},
    confidence='moderate',
)
```

| Argument | Bedeutung |
|---|---|
| `distribution` | `'constant'`, `'normal'`, `'pert'`, `'lognormal'`, `'poisson'`, `'beta'`. |
| `params` | Dictionary der Verteilungsparameter (siehe unten). |
| `confidence` | Qualitative Streubreite: `very_low`, `low`, `moderate`, `high`, `very_high`. |
| `input_mode` | Spezial-Eingabeart (aktuell nur `confidence_interval` für `beta`). |

!!! note "Additiv & abwärtskompatibel"
    Die strukturierte API ergänzt die Legacy-Form, ersetzt sie nicht.
    Bestehende Modelle laufen unverändert weiter.

## Die Verteilungen im Detail

### Constant

Fester Wert für alle Iterationen.

```python
params={'constant': 50_000}
# Legacy: constant=50_000
```

### Normal

Normalverteilung um `mean` mit Streuung `stdev`.

```python
params={'mean': 20_000, 'stdev': 5_000}
# Legacy: mean=20_000, stdev=5_000
```

### PERT (Beta-PERT)

Dreipunkt-Schätzung `low`/`mode`/`high` mit Formparameter `gamma` (Default `4`;
höheres `gamma` = spitzer um `mode`). Es muss gelten `low ≤ mode ≤ high`.

```python
params={'low': 10, 'mode': 20, 'high': 100}          # gamma default 4
params={'low': 10, 'mode': 20, 'high': 100, 'gamma': 8}
# Legacy: low=10, mode=20, high=100, gamma=8
```

### Lognormal

Schiefe Verteilung für Verlusthöhen. **`mean`** ist der arithmetische
Mittelwert auf der Originalskala, **`sigma`** die Streuung der zugrunde
liegenden Normalverteilung. `mean` muss > 0 sein.

```python
params={'mean': 250_000, 'sigma': 0.6}
```

`sigma` kann auch über `confidence` gesetzt werden (Default `0.6`).

### Poisson

Zähl-Häufigkeiten mit **unsicherem** `lambda`. `range` streut `lambda`
symmetrisch, bevor gezogen wird:

```
lambda_sample ~ Uniform(lambda · (1 − range), lambda · (1 + range))
variates      ~ Poisson(lambda_sample)
```

```python
params={'lambda': 12, 'range': 0.4}
```

`range` kann über `confidence` gesetzt werden (Default `0.4`).

### Beta

Für **Wahrscheinlichkeiten / 0–1-Faktoren**. Zwei Parametrisierungen:

- `alpha` / `beta` – direkt, **oder**
- `mean` / `k` – mit `alpha = mean·k`, `beta = (1−mean)·k`. `k` ist die
  „Konzentration" (höheres `k` = schmaler). `mean` muss in [0, 1] liegen.

```python
params={'mean': 0.3, 'k': 15}     # k default 15
params={'alpha': 2, 'beta': 5}
```

`k` kann über `confidence` gesetzt werden.

## Konfidenz-Mapping

`confidence` ersetzt den **Formparameter** der jeweiligen Verteilung durch einen
hinterlegten Wert. Je Verteilung gibt es genau einen solchen Parameter:

| Verteilung | Formparameter | Default (ohne `confidence`) |
|---|---|---|
| `beta` | `k` | 15 |
| `lognormal` | `sigma` | 0.6 |
| `poisson` | `range` | 0.4 |
| `pert` | `gamma` | 4 |

Mit `confidence` ergeben sich diese Werte (höhere Konfidenz = engere Streuung;
bei `poisson` ist kleineres `range` enger, bei `lognormal` ist die Tabelle
bewusst so kalibriert):

| confidence | beta `k` | lognormal `sigma` | poisson `range` | pert `gamma` |
|---|---|---|---|---|
| `very_low` | 4 | 0.25 | 2.5 | 10 |
| `low` | 7 | 0.4 | 0.75 | 8 |
| `moderate` | 15 | 0.6 | 0.4 | 4 |
| `high` | 40 | 0.9 | 0.25 | 3 |
| `very_high` | 100 | 1.2 | 0.15 | 2 |

```python
# Konfidenz statt explizitem Formparameter:
model.input_data('Primary Loss', distribution='lognormal',
                 params={'mean': 100_000}, confidence='high')   # sigma = 0.9
```

!!! warning "Nicht beides gleichzeitig"
    `confidence` und der explizite Formparameter derselben Verteilung schließen
    sich aus. `confidence='high'` **und** `params={'sigma': 0.5}` für dieselbe
    Eingabe wirft eine `FairException`.

Die Tabellen sind zentral in `pyfair/utility/confidence_mapping.py` definiert –
fair-web macht die Standardwerte in der App-Konfiguration editierbar.

## Beta-Konfidenzintervall (`input_mode`)

Statt `mean`/`k` lässt sich eine Beta-Verteilung aus einem **zentralen
Konfidenzintervall** über [0, 1] fitten. pyfair löst daraus `mean`/`k`:

```python
model.input_data(
    'Threat Capability',
    distribution='beta',
    input_mode='confidence_interval',
    params={'low': 0.2, 'high': 0.6, 'confidence': 0.9},
)
```

Bedeutung: „Mit 90 % Wahrscheinlichkeit liegt der Faktor zwischen 0,2 und 0,6."
Bedingungen: `0 ≤ low < high ≤ 1` und `0 < confidence < 1`; `mean`/`k`/`alpha`/
`beta` dürfen dann **nicht** zusätzlich angegeben werden.

## Wertebereiche & Clipping

Vier Faktoren sind **Wahrscheinlichkeiten** und müssen in [0, 1] liegen –
Eingabe-Parameter außerhalb [0, 1] werden abgewiesen, und die erzeugten Samples
werden auf [0, 1] beschnitten:

> **Probability of Action**, **Vulnerability**, **Control Strength**,
> **Threat Capability**

Alle übrigen Faktoren werden auf **≥ 0** beschnitten (keine negativen
Häufigkeiten/Verluste). Zusätzlich prüft pyfair, dass numerische Parameter nicht
negativ sind und PERT-Tripel geordnet sind (`low ≤ mode ≤ high`).
