"""Datenmodell für FAIR-Szenarien.

Ein ``Szenario`` bündelt die Metadaten einer Monte-Carlo-Simulation
(Name, Simulationsanzahl, Seed) und besitzt pro FAIR-Risikofaktor eine
``FaktorEingabe`` mit frei wählbarer Verteilung. Aus den Eingaben lässt
sich direkt ein pyfair-``FairModel`` füttern (Phase 4).
"""

import math

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from . import fair_tree
from .fair_confidence import (
    CONFIDENCE_DISTRIBUTIONS,
    UNSICHERHEIT_DEFAULT,
    UNSICHERHEIT_MAX,
    UNSICHERHEIT_MIN,
    UNSICHERHEIT_TO_CONFIDENCE,
    UNSICHERHEIT_LABELS,
    aktuelle_konfidenz_defaults,
)


class Angreifertyp(models.Model):
    """Vordefiniertes Threat-Capability-Profil (PERT für Threat Capability).

    Dient als Auswahl-Vorlage im Formular (füllt die TC-Werte vor). Im
    späteren Admin-Bereich editierbar (wie auch die Konfidenz-Vorgaben).
    """

    name = models.CharField("Bezeichnung", max_length=120, unique=True)
    beschreibung = models.CharField("Beschreibung", max_length=200, blank=True)
    low = models.FloatField("Minimum (0–1)")
    mode = models.FloatField("Wahrscheinlich (0–1)")
    high = models.FloatField("Maximum (0–1)")
    begruendung = models.CharField("Begründung", max_length=200, blank=True)
    typisches_szenario = models.CharField("Typisches Szenario", max_length=200, blank=True)
    reihenfolge = models.PositiveSmallIntegerField("Reihenfolge", default=0)

    class Meta:
        verbose_name = "Angreifertyp"
        verbose_name_plural = "Angreifertypen"
        ordering = ["reihenfolge", "name"]

    def __str__(self):
        return self.name


