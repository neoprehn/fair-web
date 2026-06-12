# Installation

pyfair (der neoprehn-Fork) ist eine reine Python-Bibliothek. Sie benötigt
Python 3.9+ sowie `numpy`, `pandas`, `scipy` und `matplotlib` (für Berichte).

## Aus dem Fork-Repository

Für den **erweiterten Funktionsumfang** (strukturierte Eingabe-API,
Konfidenz-Mapping, zusätzliche Verteilungen) ist der Fork nötig – das
PyPI-Original genügt nicht.

```bash
git clone https://github.com/neoprehn/pyfair.git
pip install -e pyfair
```

So wird die Engine auch in **fair-web** eingebunden: als editierbares Paket aus
dem Nachbarverzeichnis.

```bash
# innerhalb des fair-web-Projekts
pip install -e ../pyfair
```

`-e` (editable) bedeutet: Änderungen am pyfair-Quellcode wirken sofort, ohne
Neuinstallation – praktisch bei paralleler Weiterentwicklung von Engine und
Web-App.

## Original von PyPI

Das **unmodifizierte** Original ist auf PyPI verfügbar:

```bash
pip install pyfair
```

!!! warning "Funktionsumfang"
    Beispiele in dieser Doku, die `distribution=`, `params=`, `confidence=`
    oder `input_mode=` verwenden, setzen den **Fork** voraus. Auf dem
    PyPI-Original schlagen sie fehl.

## Import & Versionsprüfung

```python
import pyfair
print(pyfair.VERSION)        # z. B. "1.0.0"

# Die wichtigsten öffentlichen Klassen:
from pyfair import (
    FairModel,        # einzelnes FAIR-Modell
    FairMetaModel,    # mehrere Modelle summieren/vergleichen
    FairSimpleReport, # HTML/CSV-Bericht
    FairDatabase,     # SQLite-Ablage
    FairModelFactory, # Modellvarianten erzeugen
    FairBetaPert,     # Beta-PERT-Verteilung direkt
)
```
