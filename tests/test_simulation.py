"""Tests für die Monte-Carlo-Engine + Runner (Phase 4, Variante A)."""

import pytest

from apps.berechnung import services
from apps.berechnung.models import Simulationslauf
from apps.szenarien.models import FaktorEingabe, Szenario, VerlustFormEingabe, VerlustMamEingabe


def _szenario_mit_faktoren():
    s = Szenario.objects.create(name="Sim-Test", n_simulations=200)
    FaktorEingabe.objects.create(
        szenario=s, faktor="LEF", verteilung="pert",
        params={"low": 1, "mode": 3, "high": 6},
    )
    FaktorEingabe.objects.create(
        szenario=s, faktor="LM", verteilung="constant", params={"constant": 4000},
    )
    return s


@pytest.mark.django_db
def test_simuliere_liefert_kennzahlen_und_lec():
    pytest.importorskip("pyfair")
    s = _szenario_mit_faktoren()

    fortschritte = []
    ergebnis = services.simuliere(
        s, n_simulations=200, random_seed=42, batches=4,
        fortschritt=fortschritte.append,
    )

    assert ergebnis["n"] == 200
    for key in ("mittelwert", "median", "min", "max", "p90", "p95", "p99", "lec"):
        assert key in ergebnis
    assert ergebnis["min"] <= ergebnis["median"] <= ergebnis["max"]
    assert ergebnis["p90"] <= ergebnis["p99"]
    # LEC ist eine fallende Überschreitungskurve.
    assert len(ergebnis["lec"]) > 0
    assert ergebnis["lec"][0]["ueberschreitung"] >= ergebnis["lec"][-1]["ueberschreitung"]
    # Fortschritt endet bei 100.
    assert fortschritte[-1] == 100


@pytest.mark.django_db
def test_ergebnis_enthaelt_knoten_mit_status():
    pytest.importorskip("pyfair")
    s = _szenario_mit_faktoren()  # LEF (pert) + LM (constant) -> Eingaben
    ergebnis = services.simuliere(s, n_simulations=200, random_seed=42, batches=2)

    knoten = ergebnis["knoten"]
    assert knoten["LEF"]["status"] == "eingabe"
    assert knoten["LM"]["status"] == "eingabe"
    assert knoten["Risk"]["status"] == "berechnet"
    # Nicht genutzte Knoten (z. B. TEF) tauchen nicht auf.
    assert "TEF" not in knoten


@pytest.mark.django_db
def test_run_simulation_setzt_lauf_auf_fertig():
    pytest.importorskip("pyfair")
    s = _szenario_mit_faktoren()
    lauf = Simulationslauf.objects.create(szenario=s, n_simulations=200, random_seed=42)

    services._run_simulation(lauf.pk)  # synchron, ohne Thread

    lauf.refresh_from_db()
    assert lauf.status == Simulationslauf.Status.FERTIG
    assert lauf.fortschritt == 100
    assert lauf.ergebnis["n"] == 200


@pytest.mark.django_db
def test_simuliere_aggregiert_loss_formen_elementweise():
    """lm_modus='formen': PL wird aus den einzelnen Loss-Form-Verteilungen summiert."""
    pytest.importorskip("pyfair")
    s = Szenario.objects.create(
        name="Formen-Test", n_simulations=200, lm_modus=Szenario.LMModus.FORMEN,
    )
    FaktorEingabe.objects.create(
        szenario=s, faktor="LEF", verteilung="pert",
        params={"low": 1, "mode": 3, "high": 6},
    )
    FaktorEingabe.objects.create(
        szenario=s, faktor="SL", verteilung="constant", params={"constant": 0},
    )
    VerlustFormEingabe.objects.create(
        szenario=s, seite="PL", form="response", verteilung="constant", params={"constant": 2000},
    )
    VerlustFormEingabe.objects.create(
        szenario=s, seite="PL", form="replacement", verteilung="constant", params={"constant": 3000},
    )

    ergebnis = services.simuliere(s, n_simulations=200, random_seed=42, batches=4)

    # Beide Loss-Formen sind konstant (2000 + 3000) -> PL muss in jedem Trial exakt 5000 sein,
    # wenn die Aggregation tatsächlich elementweise summiert statt nur eine Form zu übernehmen.
    pl = ergebnis["knoten"]["PL"]
    assert pl["mittelwert"] == pytest.approx(5000)
    assert pl["stdev"] == pytest.approx(0, abs=1e-6)