class Szenario(models.Model):
    class LMModus(models.TextChoices):
        KLASSISCH = "klassisch", "Klassisch (PL/SL direkt)"
        FORMEN = "formen", "6 Forms of Loss"
        FAIR_MAM = "fair_mam", "FAIR-MAM-Fragebogen"

    class AggregationsModus(models.TextChoices):
        ELEMENTWEISE = "elementweise", "Elementweise (Monte-Carlo-Faltung)"
        KENNWERTE = "kennwerte", "Kennwerte (Momente addieren, Lognormal-Näherung)"

    name = models.CharField("Name", max_length=200)
    beschreibung = models.TextField("Beschreibung", blank=True)
    n_simulations = models.PositiveIntegerField("Anzahl Simulationen", default=10_000)
    random_seed = models.PositiveIntegerField("Zufalls-Seed", default=42)
    # Risikotoleranz, kontextbasiert: {"type": "constant"|"curve"|"distribution", ...}
    risikotoleranz = models.JSONField("Risikotoleranz", null=True, blank=True)
    # Steuert, ob PL/SL direkt eingegeben werden (wie bisher) oder aus VerlustFormEingabe
    # (6 Forms of Loss) aggregiert werden - siehe apps/berechnung/services.py::simuliere.
    lm_modus = models.CharField(
        "LM-Modus", max_length=20, choices=LMModus.choices, default=LMModus.KLASSISCH,
    )
    # Nur relevant, wenn lm_modus != "klassisch" - steuert, wie die Loss-Form-/FAIR-MAM-
    # Komponenten je Seite zu PL/SL zusammengefasst werden (siehe verlust_komponenten() vs.
    # verlust_kennwerte_kwargs() und apps/berechnung/services.py::simuliere).
    aggregations_modus = models.CharField(
        "Aggregationsmodus", max_length=20,
        choices=AggregationsModus.choices, default=AggregationsModus.ELEMENTWEISE,
    )
    erstellt_am = models.DateTimeField("Erstellt am", auto_now_add=True)
    geaendert_am = models.DateTimeField("Geändert am", auto_now=True)

    class Meta:
        verbose_name = "Szenario"
        verbose_name_plural = "Szenarien"
        ordering = ["-geaendert_am"]

    def __str__(self):
        return self.name

    def fair_inputs(self):
        """Eingaben als Dict ``{FAIR-Target: input_data-kwargs}``.

        Direkt an ``FairModel.input_data(target, **kwargs)`` übergebbar. Im
        LM-Modus "formen" fehlt PL/SL hier bewusst, falls dafür Loss-Form-
        Eingaben existieren - ``services.simuliere()`` füttert diese Seiten
        dann stattdessen aggregiert über ``model.input_raw_data(...)`` (eine
        ggf. noch vorhandene alte PL/SL-``FaktorEingabe`` wird hier daher
        übersprungen, damit dasselbe Ziel nicht doppelt gesetzt wird).
        """
        formen_seiten = self.formen_seiten()
        return {
            faktor.fair_target: faktor.to_fair_kwargs()
            for faktor in self.faktoren.all()
            if faktor.faktor not in formen_seiten
        }

    def formen_seiten(self):
        """Set der Seiten ("PL"/"SL"), die im aktuellen LM-Modus Verlust-Komponenten haben.

        Deckt beide Aufschlüsselungs-Taxonomien ab: "formen" (6 Forms of Loss,
        ``VerlustFormEingabe``) und "fair_mam" (FAIR-MAM-Kategorien, ``VerlustMamEingabe`` -
        Seite ergibt sich dort automatisch aus der Kategorie, siehe ``MAM_KATEGORIE_INFO``).
        """
        if self.lm_modus == self.LMModus.FORMEN:
            return set(self.verlustformen.values_list("seite", flat=True).distinct())
        if self.lm_modus == self.LMModus.FAIR_MAM:
            return {
                MAM_KATEGORIE_INFO[k]["seite"]
                for k in self.mam_kategorien.values_list("kategorie", flat=True)
            }
        return set()

    def verlust_komponenten(self, seite):
        """Aktive Verlust-Eingaben einer Seite ("PL"/"SL"), deterministisch sortiert.

        Taxonomie-unabhängig (liefert je nach ``lm_modus`` ``VerlustFormEingabe``- oder
        ``VerlustMamEingabe``-Objekte) - für die elementweise Aggregation in
        ``apps/berechnung/services.py::simuliere``.
        """
        if self.lm_modus == self.LMModus.FORMEN:
            return list(self.verlustformen.filter(seite=seite).order_by("form"))
        if self.lm_modus == self.LMModus.FAIR_MAM:
            return sorted(
                (k for k in self.mam_kategorien.all() if k.seite == seite),
                key=lambda k: k.kategorie,
            )
        return []

    def verlust_kennwerte_kwargs(self, seite):
        """"Kennwerte"-Aggregationsmodus (Slice 3): Momente (Mittelwert+Varianz) der aktiven
        Verlust-Komponenten einer Seite exakt aufsummieren (Unabhängigkeitsannahme - Momente
        addieren sich immer, unabhängig von der Verteilungsfamilie) und per Moment-Matching in
        eine einzelne Lognormalverteilung übersetzen. Näherung an die echte Faltung
        (``verlust_komponenten()``/elementweiser Modus): legt Mittelwert+Varianz exakt fest,
        aber nicht die tatsächliche Form/Schiefe der Summenverteilung.
        """
        komponenten = self.verlust_komponenten(seite)
        mittelwert = sum(k.momente()[0] for k in komponenten)
        varianz = sum(k.momente()[1] for k in komponenten)
        if mittelwert <= 0:  # Lognormal erfordert mean > 0 (pyfair) - degenerierter Fall
            return {"distribution": "constant", "params": {"constant": mittelwert}}
        sigma = math.sqrt(math.log(1 + varianz / mittelwert ** 2)) if varianz > 0 else 0.0
        return {"distribution": "lognormal", "params": {"mean": mittelwert, "sigma": sigma}}

    def schnitt_codes(self):
        """Die angegebenen Faktor-Codes (der Schnitt durch den FAIR-Baum).

        PL/SL gelten auch dann als abgedeckt, wenn sie im LM-Modus "formen"
        über Loss-Form-Eingaben statt einer eigenen ``FaktorEingabe`` kommen.
        """
        codes = list(self.faktoren.values_list("faktor", flat=True))
        for seite in self.formen_seiten():
            if seite not in codes:
                codes.append(seite)
        return codes

    def schnitt_ist_gueltig(self):
        """True, wenn die Faktoren einen rechenbaren Schnitt bilden (Risk abgedeckt)."""
        return fair_tree.schnitt_ist_gueltig(self.schnitt_codes())


class Vergleich(models.Model):
    """Benannte Gruppe bestehender Szenarien für einen gemeinsamen Lauf.

    Ein Vergleich referenziert mehrere ``Szenario``-Objekte (Gruppierung).
    Der Lauf (``berechnung.MetaLauf``) rechnet jedes Szenario einzeln (für
    die Compare-Überlagerung der LECs) und summiert sie (Add =
    Gesamtrisiko). Änderungen an einem Szenario wirken sich beim
    Neuberechnen aus (es wird referenziert, nicht eingefroren).
    """

    name = models.CharField("Name", max_length=200)
    beschreibung = models.TextField("Beschreibung", blank=True)
    szenarien = models.ManyToManyField(
        "Szenario", related_name="vergleiche", verbose_name="Szenarien"
    )
    # Dessen Risikotoleranz wird im Compare-Chart gezeichnet (Schnittpunkte je Szenario-LEC).
    referenz_szenario = models.ForeignKey(
        "Szenario",
        related_name="referenz_fuer",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Referenz-Szenario (Risikotoleranz)",
    )
    n_simulations = models.PositiveIntegerField("Anzahl Simulationen", default=10_000)
    random_seed = models.PositiveIntegerField("Zufalls-Seed", default=42)
    erstellt_am = models.DateTimeField("Erstellt am", auto_now_add=True)
    geaendert_am = models.DateTimeField("Geändert am", auto_now=True)

    class Meta:
        verbose_name = "Vergleich"
        verbose_name_plural = "Vergleiche"
        ordering = ["-geaendert_am"]

    def __str__(self):
        return self.name

    @property
    def letzter_lauf(self):
        """Jüngster zugehöriger Meta-Lauf (oder None)."""
        return self.laeufe.order_by("-erstellt_am").first()


