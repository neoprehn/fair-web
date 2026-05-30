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

# pyfair-Knotenname -> unser Code (Umkehrung für Ergebnis-Auswertung).
CODE_FUER_NAME = {name: code for code, (name, _a, _p, _t) in FAIR_NODES.items()}

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
    "probability": ["pert", "beta", "constant"],
    "magnitude":   ["pert", "lognormal", "normal", "constant"],
}

# Vorgeschlagene Standard-Verteilung je Knoten (fett aus der FAIR-Tabelle).
STANDARD_VERTEILUNG = {
    "LEF": "pert", "TEF": "pert", "CF": "poisson", "SLEF": "poisson",
    "POA": "beta", "VULN": "beta", "TC": "pert", "CS": "pert",
    "LM": "lognormal", "PL": "lognormal", "SLEM": "lognormal",
}

# Knoten-spezifische Abweichung der erlaubten Verteilungen (CF/SLEF: echte Counts → Poisson).
ERLAUBTE_OVERRIDE = {
    "CF": ["poisson", "pert", "normal", "constant"],
    "SLEF": ["poisson", "pert", "normal", "constant"],
}


def standard_verteilung(code):
    return STANDARD_VERTEILUNG.get(code, "pert")


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
    if code in ERLAUBTE_OVERRIDE:
        return ERLAUBTE_OVERRIDE[code]
    return DISTS_BY_TYP[FAIR_NODES[code][3]]


def vorfahren(code):
    """Liste der Vorfahren-Codes bis zur Wurzel."""
    kette = []
    p = parent(code)
    while p:
        kette.append(p)
        p = parent(p)
    return kette


def ist_blatt(code):
    return code not in CHILDREN


# Feste Positionen (x, y) für die SVG-Darstellung des Baums (inkl. Risk-Wurzel).
SVG_POS = {
    "Risk": (461, 26),
    "LEF": (240, 92), "LM": (682, 92),
    "TEF": (125, 158), "VULN": (355, 158), "PL": (590, 158), "SL": (775, 158),
    "CF": (70, 224), "POA": (185, 224), "TC": (300, 224), "CS": (415, 224),
    "SLEF": (720, 224), "SLEM": (830, 224),
}


def svg_layout():
    """Knoten + Kanten für das FAIR-Baum-SVG.

    Returns (nodes, edges):
      nodes: [{code, label, x, y}]  (label = Kürzel, Risk als 'R')
      edges: [{x1, y1, x2, y2}]
    """
    nodes = []
    for code, (x, y) in SVG_POS.items():
        label = "R" if code == "Risk" else abbr(code)
        nodes.append({"code": code, "label": label, "x": x, "y": y})

    paare = [("Risk", "LEF"), ("Risk", "LM")]
    for code, (_n, _a, parent_code, _t) in FAIR_NODES.items():
        if parent_code:
            paare.append((parent_code, code))

    edges = []
    for a, b in paare:
        x1, y1 = SVG_POS[a]
        x2, y2 = SVG_POS[b]
        edges.append({"x1": x1, "y1": y1, "x2": x2, "y2": y2})
    return nodes, edges


# Nicht-Blatt-Knoten (haben einen „direkt/aufschlüsseln"-Umschalter).
NICHT_BLATT = [code for code in FAIR_NODES if code in CHILDREN]


def traversal():
    """DFS-Reihenfolge ab den Top-Ästen als Liste von (code, tiefe)."""
    out = []

    def rec(code, tiefe):
        out.append((code, tiefe))
        for kind in CHILDREN.get(code, []):
            rec(kind, tiefe + 1)

    for ast in ROOT_CHILDREN:
        rec(ast, 0)
    return out


def traversal_ast(ast):
    """DFS-Reihenfolge eines einzelnen Astes (Tiefe relativ zum Ast-Wurzelknoten)."""
    out = []

    def rec(code, tiefe):
        out.append((code, tiefe))
        for kind in CHILDREN.get(code, []):
            rec(kind, tiefe + 1)

    rec(ast, 0)
    return out


def frontier_aus_modus(modus):
    """Aktiver Schnitt aus der Modus-Karte ({code: 'direkt'|'aufschluesseln'}).

    Blätter und auf „direkt" gestellte Knoten sind Eingabe-Knoten; auf
    „aufschluesseln" gestellte Knoten werden durch ihre Kinder ersetzt.
    Fehlt ein Modus, gilt „direkt".
    """
    front = []

    def rec(code):
        if ist_blatt(code) or modus.get(code, "direkt") == "direkt":
            front.append(code)
        else:
            for kind in CHILDREN[code]:
                rec(kind)

    for ast in ROOT_CHILDREN:
        rec(ast)
    return front


def modus_aus_codes(codes):
    """Leitet die Modus-Karte aus einem vorhandenen Schnitt ab (fürs Bearbeiten)."""
    codes = set(codes)
    modus = {}
    for code in NICHT_BLATT:
        if code in codes:
            modus[code] = "direkt"
        elif any(k in codes for k in _nachfahren(code)):
            modus[code] = "aufschluesseln"
        else:
            modus[code] = "direkt"
    return modus


def _nachfahren(code):
    out = []
    for kind in CHILDREN.get(code, []):
        out.append(kind)
        out.extend(_nachfahren(kind))
    return out


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