@pytest.mark.django_db
def test_simuliere_aggregiert_fair_mam_elementweise():
    """lm_modus='fair_mam': PL wird aus den einzelnen FAIR-MAM-Kategorien summiert."""
    pytest.importorskip("pyfair")
    s = Szenario.objects.create(
        name="MAM-Test", n_simulations=200, lm_modus=Szenario.LMModus.FAIR_MAM,
    )
    FaktorEingabe.objects.create(
        szenario=s, faktor="LEF", verteilung="pert",
        params={"low": 1, "mode": 3, "high": 6},
    )
    FaktorEingabe.objects.create(
        szenario=s, faktor="SL", verteilung="constant", params={"constant": 0},
    )
    # "ransom" und "server_replacement" sind beide Primary (-> PL) in MAM_KATEGORIE_INFO.
    VerlustMamEingabe.objects.create(
        szenario=s, kategorie="ransom", verteilung="constant", params={"constant": 2000},
    )
    VerlustMamEingabe.objects.create(
        szenario=s, kategorie="server_replacement", verteilung="constant", params={"constant": 3000},
    )

    ergebnis = services.simuliere(s, n_simulations=200, random_seed=42, batches=4)

    pl = ergebnis["knoten"]["PL"]
    assert pl["mittelwert"] == pytest.approx(5000)
    assert pl["stdev"] == pytest.approx(0, abs=1e-6)


@pytest.mark.django_db
def test_simuliere_aggregiert_kennwerte_bei_varianz_null_deterministisch():
    """aggregations_modus='kennwerte' mit zwei konstanten Formen (Varianz 0) muss wie im
    elementweisen Modus exakt auf die Summe kollabieren (Lognormal mit sigma=0 degeneriert
    auf einen festen Wert)."""
    pytest.importorskip("pyfair")
    s = Szenario.objects.create(
        name="Kennwerte-Test", n_simulations=200, lm_modus=Szenario.LMModus.FORMEN,
        aggregations_modus=Szenario.AggregationsModus.KENNWERTE,
    )
    FaktorEingabe.objects.create(
        szenario=s, faktor="LEF", verteilung="pert",
        params={"low": 1, "mode": 3, "high": 6},
    )
    FaktorEingabe.objects.create(
        szenario=s, faktor="SL", verteilung="constant", params={"constant": 0},
    )
    VerlustFormEingabe.objects.create(
        szenario=s, seite="PL", form="response", verteilung="constant", params={"constant": 2000},
    )
    VerlustFormEingabe.objects.create(
        szenario=s, seite="PL", form="replacement", verteilung="constant", params={"constant": 3000},
    )

    ergebnis = services.simuliere(s, n_simulations=200, random_seed=42, batches=4)

    pl = ergebnis["knoten"]["PL"]
    assert pl["mittelwert"] == pytest.approx(5000)
    assert pl["stdev"] == pytest.approx(0, abs=1e-6)


@pytest.mark.django_db
def test_simuliere_elementweise_und_kennwerte_liefern_gleichen_mittelwert():
    """Beide Aggregationsmodi müssen denselben PL-Mittelwert liefern (Momente addieren sich
    immer exakt, unabhängig vom Modus) - nur Varianz/Form der Summe dürfen abweichen."""
    pytest.importorskip("pyfair")

    def _szenario(modus):
        s = Szenario.objects.create(
            name=f"Vergleich-{modus}", n_simulations=4000, lm_modus=Szenario.LMModus.FORMEN,
            aggregations_modus=modus,
        )
        FaktorEingabe.objects.create(
            szenario=s, faktor="LEF", verteilung="pert",
            params={"low": 1, "mode": 3, "high": 6},
        )
        FaktorEingabe.objects.create(
            szenario=s, faktor="SL", verteilung="constant", params={"constant": 0},
        )
        VerlustFormEingabe.objects.create(
            szenario=s, seite="PL", form="response", verteilung="pert",
            params={"low": 1000, "mode": 2000, "high": 4000},
        )
        VerlustFormEingabe.objects.create(
            szenario=s, seite="PL", form="replacement", verteilung="normal",
            params={"mean": 3000, "stdev": 300},
        )
        return s

    s_element = _szenario(Szenario.AggregationsModus.ELEMENTWEISE)
    s_kennwerte = _szenario(Szenario.AggregationsModus.KENNWERTE)

    erg_element = services.simuliere(s_element, n_simulations=4000, random_seed=42, batches=8)
    erg_kennwerte = services.simuliere(s_kennwerte, n_simulations=4000, random_seed=42, batches=8)

    # Erwarteter PL-Mittelwert: PERT-Erwartungswert (low+gamma*mode+high)/(gamma+2, gamma=4) + Normal-Mittelwert.
    erwartet = (1000 + 4 * 2000 + 4000) / 6 + 3000
    assert erg_element["knoten"]["PL"]["mittelwert"] == pytest.approx(erwartet, rel=0.05)
    assert erg_kennwerte["knoten"]["PL"]["mittelwert"] == pytest.approx(erwartet, rel=0.05)


@pytest.mark.django_db
def test_run_simulation_faengt_fehler_ab():
    # Szenario ohne Faktoren -> pyfair kann nicht rechnen -> Status FEHLER.
    pytest.importorskip("pyfair")
    s = Szenario.objects.create(name="Leer", n_simulations=100)
    lauf = Simulationslauf.objects.create(szenario=s, n_simulations=100, random_seed=42)

    services._run_simulation(lauf.pk)

    lauf.refresh_from_db()
    assert lauf.status == Simulationslauf.Status.FEHLER
    assert lauf.fehler_text != ""