class Cluster(models.Model):
    """Organisatorische Gruppe (Ordner/Kategorie) für Szenarien.

    Rein zur Übersicht/Strukturierung – keine eigene Berechnung. Ein Szenario
    kann zu mehreren Clustern gehören.
    """

    name = models.CharField("Name", max_length=200)
    beschreibung = models.TextField("Beschreibung", blank=True)
    szenarien = models.ManyToManyField(
        "Szenario", related_name="cluster", blank=True, verbose_name="Szenarien"
    )
    erstellt_am = models.DateTimeField("Erstellt am", auto_now_add=True)
    geaendert_am = models.DateTimeField("Geändert am", auto_now=True)

    class Meta:
        verbose_name = "Cluster"
        verbose_name_plural = "Cluster"
        ordering = ["name"]

    def __str__(self):
        return self.name


class _VerteilungsEingabe(models.Model):
    """Abstrakte Basis: eine Verteilungs-Eingabe (Verteilung + Parameter + Unsicherheit
    + Annahmen/Quelle). Gemeinsame Felder/Methoden für ``FaktorEingabe`` (FAIR-Baumknoten)
    und ``VerlustFormEingabe`` (Loss-Form auf der PL/SL-Seite) - beide werden identisch
    validiert und identisch in pyfair-``input_data``-kwargs übersetzt.
    """

    class Verteilung(models.TextChoices):
        PERT = "pert", "PERT (min / wahrscheinlich / max)"
        NORMAL = "normal", "Normalverteilung (Mittelwert / Streuung)"
        CONSTANT = "constant", "Konstant (fester Wert)"
        POISSON = "poisson", "Poisson (λ Ereignisse pro Jahr)"
        BETA = "beta", "Beta (Mittelwert 0–1)"
        LOGNORMAL = "lognormal", "Lognormal (Mittelwert)"

    # Pflicht-Parameter je Verteilung (pyfair-Keys; Formparameter wie gamma/
    # sigma/k/range liefert der Unsicherheits-Slider via confidence).
    REQUIRED_PARAMS = {
        Verteilung.PERT: ("low", "mode", "high"),
        Verteilung.NORMAL: ("mean", "stdev"),
        Verteilung.CONSTANT: ("constant",),
        Verteilung.POISSON: ("lambda",),
        Verteilung.LOGNORMAL: ("mean",),
        # Beta wird separat validiert (zwei Eingabearten, siehe _validiere_verteilung()).
    }

    verteilung = models.CharField(
        "Verteilung",
        max_length=20,
        choices=Verteilung.choices,
        default=Verteilung.PERT,
    )
    params = models.JSONField("Parameter", default=dict)
    # Unsicherheit als 5-Stufen-Slider (0 = niedrigste ... 4 = höchste).
    # Wird invertiert auf pyfair-"confidence" abgebildet (siehe fair_confidence).
    unsicherheit = models.PositiveSmallIntegerField(
        "Unsicherheit",
        default=UNSICHERHEIT_DEFAULT,
        validators=[MinValueValidator(UNSICHERHEIT_MIN), MaxValueValidator(UNSICHERHEIT_MAX)],
    )
    annahmen = models.TextField("Annahmen", blank=True)
    quellentext = models.TextField("Quellentext", blank=True)

    class Meta:
        abstract = True

    @property
    def confidence_level(self):
        """pyfair-Konfidenzstufe (invertiert zur Unsicherheit)."""
        return UNSICHERHEIT_TO_CONFIDENCE[self.unsicherheit]

    @property
    def unsicherheit_label(self):
        """Lesbares Label der Unsicherheitsstufe (z. B. 'mittel')."""
        return UNSICHERHEIT_LABELS[self.unsicherheit]

    @property
    def confidence_shape(self):
        """Aufgelöster pyfair-Formparameter (z. B. {'gamma': 4}) oder None."""
        if self.verteilung not in CONFIDENCE_DISTRIBUTIONS:
            return None
        return aktuelle_konfidenz_defaults().get(self.confidence_level, {}).get(self.verteilung)

    def to_fair_kwargs(self):
        """kwargs für die strukturierte pyfair-API ``input_data``/``FairDataInput.generate``.

        Für Verteilungen mit Konfidenz-Formparameter (PERT/Lognormal/
        Poisson/Beta) wird ``confidence`` mitgegeben – pyfair leitet daraus
        gamma/sigma/k/range ab. Konstant/Normal kennen keine Konfidenz.
        """
        params = dict(self.params)
        # Beta: zwei explizite Eingabearten, keine confidence aus dem Slider.
        if self.verteilung == self.Verteilung.BETA:
            if "low" in params:  # Konfidenzintervall (low/high/confidence)
                return {"distribution": "beta", "input_mode": "confidence_interval", "params": params}
            return {"distribution": "beta", "params": params}  # Mittelwert + k
        kwargs = {"distribution": self.verteilung, "params": params}
        if self.verteilung in CONFIDENCE_DISTRIBUTIONS:
            # Expliziter Formparameter aus der (editierbaren) Konfidenztabelle –
            # pyfair nutzt ihn direkt (kein "confidence" mehr nötig).
            shape = aktuelle_konfidenz_defaults().get(self.confidence_level, {}).get(self.verteilung)
            if shape:
                params.update(shape)
        return kwargs

    def momente(self):
        """(Mittelwert, Varianz) dieser Verteilung - für den "Kennwerte"-Aggregationsmodus
        (Slice 3, ``Szenario.verlust_kennwerte_kwargs()``), ohne Sampling. Nur für die bei
        Loss-Formen/FAIR-MAM erlaubten Verteilungen definiert (pert/normal/constant/lognormal,
        siehe ``fair_tree.DISTS_BY_TYP["magnitude"]``).

        PERT-Momente werden über pyfairs eigene ``FairBetaPert`` berechnet statt über die
        Lehrbuch-PERT-Varianzformel - pyfairs interne Ableitung weicht davon ab (nachgerechnet:
        low=1000/mode=3000/high=8000/gamma=4 ergibt Lehrbuchformel ≈1.607.143, pyfairs tatsächliche
        Beta-Kurve ≈1.361.111) und nur so bleibt dies konsistent mit dem, was tatsächlich gesampelt wird.
        """
        kwargs = self.to_fair_kwargs()
        dist, p = kwargs["distribution"], kwargs["params"]
        if dist == self.Verteilung.CONSTANT:
            return float(p["constant"]), 0.0
        if dist == self.Verteilung.NORMAL:
            return float(p["mean"]), float(p["stdev"]) ** 2
        if dist == self.Verteilung.LOGNORMAL:
            mean = float(p["mean"])
            return mean, (math.exp(float(p["sigma"]) ** 2) - 1) * mean ** 2
        if dist == self.Verteilung.PERT:
            from pyfair.utility.beta_pert import FairBetaPert

            pert = FairBetaPert(low=p["low"], mode=p["mode"], high=p["high"], gamma=p.get("gamma", 4))
            return float(pert._beta_curve.mean()), float(pert._beta_curve.var())
        raise ValueError(f"Momente für Verteilung '{dist}' nicht definiert.")

    def _validiere_verteilung(self):
        """Prüft, dass ``params`` zur gewählten Verteilung passt. Wirft ``ValidationError``."""
        params = self.params or {}
        required = self.REQUIRED_PARAMS.get(self.verteilung, ())
        fehlend = [key for key in required if key not in params]
        if fehlend:
            raise ValidationError(
                f"Verteilung „{self.verteilung}“ benötigt: {', '.join(fehlend)}."
            )

        if self.verteilung == self.Verteilung.PERT:
            low, mode, high = params["low"], params["mode"], params["high"]
            if not (low <= mode <= high):
                raise ValidationError(
                    "PERT erfordert die Reihenfolge low ≤ mode ≤ high."
                )

        if self.verteilung == self.Verteilung.BETA:
            if "low" in params:  # Konfidenzintervall
                fehlend = [k for k in ("low", "high", "confidence") if k not in params]
                if fehlend:
                    raise ValidationError(f"Beta-Konfidenzintervall benötigt: {', '.join(fehlend)}.")
                if not (params["low"] < params["high"]):
                    raise ValidationError("Beta-Konfidenzintervall: low muss kleiner als high sein.")
            else:  # Mittelwert + k
                fehlend = [k for k in ("mean", "k") if k not in params]
                if fehlend:
                    raise ValidationError(f"Beta benötigt: {', '.join(fehlend)}.")


