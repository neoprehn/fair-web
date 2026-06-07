# pyfair (neoprehn-Fork)

fair-web nutzt als Engine den **erweiterten pyfair-Fork**
[neoprehn/pyfair](https://github.com/neoprehn/pyfair) – gegenüber dem
[Original-pyfair](https://pyfair.readthedocs.io/en/latest/) deutlich ausgebaut.

## Erweiterungen (Auszug)

- **Strukturierte Eingabe-API** für `input_data` (`distribution`, `params`,
  `confidence`, `input_mode`).
- **Konfidenz-Mapping**: qualitative Stufen (very_low … very_high) →
  Formparameter (gamma/sigma/range/k); zentral in
  `pyfair/utility/confidence_mapping.py`.
- **Beta-Konfidenzintervall** als Eingabeart (low/high/confidence → mean/k).
- Zusätzliche **Verteilungen/Parameter** und explizite Formparameter, die
  fair-web direkt übergibt.

!!! note "Noch im Aufbau"
    Dieser Abschnitt wird später ausführlich dokumentiert (inkl. API-Referenz,
    ggf. Autodoc), zweisprachig (DE/EN). Bis dahin ist der
    [Quellcode](https://github.com/neoprehn/pyfair) die maßgebliche Referenz.
