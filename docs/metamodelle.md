# Meta-Modelle (Vergleich & Summe)

`FairMetaModel` fasst **mehrere** `FairModel`-Instanzen zusammen – entweder als
**Summe** (Gesamtrisiko eines Portfolios) oder als **Vergleich** gegen ein
Basismodell.

## Konstruktor

```python
FairMetaModel(name, models, mode='sum', baseline_model=None,
              model_uuid=None, creation_date=None)
```

| Parameter | Bedeutung |
|---|---|
| `name` | Bezeichnung des Meta-Modells. |
| `models` | Liste von `FairModel` (oder `FairMetaModel`). |
| `mode` | `'sum'` (Default) oder `'compare'`. |
| `baseline_model` | **Nur bei** `mode='compare'`: Name eines Komponentenmodells (`model.get_name()`). |

Die Komponentenmodelle werden beim Laden automatisch durchgerechnet – du musst
sie nicht vorab selbst mit `calculate_all()` berechnet haben.

## Modus `sum` – Gesamtrisiko

Summiert das `Risk` aller Komponenten zeilenweise zu einer Gesamtverteilung.

```python
gesamt = pyfair.FairMetaModel(name="Portfolio", models=[m1, m2, m3])
gesamt.calculate_all()

df = gesamt.export_results()
df['Risk']            # Spalte 'Risk' = Summe über alle Modelle
```

!!! warning "Gleiche Simulationszahl"
    Die Summe wird zeilenweise gebildet. Alle Komponentenmodelle müssen
    dieselbe `n_simulations` haben – sonst entstehen `NaN`-Werte und es wird
    eine `FairException` geworfen.

## Modus `compare` – Differenz zur Baseline

Bildet je Komponente eine **Delta-Spalte** gegenüber dem Basismodell
(`Komponente − Baseline`). Ideal für „Vorher/Nachher" oder Maßnahmenvergleiche.

```python
vergleich = pyfair.FairMetaModel(
    name="Mit/ohne Kontrolle",
    models=[ohne_kontrolle, mit_kontrolle],
    mode='compare',
    baseline_model=ohne_kontrolle.get_name(),
)
vergleich.calculate_all()

df = vergleich.export_results()
# Spalten der Nicht-Baseline-Modelle: 'Delta::<Modellname>'
```

Negative Delta-Werte bedeuten **weniger** Risiko als die Baseline.

## Ergebnisse & Inspektion

| Methode | Rückgabe |
|---|---|
| `export_results()` | `DataFrame`: bei `sum` mit Spalte `Risk`, bei `compare` mit `Delta::`-Spalten. |
| `export_params()` | Parameter aller Komponentenmodelle. |
| `get_name()`, `get_uuid()` | Name / ID. |
| `calculation_completed()` | Ob die Aggregation vorliegt. |

## In fair-web

Die Web-App bildet `FairMetaModel` als **Szenariovergleich** ab: Über den Reiter
**„Vergleiche"** mehrere Szenarien gruppieren und gemeinsam berechnen – im
Ergebnis umschaltbar zwischen **Compare** (LECs überlagert) und **Add**
(Gesamtrisiko-Summe). Siehe [Bedienung](bedienung.md#szenarien-vergleichen).

Serialisierung von Meta-Modellen: [Serialisierung & Datenbank](serialisierung.md).
