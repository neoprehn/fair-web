# pyfair-cam (Engine)

**Monte Carlo simulator for FAIR-CAM** (Controls Analytics Model) –
[neoprehn/pyfair-cam](https://github.com/neoprehn/pyfair-cam). For the
conceptual background see [FAIR-CAM Fundamentals](fair-cam-grundlagen.md).

!!! note "Standalone library"
    pyfair-cam has **no hard dependency on pyfair** in the core install and
    runs independently. Since phase 3 there's an optional `to_pyfair()`
    adapter (extra `pyfair-cam[pyfair]`, see below) – the actual web
    integration (admin toggle, UI) remains a later build-out stage (phase
    5).

## Installation

```bash
pip install -e ../pyfair-cam
```

## Model

```
Risk = LEF × LM
LEF  = TEF × Susceptibility
Susceptibility = Π (1 − OpEffᵢ)            (defense in depth, OR logic)
```

Resistive controls act on the **frequency side** (Susceptibility), not as a
multiplier on the Loss Magnitude. The Loss Magnitude comes either from a
flat distribution or – since phase 2 – from the stage-gated
Detection/Response model (see below).

## Quickstart

```python
from pyfair_cam import (
    FairCamModel, FairCamSimulator, BetaPert, ResistiveControl, FairCamReport,
)

model = FairCamModel(name="Ransomware Scenario", n_simulations=10_000)
model.input_threat_frequency(BetaPert(low=5, mode=10, high=20))       # TEF
model.input_loss_magnitude(LogNormal(mean=200_000, stdev=150_000))     # LM (flat)

model.add_resistive_control(
    ResistiveControl(
        name="EDR / Anti-Malware",
        intended_efficacy=BetaPert(low=0.70, mode=0.85, high=0.95),
        variant_efficacy=0.10,
        variance_frequency=4,   # varies 4x per year
        variance_duration=5,    # 5 days each
        coverage=0.95,
    )
)

simulator = FairCamSimulator(n_simulations=10_000, seed=42)
simulator.run(model)

report = FairCamReport(simulator)
report.print_summary()
```

## Formulas

| Quantity | Formula |
|---|---|
| Reliability | `Rel = (1 − VF/365) ^ VD` |
| Operational Efficacy | `OpEff = Cov × [Rel × IntEff + (1−Rel) × VarEff]` |
| Combined Susceptibility | `Susc = Π (1 − OpEffᵢ)` across all resistive controls |

All formulas live as pure, vectorized functions in `pyfair_cam/core.py` and
are individually tested against the FAIR-CAM knowledge base
(`tests/test_core.py`).

## Detection & Response

Since phase 2, pyfair-cam implements the **stage-gated Detection/Response
model**: an attack proceeds through an ordered list of `Stage` objects
(kill-chain stages); for each Monte Carlo trial, a random draw at every
stage decides detection or progression. Each trial ends in an outcome class
(freely named, e.g. Early/Mid/Late Detection, Full Impact, Attacker Fails),
from which the Loss Magnitude is drawn.

```python
from pyfair_cam import Stage, DetectionResponseFactor, BetaPert

stage_1 = Stage(
    name="Initial Access", coverage=0.95, visibility=0.70, vis_reliability=0.95,
    recognition=0.40, rec_reliability=0.90, monitoring_cadence=0.042,
    mon_reliability=0.95, duration=0.25, progression_probability=0.90,
    review_independence=0.40,
)
# ... further stages ...

detection_response = DetectionResponseFactor(
    name="Ransomware Kill Chain",
    stages=[stage_1, ...],
    stage_outcome_map={1: "early", 2: "early", 3: "mid", ...},
    loss_distributions={
        "early": BetaPert(low=2_000, mode=8_000, high=30_000),
        "mid": BetaPert(low=25_000, mode=75_000, high=250_000),
        DetectionResponseFactor.FULL_IMPACT: BetaPert(low=1_000_000, mode=3_000_000, high=5_000_000),
        DetectionResponseFactor.ATTACKER_FAILS: BetaPert(low=2_000, mode=5_000, high=15_000),
    },
)

model.set_detection_response(detection_response)   # instead of input_loss_magnitude()
```

`set_detection_response()` and `input_loss_magnitude()` are mutually
exclusive. When a Detection/Response model is set, `FairCamModel.calculate()`
additionally returns `outcome_class` and `detected_at_stage` per trial.

A complete, runnable example (a 6-stage ransomware kill chain, combined with
a resistive control) is in the repository under
[`examples/ransomware_scenario.py`](https://github.com/neoprehn/pyfair-cam/blob/main/examples/ransomware_scenario.py).

### Response time & detection SLO (reporting)

Two further metrics are available as pure reporting functions (not part of
the risk calculation):

- `DetectionResponseFactor.response_time(n, rng)` – time to containment +
  recovery, accounting for overlap (concurrency).
- `core.detection_within_time(...)` – "how likely is detection within a
  time budget T?" (SLO validation, e.g. "detect Initial Access within 4
  hours").

## pyfair integration (phase 3)

An optional adapter translates a `FairCamModel` into a native pyfair
`FairModel`, so pyfair performs the actual Monte Carlo calculation. TEF,
Susceptibility and Loss Magnitude are passed **as full raw-data arrays per
trial** (not as a mean), so the CAM side's uncertainty isn't averaged away
prematurely.

```bash
pip install pyfair-cam[pyfair]
```

```python
fair_model, cam_result = model.to_pyfair(mode="vuln")
fair_model.export_results()          # native pyfair result (Risk, LEF, ...)
cam_result["outcome_class"]          # CAM extra info (if Detection/Response is set)
```

There are two integration points, both implemented, **deliberately left
uncalibrated** (decision 2026-07-26 – see the
[roadmap](https://github.com/neoprehn/pyfair-cam/blob/main/ROADMAP.md#offene-architektur-entscheidung-andockpunkt-fair--fair-cam)):

- **Path Vuln/A** (`mode="vuln"`, KB-compliant): `Susceptibility = 1 − OpEff`
  is passed directly to pyfair as `Vulnerability` – the result is identical
  to `FairCamModel.calculate()`.
- **Path CS/B** (`mode="cs"`): `Control Strength = 1 − Susceptibility`
  competes against a separately supplied `threat_capability` distribution
  (FAIR-CAM doesn't model Threat Capability itself); pyfair calculates
  `Vulnerability` here via its **own native step comparison**
  (`model_calc.py`).

  ```python
  fair_model, cam_result = model.to_pyfair(
      mode="cs", threat_capability=BetaPert(low=0.2, mode=0.4, high=0.8),
  )
  ```

Rather than looking for a calibration `OpEff → RS percentile` that would
make both paths numerically match, this was deliberately **left unsolved**:
path B simulates at the CS/TCap level and only converts to
Susceptibility/Vulnerability afterward, so it may legitimately produce
results that differ from path A. Anyone who needs consistency with path A
stays on path A. A third, explicitly calibrated variant is noted as a
possible future task, but not built.

!!! warning "Path B loses trial-level spread (a structural finding, not just a calibration question)"
    pyfair's native `Vulnerability = mean(CS < TCap)` is **a single scalar
    across all trials**, not a per-trial value
    (`model_calc.py._calculate_step_average`) – verified empirically,
    `Vulnerability.nunique() == 1` across n trials. Path B therefore
    structurally loses the per-trial Susceptibility spread that path A
    retains. A tighter/"safer" CS input distribution only shifts the single
    Vulnerability mean, but does not restore the lost trial variance –
    tails/VaR from path B should be interpreted with that caveat in mind.

### Both paths side by side: `compare_paths()`

Instead of calibrating, both paths can be run with an identical seed (the
same TEF/Susceptibility/LM trials) in parallel and compared directly –
analogous to the "show both instead of replacing" decision on the LM side:

```python
result = model.compare_pyfair_paths(
    threat_capability=BetaPert(low=0.2, mode=0.4, high=0.8),
)
result["stats"]                    # mean/std/median/VaR95/VaR99/max per path
result["cs_vulnerability_scalar"]  # the single pyfair-native Vulnerability value
result["note"]                     # pointer to the spread finding above
```

## HTML report

`FairCamReport.to_html()` generates a self-contained, offline-runnable HTML
file – no Bootstrap CDN dependency like fair-web itself, but visually
aligned with it (Bahnschrift font, sky blue, dark/light toggle). Charts are
inline SVG rather than matplotlib/PNG, so data colors follow the theme
toggle.

```python
report = FairCamReport(simulator)
report.to_html("report.html")
# with the optional path A/B panel (only if pyfair is installed):
report.to_html("report.html", threat_capability=BetaPert(low=0.2, mode=0.4, high=0.8))
```

Depending on the model configuration, it automatically includes: key
figures, Loss Exceedance Curve, distribution histogram, control efficacy &
susceptibility breakdown, a before/after comparison (with/without
controls), a detection-stage breakdown, an LM before/after panel (shown
side by side) and the optional path A/B panel.

## Reproducibility

Like pyfair (and as fair-web knows it from pyfair), the simulator draws all
random quantities from **one** single, centrally created
`numpy.random.Generator` – never from the global `np.random.seed()`. This
also applies to the Detection/Response model: every configured loss
distribution is **always drawn in full** for all trials on every simulation
run (not only for the trials that ultimately need it), so the number of RNG
draws never depends on the random outcome itself.

## Status

- **Phases 0–2 complete:** RNG foundation (including CI: `ruff` + `pytest`
  on every push/PR), Resistance/Prevention (frequency side), Detection &
  Response (loss-magnitude side).
- **Phase 3 complete:** pyfair integration path Vuln/A and path CS/B
  implemented and tested, including `compare_paths()` and an end-to-end
  test with a complete ransomware scenario (see above).
- **Phase 4 complete:** its own offline-runnable HTML report (see above).
- **Up next:** web integration into fair-web (phase 5).
- **Planned after that:** Variance Management (phase 6), Decision Support
  (phase 7), risk appetite & metrics (phase 8), Root Cause Analysis (phase
  9), deeper Resistance modeling (phase 10), Opportunity Analysis (phase
  11) – see the
  [roadmap in the pyfair-cam repository](https://github.com/neoprehn/pyfair-cam/blob/main/ROADMAP.md).

!!! note "License"
    pyfair-cam code: MIT. The underlying FAIR-CAM methodology is CC
    BY-NC-ND 4.0 (Jack Jones/FAIR Institute) – for details see
    [FAIR-CAM Fundamentals § Attribution & License](fair-cam-grundlagen.md#attribution-license).