class FaktorEingabe(_VerteilungsEingabe):
    """Eine Verteilungs-Eingabe für genau einen FAIR-Faktor eines Szenarios."""

    class Faktor(models.TextChoices):
        LEF = "LEF", "Loss Event Frequency (LEF)"
        TEF = "TEF", "Threat Event Frequency (TEF)"
        CF = "CF", "Contact Frequency (CF)"
        POA = "POA", "Probability of Action (PoA)"
        VULN = "VULN", "Vulnerability (Vuln)"
        TC = "TC", "Threat Capability (TC)"
        CS = "CS", "Control Strength (CS)"
        LM = "LM", "Loss Magnitude (LM)"
        PL = "PL", "Primary Loss (PL)"
        SL = "SL", "Secondary Loss (SL)"
        SLEF = "SLEF", "Secondary Loss Event Frequency (SLEF)"
        SLEM = "SLEM", "Secondary Loss Event Magnitude (SLEM)"

    szenario = models.ForeignKey(
        Szenario,
        related_name="faktoren",
        on_delete=models.CASCADE,
        verbose_name="Szenario",
    )
    faktor = models.CharField("Faktor", max_length=10, choices=Faktor.choices)
    angreifertyp = models.CharField("Angreifertyp", max_length=120, blank=True)

    class Meta:
        verbose_name = "Faktor-Eingabe"
        verbose_name_plural = "Faktor-Eingaben"
        constraints = [
            models.UniqueConstraint(
                fields=["szenario", "faktor"],
                name="unique_faktor_pro_szenario",
            )
        ]

    def __str__(self):
        return f"{self.get_faktor_display()} – {self.get_verteilung_display()}"

    @property
    def fair_target(self):
        """Der pyfair-Knotenname für diesen Faktor (z. B. 'Loss Magnitude')."""
        return fair_tree.target(self.faktor)

    @property
    def faktor_abbr(self):
        return fair_tree.abbr(self.faktor)

    def clean(self):
        self._validiere_verteilung()
        # Wahrscheinlichkeits-Faktoren müssen in [0, 1] liegen ("k" ist davon ausgenommen).
        if self.faktor and fair_tree.ist_gebunden(self.faktor):
            for key, value in (self.params or {}).items():
                if key == "k":
                    continue
                if isinstance(value, (int, float)) and not (0.0 <= value <= 1.0):
                    raise ValidationError(
                        f"„{fair_tree.abbr(self.faktor)}“ ist eine Wahrscheinlichkeit – "
                        f"Werte müssen zwischen 0 und 1 liegen (war {key}={value})."
                    )


