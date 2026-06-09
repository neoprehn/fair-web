# Serialisierung & Datenbank

Modelle lassen sich vollständig als **JSON** speichern und wieder laden – inkl.
Seed, Simulationszahl und der ursprünglich eingegebenen Parameter. Damit sind
Ergebnisse reproduzierbar.

## Modell ↔ JSON

```python
# Speichern
json_text = model.to_json()
with open('modell.json', 'w', encoding='utf-8') as f:
    f.write(json_text)

# Laden (statische Methode) – rechnet das Modell direkt durch
model = pyfair.FairModel.read_json(json_text)
```

`to_json()` speichert die **ursprünglich eingegebenen** Werte (nicht die intern
aufgelösten), sodass ein Roundtrip die Absicht des Nutzers erhält. `read_json()`
ruft am Ende automatisch `calculate_all()` auf.

### Aufbau der Modell-JSON

```json
{
    "Loss Event Frequency": { "low": 20, "mode": 90, "high": 95, "gamma": 4 },
    "Loss Magnitude":       { "mean": 100000, "stdev": 20000 },
    "name": "Beispiel-Modell",
    "n_simulations": 10000,
    "random_seed": 42,
    "model_uuid": "…",
    "creation_date": "…",
    "type": "FairModel"
}
```

Strukturierte Eingaben werden im selben Format mit `distribution` / `params` /
`confidence` abgelegt. Rohdaten-Eingaben (`input_raw_data`) erscheinen als
`{"raw": [...]}` und werden beim Laden über `input_raw_data` wiederhergestellt.

!!! note "type-Feld"
    Das Feld `type` (`"FairModel"` bzw. `"FairMetaModel"`) wird beim Laden
    geprüft. Passt der Typ nicht zur aufrufenden Klasse, wirft pyfair eine
    `FairException`.

## Meta-Modell ↔ JSON

`FairMetaModel` serialisiert seine Komponentenmodelle mit und merkt sich `mode`
und `baseline_model`:

```python
meta_json = meta.to_json()
meta = pyfair.FairMetaModel.read_json(meta_json)
```

## SQLite-Datenbank (`FairDatabase`)

`FairDatabase` ist ein dünner Wrapper um eine SQLite-Datei, der Modelle als JSON
ablegt und über Name oder UUID lädt.

```python
FairDatabase(path)
```

```python
db = pyfair.FairDatabase('modelle.sqlite3')   # legt Tabellen bei Bedarf an

db.store(model)                 # FairModel oder FairMetaModel ablegen
geladen = db.load('Beispiel-Modell')   # per Name ODER UUID laden

# Beliebige Abfrage gegen die Ablage:
rows = db.query('SELECT uuid, name, creation_date FROM models')
```

Intern gibt es zwei Tabellen: `models` (uuid, name, creation_date, json) und
`results` (uuid, mean, stdev, min, max) für schnelle Kennzahlabfragen.

!!! tip "fair-web vs. FairDatabase"
    fair-web nutzt **nicht** `FairDatabase`, sondern speichert Szenarien und
    Läufe in seiner eigenen Django-Datenbank (MariaDB/SQLite). `FairDatabase`
    ist die Variante für die reine Skript-/Bibliotheksnutzung von pyfair.

## Modellvarianten erzeugen (`FairModelFactory`)

Für Sensitivitätsbetrachtungen erzeugt `FairModelFactory` mehrere Modelle, die
sich nur in wenigen Faktoren unterscheiden. Gemeinsame Faktoren werden einmal
als `static_arguments` festgelegt, die Variationen je Modell ergänzt:

```python
factory = pyfair.FairModelFactory(
    static_arguments={'Loss Magnitude': {'constant': 50_000}},
    n_simulations=10_000,
)

# Ein Modell aus einer Variation:
m = factory.generate_from_partial(
    'Hohe Frequenz',
    {'Loss Event Frequency': {'low': 50, 'mode': 100, 'high': 200}},
)

# Mehrere Modelle auf einmal (Name -> Variation):
modelle = factory.generate_from_partials({
    'Niedrig': {'Loss Event Frequency': {'constant': 5}},
    'Hoch':    {'Loss Event Frequency': {'constant': 50}},
})
```
