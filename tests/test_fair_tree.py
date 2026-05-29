"""Tests für den FAIR-Baum (Struktur, Schnitt-Gültigkeit, Bounded-Validierung)."""

import pytest
from django.core.exceptions import ValidationError

from apps.szenarien import fair_tree
from apps.szenarien.models import FaktorEingabe


# ---------------------------------------------------------------------------
# Baumstruktur
# ---------------------------------------------------------------------------

def test_kinder_und_blaetter():
    assert fair_tree.CHILDREN["LEF"] == ["TEF", "VULN"]
    assert fair_tree.CHILDREN["TEF"] == ["CF", "POA"]
    assert fair_tree.CHILDREN["VULN"] == ["TC", "CS"]
    assert fair_tree.CHILDREN["LM"] == ["PL", "SL"]
    assert fair_tree.CHILDREN["SL"] == ["SLEF", "SLEM"]
    assert set(fair_tree.LEAVES) == {"CF", "POA", "TC", "CS", "PL", "SLEF", "SLEM"}


def test_target_und_typ():
    assert fair_tree.target("VULN") == "Vulnerability"
    assert fair_tree.target("TEF") == "Threat Event Frequency"
    assert fair_tree.ist_gebunden("VULN") and fair_tree.ist_gebunden("POA")
    assert not fair_tree.ist_gebunden("LEF") and not fair_tree.ist_gebunden("LM")
    assert "normal" not in fair_tree.erlaubte_verteilungen("VULN")
    assert "normal" in fair_tree.erlaubte_verteilungen("LEF")


def test_vorfahren():
    assert fair_tree.vorfahren("CS") == ["VULN", "LEF"]
    assert fair_tree.vorfahren("LEF") == []


def test_svg_layout():
    nodes, edges = fair_tree.svg_layout()
    codes = {n["code"] for n in nodes}
    assert codes == set(fair_tree.FAIR_NODES) | {"Risk"}  # 12 Knoten + Risk
    assert len(edges) == 12  # 2 (Risk) + 10 Eltern-Kind-Kanten
    risk = next(n for n in nodes if n["code"] == "Risk")
    assert risk["label"] == "R"


# ---------------------------------------------------------------------------
# Schnitt-Gültigkeit
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("codes", [
    ["LEF", "LM"],
    ["TEF", "VULN", "LM"],
    ["CF", "POA", "TC", "CS", "PL", "SL"],
    ["LEF", "PL", "SL"],
])
def test_gueltige_schnitte(codes):
    assert fair_tree.schnitt_ist_gueltig(codes)


@pytest.mark.parametrize("codes", [
    ["LEF"],                  # LM-Ast fehlt
    ["LM"],                   # LEF-Ast fehlt
    ["TEF", "LM"],            # Vulnerability fehlt im LEF-Ast
    ["LEF", "TEF", "LM"],     # LEF UND sein Kind TEF -> redundant
    [],
])
def test_ungueltige_schnitte(codes):
    assert not fair_tree.schnitt_ist_gueltig(codes)


# ---------------------------------------------------------------------------
# Bounded-Validierung im Modell
# ---------------------------------------------------------------------------

def test_wahrscheinlichkeit_ueber_eins_unzulaessig():
    f = FaktorEingabe(faktor="VULN", verteilung="constant", params={"constant": 1.5})
    with pytest.raises(ValidationError):
        f.clean()


def test_wahrscheinlichkeit_in_bereich_ok():
    f = FaktorEingabe(faktor="VULN", verteilung="constant", params={"constant": 0.4})
    f.clean()  # darf nicht werfen


def test_frequenz_darf_ueber_eins():
    f = FaktorEingabe(faktor="TEF", verteilung="constant", params={"constant": 12})
    f.clean()  # Häufigkeit > 1 ist erlaubt


def test_fair_target_neuer_knoten():
    f = FaktorEingabe(faktor="SLEM")
    assert f.fair_target == "Secondary Loss Event Magnitude"
    assert f.faktor_abbr == "SLEM"