# Kurz-Erklärungen je Loss-Form (Open-FAIR "Six Forms of Loss"), für den Info-Knopf
# im Eingabeformular - eigene, knappe Formulierung, keine Übernahme von Standardtexten.
VERLUSTFORM_ERKLAERUNG = {
    "productivity": "Wert verlorener Produktivität, weil ein Asset (System, Mitarbeitende, "
                    "Prozess) durch das Ereignis für die normale Arbeit nicht zur Verfügung steht.",
    "response": "Kosten, das Ereignis selbst zu bewältigen – z. B. forensische Untersuchung, "
                "Incident-Response-Team, interne und externe Kommunikation.",
    "replacement": "Kosten, durch das Ereignis zerstörte oder unbrauchbar gewordene "
                   "Vermögenswerte zu ersetzen oder wiederherzustellen – z. B. Hardware, Daten, Systeme.",
    "competitive_advantage": "Wert eines verlorenen Wettbewerbsvorteils – z. B. wenn gestohlene "
                             "Geschäftsgeheimnisse oder geistiges Eigentum einem Konkurrenten nutzen.",
    "fines_judgements": "Bußgelder, Vertragsstrafen oder Schadensersatz aus rechtlichen bzw. "
                        "regulatorischen Verfahren infolge des Ereignisses.",
    "reputation": "Wert entgangener künftiger Erträge durch Vertrauens-/Reputationsschaden – "
                  "z. B. Kundenabwanderung, sinkender Markenwert, erschwerte Neukundengewinnung.",
}


class VerlustFormEingabe(_VerteilungsEingabe):
    """Eine Loss-Form (6 Forms of Loss) auf der Primary- oder Secondary-Loss-Seite.

    Mehrere Formen je Seite werden in ``apps/berechnung/services.py::simuliere`` pro
    Trial elementweise aufsummiert (statt Kennwerte zu addieren) und über
    ``FairModel.input_raw_data("Primary Loss"/"Secondary Loss", ...)`` eingespeist -
    siehe ``Szenario.lm_modus``.
    """

    class Seite(models.TextChoices):
        PL = "PL", "Primary Loss"
        SL = "SL", "Secondary Loss"

    class Form(models.TextChoices):
        PRODUCTIVITY = "productivity", "Productivity"
        RESPONSE = "response", "Response"
        REPLACEMENT = "replacement", "Replacement"
        COMPETITIVE_ADVANTAGE = "competitive_advantage", "Competitive Advantage"
        FINES_JUDGEMENTS = "fines_judgements", "Fines & Judgements"
        REPUTATION = "reputation", "Reputation"

    szenario = models.ForeignKey(
        Szenario,
        related_name="verlustformen",
        on_delete=models.CASCADE,
        verbose_name="Szenario",
    )
    seite = models.CharField("Seite", max_length=2, choices=Seite.choices)
    form = models.CharField("Loss-Form", max_length=30, choices=Form.choices)

    class Meta:
        verbose_name = "Verlust-Form-Eingabe"
        verbose_name_plural = "Verlust-Form-Eingaben"
        constraints = [
            models.UniqueConstraint(
                fields=["szenario", "seite", "form"],
                name="unique_form_pro_seite_und_szenario",
            )
        ]
        ordering = ["seite", "form"]

    def __str__(self):
        return f"{self.get_seite_display()} – {self.get_form_display()}"

    @property
    def erklaerung(self):
        """Kurzerklärung dieser Loss-Form (für den Info-Knopf im Formular)."""
        return VERLUSTFORM_ERKLAERUNG.get(self.form, "")

    @property
    def eindeutiger_code(self):
        """Eindeutiger Bezeichner für die Sampling-Zielbenennung in ``services.simuliere``."""
        return f"{self.seite}-{self.form}"

    def clean(self):
        # Loss-Formen sind immer Geldbeträge - keine [0,1]-Bindung wie bei FAIR-Faktoren.
        self._validiere_verteilung()


