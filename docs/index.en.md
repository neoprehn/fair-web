# fair-web Documentation

**fair-web** estimates information risk using the **FAIR** model (Factor
Analysis of Information Risk) as **expected annual loss** – via Monte Carlo
simulation. The computation engine is the extended **pyfair** fork
([neoprehn/pyfair](https://github.com/neoprehn/pyfair)).

Live app: <https://fair.neoprehn.de>

## What this documentation covers

This site documents **both**: how to use the web app **and** the underlying
Python engine (the pyfair fork) – at the same level of detail as the
[original pyfair docs](https://pyfair.readthedocs.io/en/latest/), but adapted
to the fork's extended feature set.

### FAIR Fundamentals

- **[FAIR Taxonomy](fair-taxonomie.md)** – the risk factors and how they're
  derived (based on Open FAIR / O-RT).
- **[FAIR-CAM Fundamentals](fair-cam-grundlagen.md)** – control physiology,
  functional domains, the Detection/Response concept, attribution & license.

### pyfair (Engine)

- **[Installation](installation.md)** – integrating the fork.
- **[Quickstart](schnellstart.md)** – a complete example in a few lines.
- **[Building Models](modelle.md)** – the `FairModel` API.
- **[Inputs & Distributions](eingaben.md)** – legacy and structured input
  APIs, all distributions, confidence mapping.
- **[Meta-Models](metamodelle.md)** – sum (`sum`) or compare (`compare`)
  multiple models.
- **[Reports](berichte.md)** – generating HTML/CSV reports.
- **[Serialization & Database](serialisierung.md)** – saving/loading models
  as JSON, SQLite storage.
- **[Fork Extensions](pyfair-fork.md)** – what the fork adds on top of the
  original.

### pyfair-cam (Engine)

- **[Overview & Detection/Response](pyfair-cam.md)** – a standalone library
  for FAIR-CAM (Controls Analytics Model): Resistance/Prevention (the
  frequency side) and the stage-gated Detection/Response model (the
  loss-magnitude side). Not yet integrated into fair-web (web integration is
  a later build-out stage).

### Web App

- **[Usage (fair-web)](bedienung.md)** – how to use the web app.

!!! note "Status"
    The engine chapters describe the **neoprehn fork** of pyfair. When in
    doubt, the authoritative reference is the
    [fork's source code](https://github.com/neoprehn/pyfair).

Switch language: the **Deutsch/English** toggle at the top of the sidebar
(next to search).
