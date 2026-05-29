"""Der FAIR-Baum: Knoten, Hierarchie, Faktortypen.

Abgeleitet aus pyfairs ``model_tree.FairDependencyTree``. Der Nutzer gibt
einen *Schnitt* durch den Baum an (eine „Antikette", die den Risk-Knoten
vollständig abdeckt); pyfair rechnet daraus nach oben bis ``Risk``.

Faktortypen:
- ``frequency``   – Häufigkeiten (≥ 0)
- ``probability`` – Wahrscheinlichkeiten, müssen in [0, 1] liegen
- ``magnitude``   – Geldbeträge (≥ 0)
"""

# code -> (pyfair-Zielname, Kürzel, Eltern-Code|None, Typ)
FAIR_NODES = {
    "LEF":  ("Loss Event Frequency",           "LEF",  None,   "frequency"),
    "TEF":  ("Threat Event Frequency",         "TEF",  "LEF",  "frequency"),
    "CF":   ("Contact Frequency",              "CF",   "TEF",  "frequency"),
    "POA":  ("Probability of Action",          "PoA",  "TEF",  "probability"),
    "VULN": ("Vulnerability",                  "Vuln", "LEF",  "probability"),
    "TC":   ("Threat Capability",              "TC",   "VULN", "probability"),
    "CS":   ("Control Strength",               "CS",   "VULN", "probability"),
    "LM":   ("Loss Magnitude",                 "LM",   None,   "magnitude"),
    "PL":   ("Primary Loss",                   "PL",   "LM",   "magnitude"),
    "SL":   ("Secondary Loss",                 "SL",   "LM",   "magnitude"),
    "SLEF": ("Secondary Loss Event Frequency", "SLEF", "SL",   "frequency"),
    "SLEM": ("Secondary Loss Event Magnitude", "SLEM", "SL",   "magnitude"),
}

# Die zwei Top-Äste, die zusammen Risk ergeben (Risk = LEF × LM).
ROOT_CHILDREN = ["LEF", "LM"]

# Kinder je Knoten (aus den Eltern-Verweisen abgeleitet, Reihenfolge stabil).
CHILDREN = {}
for _code, (_name, _abbr, _parent, _typ) in FAIR_NODES.items():
    if _parent:
        CHILDREN.setdefault(_parent, []).append(_code)

# Blätter = Knoten ohne Kinder.
LEAVES = [code for code in FAIR_NODES if code not in CHILDREN]

# Erlaubte Verteilungen je Faktortyp (Wahrscheinlichkeiten ohne unbeschränkte
# Normalverteilung; gebunden auf [0,1] wird zusätzlich validiert).
DISTS_BY_TYP = {
    "frequency":   ["pert", "normal", "constant"],
    "probability": ["pert", "constant"],
    "magnitude":   ["pert", "normal", "constant"],
}


def target(code):
    """pyfair-Zielname für einen Knoten-Code (z. B. 'VULN' -> 'Vulnerability')."""
    return FAIR_NODES[code][0]


def abbr(code):
    return FAIR_NODES[code][1]


def parent(code):
    return FAIR_NODES[code][2]


def typ(code):
    return FAIR_NODES[code][3]


def ist_gebunden(code):
    """True, wenn der Faktor in [0, 1] liegen muss (Wahrscheinlichkeit)."""
    return FAIR_NODES[code][3] == "probability"


def erlaubte_verteilungen(code):
    return DISTS_BY_TYP[FAIR_NODES[code][3]]


def vorfahren(code):
    """Liste der Vorfahren-Codes bis zur Wurzel."""
    kette = []
    p = parent(code)
    while p:
        kette.append(p)
        p = parent(p)
    return kette


def schnitt_ist_gueltig(codes):
    """Prüft, ob die angegebenen Knoten einen gültigen Schnitt durch den Baum bilden.

    Gültig heißt: jeder Top-Ast (LEF, LM) ist vollständig abgedeckt (selbst
    angegeben ODER alle Kinder abgedeckt) UND kein Knoten ist gleichzeitig mit
    einem seiner Vorfahren angegeben (keine Redundanz).
    """
    codes = set(codes)

    # Keine doppelte Angabe entlang eines Astes.
    for code in codes:
        if any(v in codes for v in vorfahren(code)):
            return False

    def abgedeckt(code):
        if code in codes:
            return True
        kinder = CHILDREN.get(code)
        if not kinder:
            return False
        return all(abgedeckt(k) for k in kinder)

    return all(abgedeckt(ast) for ast in ROOT_CHILDREN)
