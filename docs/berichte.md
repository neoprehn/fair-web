# Berichte

`FairSimpleReport` erzeugt einen in sich geschlossenen **HTML-Bericht** mit
Kennzahlen, Verteilungs-Histogramm und **Loss-Exceedance-Curve (LEC)** für ein
oder mehrere Modelle.

## Konstruktor

```python
FairSimpleReport(model_or_models, currency_prefix='$', risk_tolerance=None)
```

| Parameter | Bedeutung |
|---|---|
| `model_or_models` | Ein `FairModel`/`FairMetaModel` **oder** eine Liste davon. |
| `currency_prefix` | Währungssymbol in den Tabellen/Charts (z. B. `'€'`). |
| `risk_tolerance` | Optionale Risikotoleranz, die in die LEC eingezeichnet wird. |

## HTML erzeugen

```python
report = pyfair.FairSimpleReport([model, gesamt], currency_prefix='€')
report.to_html('bericht.html')
```

```python
to_html(output_path, export_csv=False, csv_dir=None)
```

Mit `export_csv=True` werden zusätzlich die zugrunde liegenden Daten als CSV
abgelegt (Zielverzeichnis `csv_dir`).

## CSV erzeugen

```python
to_csv(output_dir='.', sep=';', decimal=',', index=False)
```

Schreibt die Ergebnistabellen als CSV (Default: deutsche Trennzeichen –
Semikolon als Spalten-, Komma als Dezimaltrenner).

## Inhalt des Berichts

- **Risk Summary** – Kennzahlen je Modell (Mittelwert, Streuung, Min/Max …),
  Geldbeträge mit `currency_prefix`, Wahrscheinlichkeiten als Dezimalzahl.
- **Verteilungs-Histogramm** des Gesamtrisikos.
- **Loss-Exceedance-Curve** – Wahrscheinlichkeit, einen Verlust ≥ X zu
  überschreiten; optional mit eingezeichneter `risk_tolerance`.

!!! tip "Mehrere Modelle vergleichen"
    Übergibst du eine Liste (z. B. ein Einzelmodell **und** ein Meta-Modell),
    werden deren Kurven gemeinsam dargestellt – praktisch zum Vergleich von
    Einzel- gegen Gesamtrisiko.

In fair-web sind diese Auswertungen direkt in die Szenario- und
Vergleichs-Ansichten integriert (LEC, VaR, Histogramme, Knoten-Detailtabelle),
siehe [Bedienung](bedienung.md#simulation-ergebnis).
