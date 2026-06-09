# Modelle erstellen

Die zentrale Klasse ist `FairModel`. Jede Instanz steht für **ein** FAIR-Modell
mit eigenem Abhängigkeitsbaum, Eingabe-Parser und Berechnungswerk.

## Konstruktor

```python
FairModel(name, n_simulations=10_000, random_seed=42,
          model_uuid=None, creation_date=None)
```

| Parameter | Bedeutung |
|---|---|
| `name` | Menschenlesbare Bezeichnung. |
| `n_simulations` | Anzahl Monte-Carlo-Iterationen (mehr = genauer, langsamer). |
| `random_seed` | Seed für Reproduzierbarkeit – gleicher Seed → gleiches Ergebnis. |
| `model_uuid`, `creation_date` | Werden automatisch vergeben. |

!!! warning "UUID/Datum"
    `model_uuid` und `creation_date` nicht selbst setzen – das ist nur für die
    JSON-Deserialisierung gedacht und kann sonst Dinge zerstören.

## Faktoren eingeben

Ein FAIR-Modell wird befüllt, indem du einen **Schnitt** durch den
[FAIR-Baum](fair-taxonomie.md) eingibst: jeden Ast so weit herunterbrechen, bis
du den Faktor schätzen kannst. Nur die **Blätter deines Schnitts** musst du
eingeben – die Engine rechnet nach oben bis `Risk`.

```python
model.input_data(target, **kwargs)
```

`target` ist der Faktorname, `kwargs` die Verteilungsparameter. Alle Eingabearten
sind ausführlich unter [Eingaben & Verteilungen](eingaben.md) beschrieben.
`input_data` gibt das Modell zurück, ist also **verkettbar**:

```python
(model
    .input_data('Loss Event Frequency', low=10, mode=20, high=100)
    .input_data('Loss Magnitude', constant=50_000)
    .calculate_all())
```

### Weitere Eingabemethoden

| Methode | Zweck |
|---|---|
| `input_data(target, **kwargs)` | Einzelner Faktor (Legacy oder strukturiert). |
| `bulk_import_data(dict)` | Mehrere Faktoren auf einmal (`{target: params}`). |
| `input_multi_data(target, dict)` | Mehrere Posten, die zu einem Faktor aggregieren (v. a. Sekundärverluste). |
| `input_raw_data(target, array)` | Fertiges Sample direkt einspeisen (Länge = `n_simulations`). |

```python
model.bulk_import_data({
    'Loss Event Frequency': {'mean': 90, 'stdev': 10},
    'Loss Magnitude': {'constant': 4_000},
})
```

`input_multi_data` für mehrteilige Sekundärverluste (z. B. Reputation + Recht):

```python
model.input_multi_data('Secondary Loss', {
    'Reputation': {
        'Secondary Loss Event Frequency': {'constant': 0.4},
        'Secondary Loss Event Magnitude': {'low': 10_000, 'mode': 20_000, 'high': 100_000},
    },
    'Recht': {
        'Secondary Loss Event Frequency': {'constant': 0.2},
        'Secondary Loss Event Magnitude': {'low': 5_000, 'mode': 15_000, 'high': 60_000},
    },
})
```

!!! warning "Rohdaten"
    `input_raw_data` speichert das komplette Array **unkomprimiert** in der
    Modell-JSON (es lässt sich nicht aus Parametern reproduzieren). Das kann
    serialisierte Modelle stark aufblähen.

## Rechnen

```python
model.calculate_all()
```

Berechnet alle noch offenen Knoten. Sind die nötigen Eingaben unvollständig,
wird eine `FairException` mit den Knoten-Status geworfen. Prüfen lässt sich das
vorab mit:

```python
model.calculation_completed()   # bool
model.get_node_statuses()       # pandas.Series: Knoten -> Status
```

Mögliche Status sind u. a. `Supplied` (eingegeben), `Calculable` (berechenbar),
`Calculated` (fertig) und `Required` (fehlt noch).

### Reihenfolge der Vulnerability

Intern wird `Vulnerability` aus **Threat Capability** (TC) und **Control
Strength** (CS) berechnet (TC vs. RS/CS) – die Engine berücksichtigt dabei die
korrekte Reihenfolge automatisch.

## Ergebnisse exportieren

| Methode | Rückgabe |
|---|---|
| `export_results()` | `pandas.DataFrame` – eine Spalte je Faktor, eine Zeile je Simulation. |
| `export_results_csv(output_path=None, sep=';', decimal=',', index=False)` | Schreibt die Ergebnistabelle als CSV (Default deutsche Trennzeichen) und gibt den Pfad zurück. |
| `export_params()` | Aufgelöste Eingabeparameter (Dictionary). |

```python
df = model.export_results()
df['Risk'].quantile([0.5, 0.9, 0.95])     # Median, P90, P95
model.export_results_csv('ergebnis.csv')
```

## Faktornamen & Abkürzungen

`input_data` versteht Voll- und Kurznamen (Groß-/Kleinschreibung egal):

| Faktor | Abkürzungen |
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

## Inspektion

| Methode | Rückgabe |
|---|---|
| `get_name()` | Modellname. |
| `get_uuid()` | Eindeutige Modell-ID. |
| `get_node_statuses()` | Status je Knoten. |
| `calculation_completed()` | Ob alle Abhängigkeiten erfüllt sind. |

Speichern/Laden als JSON behandelt das Kapitel
[Serialisierung & Datenbank](serialisierung.md).
