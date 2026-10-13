"""Tests für apps.cam.cam_tree - Kill-Chain-Layout (graph-nativ) + Cytoscape-Konvertierung."""

from apps.cam import cam_tree
from apps.cam.beispiele import RANSOMWARE_BEISPIEL


class _StageStub:
    """Minimaler Stand-in für CamStage/CamStageForm.instance - kill_chain_layout()
    braucht nur .reihenfolge/.name/.outcome_class (siehe dortiger Docstring)."""

    def __init__(self, reihenfolge, name, outcome_class):
        self.reihenfolge = reihenfolge
        self.name = name
        self.outcome_class = outcome_class


def _ransomware_stages():
    return [_StageStub(s["reihenfolge"], s["name"], s["outcome_class"]) for s in RANSOMWARE_BEISPIEL["stages"]]


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
