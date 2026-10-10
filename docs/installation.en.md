# Installation

pyfair (the neoprehn fork) is a pure Python library. It requires Python 3.9+
as well as `numpy`, `pandas`, `scipy` and `matplotlib` (for reports).

## From the fork repository

The **extended feature set** (structured input API, confidence mapping,
additional distributions) requires the fork – the PyPI original is not
sufficient.

```bash
git clone https://github.com/neoprehn/pyfair.git
pip install -e pyfair
```

This is also how the engine is integrated into **fair-web**: as an editable
package from the sibling directory.

```bash
# from within the fair-web project
pip install -e ../pyfair
```

`-e` (editable) means: changes to the pyfair source take effect immediately,
without reinstalling – useful when developing the engine and the web app in
parallel.

## Original from PyPI

The **unmodified** original is available on PyPI:

```bash
pip install pyfair
```

!!! warning "Feature scope"
    Examples in this documentation that use `distribution=`, `params=`,
    `confidence=` or `input_mode=` require the **fork**. They fail on the
    PyPI original.

## Import & version check

```python
import pyfair
print(pyfair.VERSION)        # e.g. "1.0.0"

# The main public classes:
from pyfair import (
    FairModel,        # a single FAIR model
    FairMetaModel,    # sum/compare multiple models
    FairSimpleReport, # HTML/CSV report
    FairDatabase,     # SQLite storage
    FairModelFactory, # generate model variants
    FairBetaPert,     # Beta-PERT distribution directly
)
```
