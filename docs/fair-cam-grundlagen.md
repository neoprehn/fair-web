# FAIR-CAM-Grundlagen

**FAIR-CAM** (FAIR Controls Analytics Model) erweitert das FAIR-Risikomodell
um eine strukturierte Betrachtung, *wie* Sicherheits-Controls Risiko
tatsächlich reduzieren – einzeln und im Zusammenspiel. Während FAIR die
Verlustwahrscheinlichkeit und -höhe modelliert, liefert FAIR-CAM die
Control-Physiologie darunter: welche Funktionen ein Control erfüllt, wie
diese Funktionen sich zu Prevention/Detection/Response kombinieren, und wie
man ihre Wirksamkeit quantitativ misst statt qualitativ einzuschätzen.

fair-web nutzt für die eigentliche Berechnung die separate Bibliothek
**pyfair-cam** ([neoprehn/pyfair-cam](https://github.com/neoprehn/pyfair-cam))
– Engine-Details siehe [pyfair-cam (Engine)](pyfair-cam.md).

## Drei funktionale Domänen

| Domäne | Wirkt | Funktionen |
|---|---|---|
| **Loss Event (LE)** | direkt auf das Risiko | Prevention (Avoid/Deter/Resist), Detection (Visibility/Monitoring/Recognition), Response (Containment/Resilience/Loss Minimization) |
| **Variance Management (VM)** | indirekt, über die Zuverlässigkeit anderer Controls | Prevention, Identification, Correction von Control-Ausfällen |
| **Decision Support (DS)** | indirekt, über die Entscheidungsqualität | Erwartungsklärung, Situationsbewusstsein, Fähigkeit, Anreize |

pyfair-cam (Phase 0–2) bildet aktuell die **Loss-Event-Domäne** ab: die
Frequenz-Seite (Resistance/Susceptibility) und die Loss-Magnitude-Seite
(Detection & Response). Variance Management und Decision Support sind für
spätere Ausbaustufen vorgesehen.

## Zwei Verknüpfungslogiken

FAIR-CAM unterscheidet, wie mehrere Controls **derselben** Funktion
zusammenwirken:

- **Prevention verknüpft als ODER:** Jedes wirksame Prevention-Control senkt
  das Risiko für sich – mehrere gestaffelte Controls (Defense-in-Depth)
  reduzieren die Susceptibility multiplikativ.
- **Detection verknüpft als UND:** Damit ein Ereignis erkannt wird, müssen
  Visibility (Evidenz wird erfasst), Monitoring (Evidenz wird geprüft) und
  Recognition (Evidenz wird korrekt eingeordnet) **gemeinsam** funktionieren.
- **Response setzt Detection voraus:** Ohne Erkennung keine Reaktion –
  ungebremster Angriff bedeutet vollen Schaden ("Full Impact").

## Kernformeln (wie in pyfair-cam implementiert)

Reliability, Operational Efficacy und die Multi-Review-Detection-Formel sind
Standard-FAIR-CAM-Mathematik; pyfair-cam implementiert sie 1:1 in `core.py`.
Details, Herleitung und die vollständige Formelsammlung siehe
[pyfair-cam (Engine)](pyfair-cam.md#formeln).

## Stage-Gated Detection & Response

Statt Verlust als kontinuierliche Funktion der Zeit zu modellieren, zerlegt
FAIR-CAM einen Angriff in diskrete **Stufen** entlang einer Kill-Chain (z.B.
MITRE ATT&CK). Jede Stufe ist eine eigene Erkennungsgelegenheit mit eigenen
Parametern; ein simulierter Angriff durchläuft die Stufen der Reihe nach, bis
er entdeckt wird, natürlich abbricht, oder unentdeckt bis zum Ende
durchdringt ("Full Impact"). Das Ergebnis ist eine **bedingte
Verlustverteilung** je nach Ausgang (früh erkannt / spät erkannt / voller
Schaden / Angreifer scheitert) statt einer pauschalen Schadenshöhe.

!!! tip "Umsetzung"
    Das vollständige Stage-Modell ist in pyfair-cam implementiert
    (`Stage`, `DetectionResponseFactor`) – siehe
    [pyfair-cam (Engine)](pyfair-cam.md#detection-response).

## Attribution & Lizenz

**FAIR-CAM als Methodik wurde von Jack Jones entwickelt** und vom
[FAIR Institute](https://fairinstitute.org) veröffentlicht. Offizielle
Ressourcen: [fairinstitute.org/FAIR-CAM](https://fairinstitute.org/FAIR-CAM).

Die FAIR-CAM-Materialien (Knowledge Base) stehen unter
**[CC BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/)**
(Attribution – NonCommercial – NoDerivatives). Das bedeutet konkret:

- **Attribution**: Jede Nutzung muss Jack Jones/FAIR Institute als Quelle
  nennen (diese Seite tut das).
- **NonCommercial**: Nur nicht-kommerzielle Nutzung erlaubt – fair-web ist
  ein privates, nicht-kommerzielles Projekt.
- **NoDerivatives**: Die Original-Materialien dürfen nicht verändert
  weiterverbreitet werden. Diese Seite **reproduziert die FAIR-CAM-Texte
  nicht**, sondern beschreibt die Konzepte in eigenen Worten und verweist
  für die maßgebliche, vollständige Methodik auf die Originalquelle.

pyfair-cam bündelt die offizielle Knowledge Base (unverändert, als
Referenzmaterial für die Implementierung) im Unterordner `knowledge-base/`
des Repositories – ebenfalls unter CC BY-NC-ND 4.0, nicht Teil des
MIT-lizenzierten pyfair-cam-Codes.

**Der pyfair-cam-Code selbst ist MIT-lizenziert** (eigene Implementierung der
Formeln, keine Übernahme von KB-Text). "Open FAIR" ist außerdem eine Marke
der Open Group (vgl. [Fork-Erweiterungen](pyfair-fork.md)).
