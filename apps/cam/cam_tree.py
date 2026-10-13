"""CAM-Diagramme: Knoten/Kanten für die beiden CAM-Grafiken.

Anders als der FAIR-Baum gibt es hier keinen editierbaren "Schnitt" – CAMs
Struktur ist fix (immer genau 1 Resistive Control, 6 Kill-Chain-Stufen, 5
Verlustklassen), die Layout-Funktionen sind daher reine Anzeige-Helfer.

Zwei Diagramme, zwei Darstellungsarten:

- ``susceptibility_layout()`` – die Frequenz-Seite (TEF × Susceptibility über
  das Resistive Control), spiegelt den LEF-Ast des FAIR-Baums. Weiterhin
  statisches SVG, analog zu ``apps.szenarien.fair_tree`` (``nodes``:
  ``[{code, label, x, y, ...}]``, ``edges``: ``[{x1,y1,x2,y2, ...}]``, dieselben
  ``.svg-node``/``.svg-edge``-CSS-Klassen aus ``templates/base.html``).
- ``kill_chain_layout(stages)`` – die Loss-Magnitude-Seite: die Kill-Chain als
  Prozesskette, mit Abzweigungen zu den Outcome-Klassen und den zwei
  Terminal-Zuständen (voller Schaden / Angreifer scheitert). Graph-nativ
  (``edges``: ``[{source, target, kind, label}]``, Knoten-Codes statt
  Koordinaten) für den interaktiven Cytoscape-Graph (``to_cytoscape_elements()``,
  ``static/vendor/cytoscape/``, analog zum Graph-Tab im iam-Projekt) –
  ``x``/``y`` auf den Knoten sind nur noch initiale Positionen (``preset``-
  Layout, danach frei draggable).
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

    Kanten referenzieren Knoten über ``source``/``target`` (Knoten-Codes) statt
    Pixel-Koordinaten – graph-nativ für Cytoscape (siehe ``to_cytoscape_elements``),
    ``x``/``y`` auf den Knoten dienen nur noch als initiale Positionen (``preset``-
    Layout, frei draggable danach).
    """
    stages = sorted(stages, key=lambda s: s.reihenfolge)
    n = len(stages)

    nodes = []
    edges = []
    stage_code = {}

    for s in stages:
        code = f"stage{s.reihenfolge}"
        stage_code[s.reihenfolge] = code
        x = _X0 + (s.reihenfolge - 1) * _DX
        nodes.append({
            "code": code, "kind": "stage",
            "label": f"{s.reihenfolge}. {s.name}", "x": x, "y": _Y_STAGE,
            "reihenfolge": s.reihenfolge,
        })

    for a, b in zip(stages, stages[1:]):
        edges.append({
            "source": stage_code[a.reihenfolge], "target": stage_code[b.reihenfolge],
            "kind": "progression",
        })

    # Outcome-Klasse -> letzte Stufe, die auf sie mappt (bestimmt die x-Position).
    letzte_stufe_je_klasse = {}
    for s in stages:
        letzte_stufe_je_klasse[s.outcome_class] = s.reihenfolge
    klassen_in_reihenfolge = sorted(letzte_stufe_je_klasse, key=lambda k: letzte_stufe_je_klasse[k])

    for klasse in klassen_in_reihenfolge:
        reihenfolge = letzte_stufe_je_klasse[klasse]
        x = _X0 + (reihenfolge - 1) * _DX
        nodes.append({
            "code": klasse, "kind": "outcome",
            "label": klassen_label(klasse), "x": x, "y": _Y_OUTCOME,
        })
    for s in stages:
        edges.append({
            "source": stage_code[s.reihenfolge], "target": s.outcome_class,
            "kind": "outcome", "label": klassen_label(s.outcome_class),
        })

    x_terminal = _X0 + n * _DX
    nodes.append({
        "code": "full_impact", "kind": "outcome",
        "label": klassen_label("full_impact"), "x": x_terminal, "y": _Y_STAGE,
    })
    edges.append({
        "source": stage_code[n], "target": "full_impact", "kind": "progression",
    })

    nodes.append({
        "code": "attacker_fails", "kind": "outcome",
        "label": klassen_label("attacker_fails"), "x": x_terminal, "y": _Y_OUTCOME,
    })
    # Eine gestrichelte Kante statt sechs einzelner (jede Stufe kann theoretisch
    # zum Scheitern führen) - Quelle nominell Stufe 1 (Start der Kette), stellt
    # dasselbe Konzept dar wie zuvor die Mittelpunkt-verankerte SVG-Linie.
    edges.append({
        "source": stage_code[1], "target": "attacker_fails", "kind": "fail",
        "label": "scheitert",
    })

    return nodes, edges


def to_cytoscape_elements(nodes, edges):
    """Wandelt ``(nodes, edges)`` aus ``kill_chain_layout()`` in Cytoscape-``elements``
    um (``cytoscape({elements: ...})``, siehe ``static/vendor/cytoscape/``).

    Knoten mit berechnetem Wert (``n["wert"]``, siehe
    ``CamLaufDetailView._annotiere_kill_chain``) bekommen eine zweite Beschriftungs-
    zeile; Kanten tragen ihr ``label`` direkt (Cytoscape zeichnet es auf der Kante).
    """
    elements = []
    for n in nodes:
        label = f"{n['label']}\n{n['wert']}" if n.get("wert") else n["label"]
        elements.append({
            "data": {
                "id": n["code"], "label": label, "kind": n["kind"],
                "reihenfolge": n.get("reihenfolge"),
            },
            "position": {"x": n["x"], "y": n["y"]},
        })
    for i, e in enumerate(edges):
        elements.append({
            "data": {
                "id": f"e{i}", "source": e["source"], "target": e["target"],
                "label": e.get("label", ""), "kind": e["kind"],
            },
        })
    return elements