# FAIR-MAM (FAIR Materiality Assessment Model, FAIR Institute 2023): 10 Kostenmodule mit
# 26 Sub-Kategorien, feinere Aufschlüsselung von Loss Magnitude als die 6 Forms of Loss.
# Primary/Secondary-Zuordnung (-> Seite PL/SL) exakt nach der FAIR-MAM-Übersichtstabelle;
# Modul- und Kategorienamen sind die Taxonomie-Bezeichner des Standards (Eigennamen, zulässig
# laut FAIR-MAM-FAQ für eigene Implementierungen). Erklärungstexte sind eigene, knappe
# Formulierungen - keine Übernahme von Beschreibungstexten aus dem (privat, nicht committeten)
# Quell-PDF (CC BY-NC-ND, siehe pyfair-cam/knowledge-base-notes/fair_mam.md).
MAM_MODULE = [
    "Information Privacy",
    "Proprietary Data Loss",
    "Business Interruption",
    "Cyber Extortion",
    "Network Security",
    "Financial Fraud",
    "Media Content",
    "Hardware Bricking",
    "Post Breach Security Improvements",
    "Reputational Damage",
]

MAM_KATEGORIE_INFO = {
    "sensitive_pii_response": {
        "modul": "Information Privacy", "seite": "PL", "typ": "Response",
        "erklaerung": "Kosten der Reaktion auf ein Ereignis mit sensiblen personenbezogenen "
                      "Daten – z. B. forensische Aufklärung, Betroffenen-Benachrichtigung.",
    },
    "pci_dss_liability": {
        "modul": "Information Privacy", "seite": "PL", "typ": "Response",
        "erklaerung": "Kosten aus der Verpflichtung, bei einem Zahlungskarten-Vorfall die "
                      "PCI-DSS-Vorgaben der Kartennetzwerke einzuhalten (Prüfungen, Strafen).",
    },
    "information_privacy_liability": {
        "modul": "Information Privacy", "seite": "SL", "typ": "Response",
        "erklaerung": "Haftungskosten Dritter (Klagen, Vergleiche) wegen kompromittierter "
                      "personenbezogener Daten.",
    },
    "regulatory_liability": {
        "modul": "Information Privacy", "seite": "SL", "typ": "Fines & Judgements",
        "erklaerung": "Bußgelder oder Sanktionen von Aufsichtsbehörden infolge eines "
                      "Datenschutzvorfalls.",
    },
    "future_net_revenue_loss": {
        "modul": "Proprietary Data Loss", "seite": "SL", "typ": "Competitive Advantage",
        "erklaerung": "Entgangene künftige Nettoerträge, weil gestohlene Geschäftsgeheimnisse "
                      "oder geistiges Eigentum den Wettbewerbsvorteil mindern.",
    },
    "proprietary_data_loss_liability": {
        "modul": "Proprietary Data Loss", "seite": "SL", "typ": "Response",
        "erklaerung": "Haftungskosten Dritter (z. B. Vertragspartner) wegen verlorener "
                      "nicht-personenbezogener Daten (Geschäftsgeheimnisse, Kundendaten).",
    },
    "direct_business_interruption": {
        "modul": "Business Interruption", "seite": "PL", "typ": "Productivity",
        "erklaerung": "Direkter Ertrags- oder Produktivitätsverlust durch die eigene "
                      "Betriebsunterbrechung während des Ereignisses.",
    },
    "contingent_business_interruption": {
        "modul": "Business Interruption", "seite": "PL", "typ": "Productivity",
        "erklaerung": "Ertrags- oder Produktivitätsverlust, weil ein Dienstleister (z. B. "
                      "IT-Provider in der Lieferkette) infolge des Ereignisses ausfällt.",
    },
    "business_interruption_liability": {
        "modul": "Business Interruption", "seite": "SL", "typ": "Response",
        "erklaerung": "Haftungskosten Dritter, die durch die eigene Betriebsunterbrechung "
                      "selbst geschädigt wurden (z. B. Kunden in der Lieferkette).",
    },
    "ransom": {
        "modul": "Cyber Extortion", "seite": "PL", "typ": "Response",
        "erklaerung": "Kosten eines gezahlten (oder für eine mögliche Zahlung vorgehaltenen) "
                      "Lösegelds bei einem Erpressungsangriff.",
    },
    "network_event_response": {
        "modul": "Network Security", "seite": "PL", "typ": "Response",
        "erklaerung": "Forensik- und Rechtskosten der Untersuchung, Meldung und "
                      "Wiederherstellung eines Netzwerk-/Systemvorfalls.",
    },
    "network_security_liability": {
        "modul": "Network Security", "seite": "SL", "typ": "Response",
        "erklaerung": "Haftungskosten, wenn von den eigenen Systemen ein Angriff auf Dritte "
                      "ausging (z. B. Lieferketten-Vorfall auf Verursacherseite).",
    },
    "bec_fraud": {
        "modul": "Financial Fraud", "seite": "PL", "typ": "Replacement",
        "erklaerung": "Finanzieller Schaden durch Business-E-Mail-Compromise – Betrüger "
                      "geben sich per E-Mail als vertrauenswürdige Partei aus.",
    },
    "funds_transfer_fraud": {
        "modul": "Financial Fraud", "seite": "PL", "typ": "Replacement",
        "erklaerung": "Direkter Verlust gestohlener Gelder oder anderer Zahlungsmittel durch "
                      "betrügerische Überweisungen.",
    },
    "media_event_response": {
        "modul": "Media Content", "seite": "PL", "typ": "Response",
        "erklaerung": "Kosten der Reaktion auf einen Vorfall mit Medien- oder "
                      "Werbeinhalten (z. B. missbräuchlich genutzte Marken/Logos).",
    },
    "media_liability": {
        "modul": "Media Content", "seite": "SL", "typ": "Response",
        "erklaerung": "Haftungskosten Dritter wegen unrechtmäßiger Nutzung von Medien- oder "
                      "Werbeinhalten, die das Unternehmen identifizieren.",
    },
    "server_replacement": {
        "modul": "Hardware Bricking", "seite": "PL", "typ": "Replacement",
        "erklaerung": "Kosten für den Ersatz von Servern, die durch einen zerstörerischen "
                      "Angriff (z. B. Wiper-Malware) unbrauchbar wurden.",
    },
    "computer_replacement": {
        "modul": "Hardware Bricking", "seite": "PL", "typ": "Replacement",
        "erklaerung": "Kosten für den Ersatz von Computern/Laptops, die durch einen "
                      "zerstörerischen Angriff unbrauchbar wurden.",
    },
    "legally_mandated_improvements": {
        "modul": "Post Breach Security Improvements", "seite": "SL", "typ": "Response",
        "erklaerung": "Kosten für Sicherheitsverbesserungen, die nach dem Vorfall von einer "
                      "Behörde oder einem Gericht verpflichtend vorgegeben werden.",
    },
    "voluntary_improvements": {
        "modul": "Post Breach Security Improvements", "seite": "SL", "typ": "Response",
        "erklaerung": "Kosten für Sicherheitsverbesserungen, die das Unternehmen nach dem "
                      "Vorfall freiwillig (ohne Vorgabe) umsetzt.",
    },
    "customer_retention": {
        "modul": "Reputational Damage", "seite": "SL", "typ": "Reputation",
        "erklaerung": "Mehrkosten oder Ertragsverlust, um Kunden nach dem Vorfall zu halten "
                      "(z. B. Rabatte, zusätzliche Kundenbindungsmaßnahmen).",
    },
    "future_projects": {
        "modul": "Reputational Damage", "seite": "SL", "typ": "Reputation",
        "erklaerung": "Entgangener Wert künftiger Geschäftschancen, die wegen des "
                      "Reputationsschadens nicht zustande kommen.",
    },
    "market_value": {
        "modul": "Reputational Damage", "seite": "SL", "typ": "Reputation",
        "erklaerung": "Rückgang des Unternehmens-/Marktwerts infolge des öffentlich "
                      "gewordenen Vorfalls.",
    },
    "cyber_insurance": {
        "modul": "Reputational Damage", "seite": "SL", "typ": "Reputation",
        "erklaerung": "Mehrkosten künftiger Cyber-Versicherungsprämien infolge des Vorfalls "
                      "(höheres Risiko, schlechtere Konditionen).",
    },
    "cost_of_capital": {
        "modul": "Reputational Damage", "seite": "SL", "typ": "Reputation",
        "erklaerung": "Höhere Finanzierungskosten (z. B. schlechteres Rating), weil "
                      "Kapitalgeber den Vorfall als erhöhtes Risiko einpreisen.",
    },
    "employee_churn": {
        "modul": "Reputational Damage", "seite": "SL", "typ": "Reputation",
        "erklaerung": "Mehrkosten durch erhöhte Mitarbeiterfluktuation und erschwerte "
                      "Neueinstellung infolge des Reputationsschadens.",
    },
}


