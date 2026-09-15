"""Datenmodell für FAIR-Szenarien.

Ein ``Szenario`` bündelt die Metadaten einer Monte-Carlo-Simulation
(Name, Simulationsanzahl, Seed) und besitzt pro FAIR-Risikofaktor eine
``FaktorEingabe`` mit frei wählbarer Verteilung. Aus den Eingaben lässt
sich direkt ein pyfair-``FairModel`` füttern (Phase 4).
"""

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
        """Set der Seiten ("PL"/"SL"), die im LM-Modus "formen" Loss-Form-Eingaben haben."""
        if self.lm_modus != self.LMModus.FORMEN:
            return set()
        return set(self.verlustformen.values_list("seite", flat=True).distinct())

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

    def clean(self):
        # Loss-Formen sind immer Geldbeträge - keine [0,1]-Bindung wie bei FAIR-Faktoren.
        self._validiere_verteilung()
