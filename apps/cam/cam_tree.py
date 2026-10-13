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


# Die 14 MITRE ATT&CK Enterprise Tactics, kanonische Navigator-Spaltenreihenfolge
# (links -> rechts) - muss mit CamStage.AttackTactic übereinstimmen (hier dupliziert
# statt importiert, damit cam_tree weiterhin ein reiner, modellunabhängiger
# Anzeige-Helfer bleibt). Nur für die optionale MITRE-ATT&CK-Ansicht der Kill-Chain,
# keine Auswirkung auf die Risikoberechnung.
ATTACK_TACTIC_ORDER = [
    "TA0043", "TA0042", "TA0001", "TA0002", "TA0003", "TA0004", "TA0005",
    "TA0006", "TA0007", "TA0008", "TA0009", "TA0011", "TA0010", "TA0040",
]
ATTACK_TACTIC_LABEL = {
    "TA0043": "Reconnaissance", "TA0042": "Resource Development",
    "TA0001": "Initial Access", "TA0002": "Execution", "TA0003": "Persistence",
    "TA0004": "Privilege Escalation", "TA0005": "Defense Evasion",
    "TA0006": "Credential Access", "TA0007": "Discovery",
    "TA0008": "Lateral Movement", "TA0009": "Collection",
    "TA0011": "Command and Control", "TA0010": "Exfiltration", "TA0040": "Impact",
}

_ATTACK_X0 = 70
_ATTACK_DX = 130
_ATTACK_Y0 = 60
_ATTACK_ROW_DY = 55


def attack_position(tactic, row=0):
    """Position einer Stufe in der MITRE-ATT&CK-Ansicht (Spalte = Tactic-Index in
    ``ATTACK_TACTIC_ORDER``, ``row`` für mehrere Stufen mit derselben Tactic
    übereinander) - ``None``, wenn keine/eine unbekannte Tactic zugeordnet ist."""
    if tactic not in ATTACK_TACTIC_ORDER:
        return None
    x = _ATTACK_X0 + ATTACK_TACTIC_ORDER.index(tactic) * _ATTACK_DX
    y = _ATTACK_Y0 + row * _ATTACK_ROW_DY
    return {"x": x, "y": y}


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
            "attack_tactic": getattr(s, "attack_tactic", "") or "",
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

    Stufen-Knoten mit zugeordneter MITRE-ATT&CK-Tactic bekommen zusätzlich
    ``attack_position`` (Spalte = Tactic, siehe ``attack_position()``) sowie eine
    dritte Beschriftungszeile mit dem Tactic-Namen - fürs Umschalten auf die
    MITRE-ATT&CK-Ansicht im Frontend (JS liest ``attack_position``/``attack_label``;
    ``None`` bedeutet "in dieser Ansicht ausblenden", z. B. bei Outcome-Knoten oder
    Stufen ohne Zuordnung).
    """
    # Zeilen-Index je Tactic (mehrere Stufen mit derselben Tactic werden in der
    # ATT&CK-Ansicht in derselben Spalte übereinander gestapelt statt überlappt).
    naechste_zeile = {}

    elements = []
    for n in nodes:
        label = f"{n['label']}\n{n['wert']}" if n.get("wert") else n["label"]
        data = {
            "id": n["code"], "label": label, "kind": n["kind"],
            "reihenfolge": n.get("reihenfolge"),
        }
        tactic = n.get("attack_tactic")
        if tactic:
            row = naechste_zeile.get(tactic, 0)
            naechste_zeile[tactic] = row + 1
            pos = attack_position(tactic, row)
            if pos:
                data["attack_position"] = pos
                data["attack_label"] = f"{n['label']}\n{ATTACK_TACTIC_LABEL.get(tactic, tactic)}"
        elements.append({"data": data, "position": {"x": n["x"], "y": n["y"]}})
    for i, e in enumerate(edges):
        elements.append({
            "data": {
                "id": f"e{i}", "source": e["source"], "target": e["target"],
                "label": e.get("label", ""), "kind": e["kind"],
            },
        })
    return elements
