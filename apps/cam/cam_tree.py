"""CAM-Diagramme: Knoten/Kanten fürs SVG, analog zu ``apps.szenarien.fair_tree``.

Anders als der FAIR-Baum gibt es hier keinen editierbaren "Schnitt" – CAMs
Struktur ist fix (immer genau 1 Resistive Control, 6 Kill-Chain-Stufen, 5
Verlustklassen), die Layout-Funktionen sind daher reine Anzeige-Helfer.

Zwei Diagramme:

- ``susceptibility_layout()`` – die Frequenz-Seite (TEF × Susceptibility über
  das Resistive Control), spiegelt den LEF-Ast des FAIR-Baums.
- ``kill_chain_layout(stages)`` – die Loss-Magnitude-Seite: die Kill-Chain
  als horizontale Prozesskette, mit Abzweigungen zu den Outcome-Klassen und
  den zwei Terminal-Zuständen (voller Schaden / Angreifer scheitert).

Beide liefern ``(nodes, edges)`` im selben Format wie ``fair_tree.svg_layout()``
(``nodes: [{code, label, x, y, ...}]``, ``edges: [{x1,y1,x2,y2, ...}]``), damit
die Templates dieselben ``.svg-node``/``.svg-edge``-CSS-Klassen aus
``templates/base.html`` wiederverwenden können.
"""

KLASSEN_LABEL = {
    "early": "Früh",
    "mid": "Mittel",
    "late": "Spät",
    "full_impact": "Voller Schaden",
    "attacker_fails": "Angreifer scheitert",
}


def klassen_label(klasse):
    return KLASSEN_LABEL.get(klasse, klasse)


# Statische Positionen für den Susceptibility-Ast (spiegelt FAIRs LEF ← TEF, VULN).
_SUSC_POS = {
    "LEF": (180, 30),
    "TEF": (70, 100),
    "SUSC": (290, 100),
    "CONTROL": (290, 175),
}


def susceptibility_layout():
    """Knoten + Kanten für den Frequenz-Seite-Baum (TEF × Susceptibility)."""
    nodes = [
        {"code": "LEF", "kind": "computed", "label": "LEF", "x": _SUSC_POS["LEF"][0], "y": _SUSC_POS["LEF"][1]},
        {"code": "TEF", "kind": "input", "label": "TEF", "x": _SUSC_POS["TEF"][0], "y": _SUSC_POS["TEF"][1]},
        {"code": "SUSC", "kind": "computed", "label": "Susceptibility", "x": _SUSC_POS["SUSC"][0], "y": _SUSC_POS["SUSC"][1]},
        {"code": "CONTROL", "kind": "input", "label": "Control", "x": _SUSC_POS["CONTROL"][0], "y": _SUSC_POS["CONTROL"][1]},
    ]
    edges = [
        {"x1": _SUSC_POS["LEF"][0], "y1": _SUSC_POS["LEF"][1], "x2": _SUSC_POS["TEF"][0], "y2": _SUSC_POS["TEF"][1]},
        {"x1": _SUSC_POS["LEF"][0], "y1": _SUSC_POS["LEF"][1], "x2": _SUSC_POS["SUSC"][0], "y2": _SUSC_POS["SUSC"][1]},
        {"x1": _SUSC_POS["SUSC"][0], "y1": _SUSC_POS["SUSC"][1], "x2": _SUSC_POS["CONTROL"][0], "y2": _SUSC_POS["CONTROL"][1]},
    ]
    return nodes, edges


_X0 = 80
_DX = 150
_Y_STAGE = 60
_Y_OUTCOME = 190


def kill_chain_layout(stages):
    """Knoten + Kanten für die Kill-Chain (Detection & Response) als Prozesskette.

    ``stages``: Iterable mit ``.reihenfolge``/``.name``/``.outcome_class`` — sowohl
    ein ``CamStage``-Queryset (Ergebnis-Seite) als auch eine Liste von
    ``CamStageForm``-Instanzen (Eingabeformular, vor dem Speichern) erfüllen das.
    """
    stages = sorted(stages, key=lambda s: s.reihenfolge)
    n = len(stages)

    nodes = []
    edges = []
    stage_x = {}

    for s in stages:
        x = _X0 + (s.reihenfolge - 1) * _DX
        stage_x[s.reihenfolge] = x
        nodes.append({
            "code": f"stage{s.reihenfolge}", "kind": "stage",
            "label": f"{s.reihenfolge}. {s.name}", "x": x, "y": _Y_STAGE,
            "reihenfolge": s.reihenfolge,
        })

    for a, b in zip(stages, stages[1:]):
        edges.append({
            "x1": stage_x[a.reihenfolge], "y1": _Y_STAGE,
            "x2": stage_x[b.reihenfolge], "y2": _Y_STAGE,
            "kind": "progression",
        })

    # Outcome-Klasse -> letzte Stufe, die auf sie mappt (bestimmt die x-Position).
    letzte_stufe_je_klasse = {}
    for s in stages:
        letzte_stufe_je_klasse[s.outcome_class] = s.reihenfolge
    klassen_in_reihenfolge = sorted(letzte_stufe_je_klasse, key=lambda k: letzte_stufe_je_klasse[k])

    outcome_x = {}
    for klasse in klassen_in_reihenfolge:
        x = stage_x[letzte_stufe_je_klasse[klasse]]
        outcome_x[klasse] = x
        nodes.append({
            "code": klasse, "kind": "outcome",
            "label": klassen_label(klasse), "x": x, "y": _Y_OUTCOME,
        })
    for s in stages:
        edges.append({
            "x1": stage_x[s.reihenfolge], "y1": _Y_STAGE,
            "x2": outcome_x[s.outcome_class], "y2": _Y_OUTCOME,
            "kind": "outcome",
        })

    x_terminal = _X0 + n * _DX
    nodes.append({
        "code": "full_impact", "kind": "outcome",
        "label": klassen_label("full_impact"), "x": x_terminal, "y": _Y_STAGE,
    })
    edges.append({
        "x1": stage_x[n], "y1": _Y_STAGE, "x2": x_terminal, "y2": _Y_STAGE, "kind": "progression",
    })

    nodes.append({
        "code": "attacker_fails", "kind": "outcome",
        "label": klassen_label("attacker_fails"), "x": x_terminal, "y": _Y_OUTCOME,
    })
    # Eine gesammelte, gestrichelte Kante statt sechs einzelner (jede Stufe kann
    # theoretisch zum Scheitern führen) - Ausgangspunkt knapp unter der Stufenreihe,
    # damit die Linie nicht optisch durch die Stufen-Boxen läuft.
    mitte_x = (stage_x[1] + stage_x[n]) / 2
    edges.append({
        "x1": mitte_x, "y1": _Y_STAGE + 26, "x2": x_terminal, "y2": _Y_OUTCOME, "kind": "fail",
    })

    return nodes, edges
