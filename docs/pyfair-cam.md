# pyfair-cam (Engine)

**Monte-Carlo-Simulator für FAIR-CAM** (Controls Analytics Model) –
[neoprehn/pyfair-cam](https://github.com/neoprehn/pyfair-cam). Konzeptionelle
Grundlagen siehe [FAIR-CAM-Grundlagen](fair-cam-grundlagen.md).

!!! note "Eigenständige Bibliothek"
    pyfair-cam hat **keine Abhängigkeit zu pyfair** und ist unabhängig
    lauffähig. Die Integration von FAIR und FAIR-CAM in fair-web ist für eine
    spätere Ausbaustufe vorgesehen (Web-UI, Andockpunkt FAIR ↔ FAIR-CAM noch
    offen) – aktuell nur als eigenständige Python-Bibliothek nutzbar.

## Installation

```bash
pip install -e ../pyfair-cam
```

## Modell

```
Risk = LEF × LM
LEF  = TEF × Susceptibility
Susceptibility = Π (1 − OpEffᵢ)            (Defense-in-Depth, ODER-Logik)
```

Resistive Controls wirken auf die **Frequenz-Seite** (Susceptibility), nicht
als Multiplikator auf die Loss Magnitude. Die Loss Magnitude kommt entweder
aus einer flachen Verteilung oder – seit Phase 2 – aus dem stage-gated
Detection/Response-Modell (siehe unten).

## Schnellstart

```python
from pyfair_cam import (
    FairCamModel, FairCamSimulator, BetaPert, ResistiveControl, FairCamReport,
)

model = FairCamModel(name="Ransomware Szenario", n_simulations=10_000)
model.input_threat_frequency(BetaPert(low=5, mode=10, high=20))       # TEF
model.input_loss_magnitude(LogNormal(mean=200_000, stdev=150_000))     # LM (flach)

model.add_resistive_control(
    ResistiveControl(
        name="EDR / Anti-Malware",
        intended_efficacy=BetaPert(low=0.70, mode=0.85, high=0.95),
        variant_efficacy=0.10,
        variance_frequency=4,   # 4x pro Jahr variant
        variance_duration=5,    # je 5 Tage
        coverage=0.95,
    )
)

simulator = FairCamSimulator(n_simulations=10_000, seed=42)
simulator.run(model)

report = FairCamReport(simulator)
report.print_summary()
```

## Formeln

| Größe | Formel |
|---|---|
| Reliability | `Rel = (1 − VF/365) ^ VD` |
| Operational Efficacy | `OpEff = Cov × [Rel × IntEff + (1−Rel) × VarEff]` |
| Combined Susceptibility | `Susc = Π (1 − OpEffᵢ)` über alle Resistive Controls |

Alle Formeln liegen als reine, vektorisierte Funktionen in `pyfair_cam/core.py`
und sind einzeln gegen die FAIR-CAM-Knowledge-Base getestet
(`tests/test_core.py`).

## Detection & Response

Seit Phase 2 bildet pyfair-cam das **stage-gated Detection/Response-Modell**
ab: ein Angriff durchläuft eine geordnete Liste von `Stage`-Objekten
(Kill-Chain-Stufen); pro Monte-Carlo-Trial entscheidet eine Zufallsziehung an
jeder Stufe über Erkennung oder Fortschritt. Am Ende steht pro Trial eine
Outcome-Klasse (frei benennbar, z.B. Early/Mid/Late Detection, Full Impact,
Attacker Fails), aus der die Loss Magnitude gezogen wird.

```python
from pyfair_cam import Stage, DetectionResponseFactor, BetaPert

stage_1 = Stage(
    name="Initial Access", coverage=0.95, visibility=0.70, vis_reliability=0.95,
    recognition=0.40, rec_reliability=0.90, monitoring_cadence=0.042,
    mon_reliability=0.95, duration=0.25, progression_probability=0.90,
    review_independence=0.40,
)
# ... weitere Stages ...

detection_response = DetectionResponseFactor(
    name="Ransomware Kill-Chain",
    stages=[stage_1, ...],
    stage_outcome_map={1: "early", 2: "early", 3: "mid", ...},
    loss_distributions={
        "early": BetaPert(low=2_000, mode=8_000, high=30_000),
        "mid": BetaPert(low=25_000, mode=75_000, high=250_000),
        DetectionResponseFactor.FULL_IMPACT: BetaPert(low=1_000_000, mode=3_000_000, high=5_000_000),
        DetectionResponseFactor.ATTACKER_FAILS: BetaPert(low=2_000, mode=5_000, high=15_000),
    },
)

model.set_detection_response(detection_response)   # statt input_loss_magnitude()
```

`set_detection_response()` und `input_loss_magnitude()` schließen sich
gegenseitig aus. `FairCamModel.calculate()` liefert bei gesetztem
Detection/Response-Modell zusätzlich `outcome_class` und `detected_at_stage`
je Trial.

Ein vollständiges, lauffähiges Beispiel (6-Stufen-Ransomware-Kill-Chain,
kombiniert mit einem Resistive Control) liegt im Repository unter
[`examples/ransomware_scenario.py`](https://github.com/neoprehn/pyfair-cam/blob/main/examples/ransomware_scenario.py).

### Response-Zeit & Detection-SLO (Reporting)

Zwei weitere Kennzahlen sind als reine Reporting-Funktionen verfügbar (nicht
Teil der Risk-Berechnung):

- `DetectionResponseFactor.response_time(n, rng)` – Zeit bis Eindämmung +
  Wiederherstellung unter Berücksichtigung von Überlappung (Concurrency).
- `core.detection_within_time(...)` – "Wie wahrscheinlich ist Erkennung
  innerhalb eines Zeitbudgets T?" (SLO-Validierung, z.B. "Initial Access
  innerhalb von 4 Stunden erkennen").

## Reproduzierbarkeit

Wie pyfair (und wie fair-web es von pyfair kennt) zieht der Simulator alle
Zufallsgrößen aus **einem** einzigen, zentral erzeugten
`numpy.random.Generator` – nie aus globalem `np.random.seed()`. Das gilt auch
für das Detection/Response-Modell: jede der konfigurierten Verlustverteilungen
wird bei jedem Simulationslauf **immer vollständig** für alle Trials gezogen
(nicht nur für die, die sie am Ende brauchen), damit die Anzahl der
RNG-Ziehungen nie vom Zufallsergebnis selbst abhängt.

## Stand

- **Phase 0–2 abgeschlossen:** RNG-Fundament, Resistance/Prevention
  (Frequenz-Seite), Detection & Response (Loss-Magnitude-Seite).
- **Offen:** pyfair-Integration (Phase 3), eigener HTML-Report (Phase 4),
  Web-Integration in fair-web (Phase 5) – siehe
  [Roadmap im pyfair-cam-Repository](https://github.com/neoprehn/pyfair-cam/blob/main/ROADMAP.md).

!!! note "Lizenz"
    pyfair-cam-Code: MIT. Die zugrunde liegende FAIR-CAM-Methodik ist
    CC BY-NC-ND 4.0 (Jack Jones/FAIR Institute) – Details siehe
    [FAIR-CAM-Grundlagen § Attribution & Lizenz](fair-cam-grundlagen.md#attribution-lizenz).
