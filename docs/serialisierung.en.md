# Serialization & Database

Models can be saved and reloaded completely as **JSON** – including the
seed, number of simulations and the originally entered parameters. This
makes results reproducible.

## Model ↔ JSON

```python
# Save
json_text = model.to_json()
with open('model.json', 'w', encoding='utf-8') as f:
    f.write(json_text)

# Load (static method) – calculates the model immediately
model = pyfair.FairModel.read_json(json_text)
```

`to_json()` stores the **originally entered** values (not the internally
resolved ones), so a round trip preserves the user's intent. `read_json()`
automatically calls `calculate_all()` at the end.

### Structure of the model JSON

```json
{
    "Loss Event Frequency": { "low": 20, "mode": 90, "high": 95, "gamma": 4 },
    "Loss Magnitude":       { "mean": 100000, "stdev": 20000 },
    "name": "Example Model",
    "n_simulations": 10000,
    "random_seed": 42,
    "model_uuid": "…",
    "creation_date": "…",
    "type": "FairModel"
}
```

Structured inputs are stored in the same format with `distribution` /
`params` / `confidence`. Raw-data inputs (`input_raw_data`) appear as
`{"raw": [...]}` and are restored via `input_raw_data` on load.

!!! note "type field"
    The `type` field (`"FairModel"` or `"FairMetaModel"`) is checked on
    load. If the type doesn't match the calling class, pyfair raises a
    `FairException`.

## Meta-model ↔ JSON

`FairMetaModel` also serializes its component models and remembers `mode`
and `baseline_model`:

```python
meta_json = meta.to_json()
meta = pyfair.FairMetaModel.read_json(meta_json)
```

## SQLite database (`FairDatabase`)

`FairDatabase` is a thin wrapper around a SQLite file that stores models as
JSON and loads them by name or UUID.

```python
FairDatabase(path)
```

```python
db = pyfair.FairDatabase('models.sqlite3')   # creates tables as needed

db.store(model)                 # store a FairModel or FairMetaModel
loaded = db.load('Example Model')    # load by name OR UUID

# Arbitrary query against the store:
rows = db.query('SELECT uuid, name, creation_date FROM models')
```

Internally there are two tables: `models` (uuid, name, creation_date, json)
and `results` (uuid, mean, stdev, min, max) for fast key-figure lookups.

!!! tip "fair-web vs. FairDatabase"
    fair-web does **not** use `FairDatabase` – it stores scenarios and runs
    in its own Django database (MariaDB/SQLite). `FairDatabase` is the
    variant for plain script/library use of pyfair.

## Generating model variants (`FairModelFactory`)

For sensitivity analyses, `FairModelFactory` generates multiple models that
differ in only a few factors. Shared factors are set once as
`static_arguments`, and the variations are supplied per model:

```python
factory = pyfair.FairModelFactory(
    static_arguments={'Loss Magnitude': {'constant': 50_000}},
    n_simulations=10_000,
)

# A single model from one variation:
m = factory.generate_from_partial(
    'High Frequency',
    {'Loss Event Frequency': {'low': 50, 'mode': 100, 'high': 200}},
)

# Several models at once (name -> variation):
models = factory.generate_from_partials({
    'Low':  {'Loss Event Frequency': {'constant': 5}},
    'High': {'Loss Event Frequency': {'constant': 50}},
})
```
