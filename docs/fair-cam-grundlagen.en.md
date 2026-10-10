# FAIR-CAM Fundamentals

**FAIR-CAM** (FAIR Controls Analytics Model) extends the FAIR risk model
with a structured view of *how* security controls actually reduce risk –
individually and in combination. While FAIR models the probability and
magnitude of loss, FAIR-CAM supplies the control physiology underneath it:
what functions a control performs, how those functions combine into
Prevention/Detection/Response, and how to measure their effectiveness
quantitatively instead of assessing it qualitatively.

For the actual calculation, fair-web uses the separate library
**pyfair-cam** ([neoprehn/pyfair-cam](https://github.com/neoprehn/pyfair-cam))
– for engine details see [pyfair-cam (Engine)](pyfair-cam.md).

## Three functional domains

| Domain | Acts | Functions |
|---|---|---|
| **Loss Event (LE)** | directly on risk | Prevention (Avoid/Deter/Resist), Detection (Visibility/Monitoring/Recognition), Response (Containment/Resilience/Loss Minimization) |
| **Variance Management (VM)** | indirectly, via the reliability of other controls | Prevention, Identification, Correction of control failures |
| **Decision Support (DS)** | indirectly, via decision quality | Clarifying expectations, situational awareness, capability, incentives |

pyfair-cam (phase 0–2) currently covers the **Loss Event domain**: the
frequency side (Resistance/Susceptibility) and the loss-magnitude side
(Detection & Response). Variance Management and Decision Support are planned
for later build-out stages.

## Two combination logics

FAIR-CAM distinguishes how multiple controls of the **same** function work
together:

- **Prevention combines as OR:** Each effective prevention control lowers
  risk on its own – multiple layered controls (defense in depth) reduce
  susceptibility multiplicatively.
- **Detection combines as AND:** For an event to be detected, Visibility
  (evidence is captured), Monitoring (evidence is reviewed) and Recognition
  (evidence is correctly interpreted) must **all** work **together**.
- **Response presupposes detection:** No detection, no response – an
  unchecked attack means full loss ("Full Impact").

## Core formulas (as implemented in pyfair-cam)

Reliability, Operational Efficacy and the multi-review detection formula are
standard FAIR-CAM mathematics; pyfair-cam implements them 1:1 in `core.py`.
For details, derivation and the complete formula collection see
[pyfair-cam (Engine)](pyfair-cam.md#formulas).

## Stage-gated Detection & Response

Instead of modeling loss as a continuous function of time, FAIR-CAM breaks
an attack down into discrete **stages** along a kill chain (e.g. MITRE
ATT&CK). Each stage is its own detection opportunity with its own
parameters; a simulated attack proceeds through the stages in order until it
is either detected, naturally aborts, or penetrates undetected to the end
("Full Impact"). The result is a **conditional loss distribution** depending
on the outcome (detected early / detected late / full loss / attacker
fails) instead of a single flat loss figure.

!!! tip "Implementation"
    The complete stage model is implemented in pyfair-cam (`Stage`,
    `DetectionResponseFactor`) – see
    [pyfair-cam (Engine)](pyfair-cam.md#detection-response).

## Attribution & license

**FAIR-CAM as a methodology was developed by Jack Jones** and published by
the [FAIR Institute](https://fairinstitute.org). Official resources:
[fairinstitute.org/FAIR-CAM](https://fairinstitute.org/FAIR-CAM).

The FAIR-CAM materials (knowledge base) are licensed under
**[CC BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/)**
(Attribution – NonCommercial – NoDerivatives). In concrete terms:

- **Attribution**: any use must credit Jack Jones/FAIR Institute as the
  source (this page does so).
- **NonCommercial**: only non-commercial use is permitted – fair-web is a
  private, non-commercial project.
- **NoDerivatives**: the original materials may not be redistributed in
  modified form. This page **does not reproduce the FAIR-CAM texts**, but
  describes the concepts in its own words and refers to the original source
  for the authoritative, complete methodology.

pyfair-cam bundles the official knowledge base (unmodified, as reference
material for the implementation) in the `knowledge-base/` subdirectory of
the repository – also under CC BY-NC-ND 4.0, not part of the MIT-licensed
pyfair-cam code.

**The pyfair-cam code itself is MIT-licensed** (its own implementation of
the formulas, no reuse of KB text). "Open FAIR" is also a trademark of The
Open Group (see [Fork Extensions](pyfair-fork.md)).
