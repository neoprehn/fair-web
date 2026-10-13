"""Tests für apps.cam.cam_tree - Kill-Chain-Layout (graph-nativ) + Cytoscape-Konvertierung."""

from apps.cam import cam_tree
from apps.cam.beispiele import RANSOMWARE_BEISPIEL


class _StageStub:
    """Minimaler Stand-in für CamStage/CamStageForm.instance - kill_chain_layout()
    braucht nur .reihenfolge/.name/.outcome_class/.attack_tactic (siehe dortiger Docstring)."""

    def __init__(self, reihenfolge, name, outcome_class, attack_tactic=""):
        self.reihenfolge = reihenfolge
        self.name = name
        self.outcome_class = outcome_class
        self.attack_tactic = attack_tactic


def _ransomware_stages():
    return [
        _StageStub(s["reihenfolge"], s["name"], s["outcome_class"], s.get("attack_tactic", ""))
        for s in RANSOMWARE_BEISPIEL["stages"]
    ]


def test_kill_chain_layout_kanten_referenzieren_knoten_codes_nicht_koordinaten():
    nodes, edges = cam_tree.kill_chain_layout(_ransomware_stages())
    node_codes = {n["code"] for n in nodes}

    assert edges  # es gibt überhaupt Kanten
    for e in edges:
        assert "source" in e and "target" in e
        assert "x1" not in e and "x2" not in e  # alte, koordinatenbasierte Form ist weg
        assert e["source"] in node_codes
        assert e["target"] in node_codes


def test_kill_chain_layout_enthaelt_progression_outcome_und_fail_kanten():
    nodes, edges = cam_tree.kill_chain_layout(_ransomware_stages())
    kinds = {e["kind"] for e in edges}
    assert kinds == {"progression", "outcome", "fail"}

    fail_edges = [e for e in edges if e["kind"] == "fail"]
    assert len(fail_edges) == 1  # eine gesammelte Kante, nicht eine je Stufe
    assert fail_edges[0]["target"] == "attacker_fails"

    outcome_edges = [e for e in edges if e["kind"] == "outcome"]
    assert len(outcome_edges) == len(_ransomware_stages())  # eine je Stufe


def test_to_cytoscape_elements_baut_knoten_mit_position_und_kanten_mit_label():
    nodes, edges = cam_tree.kill_chain_layout(_ransomware_stages())
    elements = cam_tree.to_cytoscape_elements(nodes, edges)

    node_elements = [el for el in elements if "position" in el]
    edge_elements = [el for el in elements if "position" not in el]
    assert len(node_elements) == len(nodes)
    assert len(edge_elements) == len(edges)

    stage1 = next(el for el in node_elements if el["data"]["id"] == "stage1")
    assert stage1["position"] == {"x": 80, "y": 60}
    assert "1." in stage1["data"]["label"]

    fail_edge = next(el for el in edge_elements if el["data"]["kind"] == "fail")
    assert fail_edge["data"]["label"] == "scheitert"


def test_to_cytoscape_elements_zweite_beschriftungszeile_bei_berechnetem_wert():
    nodes, edges = cam_tree.kill_chain_layout(_ransomware_stages())
    for n in nodes:
        if n["code"] == "stage1":
            n["wert"] = "42.0 %"
    elements = cam_tree.to_cytoscape_elements(nodes, edges)
    stage1 = next(el for el in elements if el.get("data", {}).get("id") == "stage1")
    assert "42.0 %" in stage1["data"]["label"]
    assert "\n" in stage1["data"]["label"]


def test_attack_position_ordnet_spalte_nach_kanonischer_tactic_reihenfolge():
    """Initial Access (TA0001) liegt laut ATTACK_TACTIC_ORDER nach Reconnaissance (TA0043)
    und Resource Development (TA0042), also in Spalte 2 (Index 2)."""
    pos_ia = cam_tree.attack_position("TA0001")
    pos_recon = cam_tree.attack_position("TA0043")
    assert pos_ia["x"] > pos_recon["x"]
    assert cam_tree.ATTACK_TACTIC_ORDER.index("TA0001") == 2


def test_attack_position_unbekannte_oder_leere_tactic_gibt_none():
    assert cam_tree.attack_position("") is None
    assert cam_tree.attack_position("keine-echte-tactic") is None


def test_attack_position_mehrere_stufen_gleiche_tactic_werden_gestapelt():
    pos_row0 = cam_tree.attack_position("TA0001", row=0)
    pos_row1 = cam_tree.attack_position("TA0001", row=1)
    assert pos_row0["x"] == pos_row1["x"]
    assert pos_row1["y"] > pos_row0["y"]


def test_to_cytoscape_elements_stufen_mit_tactic_bekommen_attack_position():
    nodes, edges = cam_tree.kill_chain_layout(_ransomware_stages())
    elements = cam_tree.to_cytoscape_elements(nodes, edges)
    stage_elements = {
        el["data"]["id"]: el["data"] for el in elements
        if el["data"].get("kind") == "stage"
    }
    # Alle 6 Ransomware-Beispielstufen haben in beispiele.py eine attack_tactic gesetzt.
    for code in ("stage1", "stage2", "stage3", "stage4", "stage5", "stage6"):
        assert "attack_position" in stage_elements[code]
        assert "attack_label" in stage_elements[code]

    outcome_elements = [el["data"] for el in elements if el["data"].get("kind") == "outcome"]
    for data in outcome_elements:
        assert "attack_position" not in data  # Outcome-Knoten haben keine Tactic


def test_to_cytoscape_elements_stufe_ohne_tactic_bekommt_keine_attack_position():
    stages = _ransomware_stages()
    stages[0].attack_tactic = ""  # Zuordnung entfernen
    nodes, edges = cam_tree.kill_chain_layout(stages)
    elements = cam_tree.to_cytoscape_elements(nodes, edges)
    stage1 = next(el["data"] for el in elements if el["data"]["id"] == "stage1")
    assert "attack_position" not in stage1