class VerlustMamEingabe(_VerteilungsEingabe):
    """Eine FAIR-MAM-Kostenkategorie auf der Primary- oder Secondary-Loss-Seite.

    Zweite Taxonomie neben ``VerlustFormEingabe`` (6 Forms of Loss) für die LM-Aufschlüsselung -
    feinere Kategorien (FAIR Materiality Assessment Model, FAIR Institute), Primary/Secondary
    fest je Kategorie vorgegeben (siehe ``MAM_KATEGORIE_INFO``), daher kein eigenes ``seite``-
    Feld nötig. Aggregation identisch zu ``VerlustFormEingabe`` (siehe
    ``Szenario.verlust_komponenten()`` und ``apps/berechnung/services.py::simuliere``).
    """

    class Kategorie(models.TextChoices):
        SENSITIVE_PII_RESPONSE = "sensitive_pii_response", "Sensitive PII Event Response and Management"
        PCI_DSS_LIABILITY = "pci_dss_liability", "PCI-DSS Liability"
        INFORMATION_PRIVACY_LIABILITY = "information_privacy_liability", "Information Privacy Liability"
        REGULATORY_LIABILITY = "regulatory_liability", "Regulatory Liability"
        FUTURE_NET_REVENUE_LOSS = "future_net_revenue_loss", "Loss of Estimated Future Net Revenue"
        PROPRIETARY_DATA_LOSS_LIABILITY = "proprietary_data_loss_liability", "Proprietary Data Loss Liability"
        DIRECT_BUSINESS_INTERRUPTION = "direct_business_interruption", "Direct Business Interruption"
        CONTINGENT_BUSINESS_INTERRUPTION = "contingent_business_interruption", "Contingent Business Interruption"
        BUSINESS_INTERRUPTION_LIABILITY = "business_interruption_liability", "Business Interruption Liability"
        RANSOM = "ransom", "Ransom"
        NETWORK_EVENT_RESPONSE = "network_event_response", "Network Event Response and Recovery"
        NETWORK_SECURITY_LIABILITY = "network_security_liability", "Network Security Liability"
        BEC_FRAUD = "bec_fraud", "Business Email Compromise (BEC)"
        FUNDS_TRANSFER_FRAUD = "funds_transfer_fraud", "Funds Transfer Fraud"
        MEDIA_EVENT_RESPONSE = "media_event_response", "Media Event Response"
        MEDIA_LIABILITY = "media_liability", "Media Liability"
        SERVER_REPLACEMENT = "server_replacement", "Server Replacement"
        COMPUTER_REPLACEMENT = "computer_replacement", "Computer/Laptop Replacement"
        LEGALLY_MANDATED_IMPROVEMENTS = "legally_mandated_improvements", "Legally-Mandated Improvements"
        VOLUNTARY_IMPROVEMENTS = "voluntary_improvements", "Voluntary Improvements"
        CUSTOMER_RETENTION = "customer_retention", "Customer Retention"
        FUTURE_PROJECTS = "future_projects", "Future Projects"
        MARKET_VALUE = "market_value", "Market Value"
        CYBER_INSURANCE = "cyber_insurance", "Cyber Insurance"
        COST_OF_CAPITAL = "cost_of_capital", "Cost of Capital"
        EMPLOYEE_CHURN = "employee_churn", "Employee Churn"

    szenario = models.ForeignKey(
        Szenario,
        related_name="mam_kategorien",
        on_delete=models.CASCADE,
        verbose_name="Szenario",
    )
    kategorie = models.CharField("Kostenkategorie", max_length=40, choices=Kategorie.choices)

    class Meta:
        verbose_name = "FAIR-MAM-Eingabe"
        verbose_name_plural = "FAIR-MAM-Eingaben"
        constraints = [
            models.UniqueConstraint(
                fields=["szenario", "kategorie"],
                name="unique_kategorie_pro_szenario",
            )
        ]
        ordering = ["kategorie"]

    def __str__(self):
        return self.get_kategorie_display()

    @property
    def modul(self):
        return MAM_KATEGORIE_INFO[self.kategorie]["modul"]

    @property
    def seite(self):
        return MAM_KATEGORIE_INFO[self.kategorie]["seite"]

    @property
    def typ(self):
        return MAM_KATEGORIE_INFO[self.kategorie]["typ"]

    @property
    def erklaerung(self):
        return MAM_KATEGORIE_INFO[self.kategorie]["erklaerung"]

    @property
    def eindeutiger_code(self):
        """Eindeutiger Bezeichner für die Sampling-Zielbenennung in ``services.simuliere``."""
        return f"mam-{self.kategorie}"

    def clean(self):
        # FAIR-MAM-Kategorien sind immer Geldbeträge - keine [0,1]-Bindung wie bei FAIR-Faktoren.
        self._validiere_verteilung()
