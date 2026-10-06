"""Tests für Mehr-Szenarien-Berechnung (FairMetaModel, Variante A)."""

import pytest
from django.urls import reverse

from apps.berechnung import services, views
from apps.berechnung.models import MetaLauf, Simulationslauf
from apps.szenarien.models import FaktorEingabe, Szenario


def _szenario(name, lm_konstant):
    s = Szenario.objects.create(name=name, n_simulations=300, random_seed=7)
    FaktorEingabe.objects.create(
        szenario=s, faktor="LEF", verteilung="pert",
        params={"low": 1, "mode": 3, "high": 6},
    )
    FaktorEingabe.objects.create(
        szenario=s, faktor="LM", verteilung="constant", params={"constant": lm_konstant},
    )
    return s


@pytest.mark.django_db
def test_simuliere_meta_gesamt_und_je_szenario():
    pytest.importorskip("pyfair")
    a = _szenario("A", 1000)
    b = _szenario("B", 2000)

    ergebnis = services.simuliere_meta([a, b], n_simulations=300, random_seed=42)

    assert set(ergebnis) == {"gesamt", "szenarien"}
    assert ergebnis["gesamt"]["n"] == 300
    assert len(ergebnis["szenarien"]) == 2
    namen = {s["name"] for s in ergebnis["szenarien"]}
    assert namen == {"A", "B"}
    # Gesamtmittelwert ~ Summe der Einzelmittelwerte (unabhängige Summen).
    summe_einzeln = sum(s["stats"]["mittelwert"] for s in ergebnis["szenarien"])
    assert ergebnis["gesamt"]["mittelwert"] == pytest.approx(summe_einzeln, rel=0.05)


@pytest.mark.django_db
def test_run_meta_setzt_fertig():
    pytest.importorskip("pyfair")
    a, b = _szenario("A", 1000), _szenario("B", 2000)
    lauf = MetaLauf.objects.create(n_simulations=300, random_seed=42)
    lauf.szenarien.set([a, b])

    services._run_meta(lauf.pk)

    lauf.refresh_from_db()
    assert lauf.status == Simulationslauf.Status.FERTIG
    assert lauf.ergebnis["gesamt"]["n"] == 300


@pytest.mark.django_db
def test_meta_starten_legt_lauf_an(client, monkeypatch):
    a, b = _szenario("A", 1000), _szenario("B", 2000)
    monkeypatch.setattr(views, "starte_meta_async", lambda meta_id: None)

    resp = client.post(reverse("berechnung:meta_starten"),
                       data={"szenarien": [a.pk, b.pk]})

    lauf = MetaLauf.objects.get()
    assert resp.status_code == 302
    assert resp.url == reverse("berechnung:meta_lauf", kwargs={"pk": lauf.pk})
    assert set(lauf.szenarien.values_list("pk", flat=True)) == {a.pk, b.pk}


@pytest.mark.django_db
def test_meta_starten_ohne_auswahl_zurueck_zum_dashboard(client):
    resp = client.post(reverse("berechnung:meta_starten"), data={})
    assert resp.status_code == 302
    assert resp.url == reverse("szenarien:dashboard")
    assert not MetaLauf.objects.exists()


@pytest.mark.django_db
def test_meta_lauf_zeigt_aktuellen_namen_nach_umbenennen(client):
    """Bug: ergebnis-JSON friert den Szenario-Namen zum Berechnungszeitpunkt ein - nach einem
    Umbenennen muss die Ergebnisseite trotzdem den aktuellen (nicht den alten) Namen zeigen."""
    pytest.importorskip("pyfair")
    a, b = _szenario("Alter Name A", 1000), _szenario("B", 2000)
    ergebnis = services.simuliere_meta([a, b], n_simulations=300, random_seed=42)
    lauf = MetaLauf.objects.create(
        n_simulations=300, random_seed=42,
        status=Simulationslauf.Status.FERTIG, fortschritt=100, ergebnis=ergebnis,
    )
    lauf.szenarien.set([a, b])
    # Das gespeicherte ergebnis-JSON hat weiterhin den alten Namen (gewolltes Verhalten -
    # der Snapshot wird nicht nachträglich umgeschrieben, nur die Anzeige korrigiert).
    assert {s["name"] for s in lauf.ergebnis["szenarien"]} == {"Alter Name A", "B"}

    a.name = "Neuer Name A"
    a.save()

    resp = client.get(reverse("berechnung:meta_lauf", kwargs={"pk": lauf.pk}))
    assert resp.status_code == 200
    namen = {s["name"] for s in resp.context["szenarien_ergebnis"]}
    assert namen == {"Neuer Name A", "B"}
    assert b"Alter Name A" not in resp.content
    assert b"Neuer Name A" in resp.content


@pytest.mark.django_db
def test_meta_lauf_faellt_bei_geloeschtem_szenario_auf_gespeicherten_namen_zurueck(client):
    pytest.importorskip("pyfair")
    a, b = _szenario("A", 1000), _szenario("B", 2000)
    ergebnis = services.simuliere_meta([a, b], n_simulations=300, random_seed=42)
    lauf = MetaLauf.objects.create(
        n_simulations=300, random_seed=42,
        status=Simulationslauf.Status.FERTIG, fortschritt=100, ergebnis=ergebnis,
    )
    lauf.szenarien.set([a, b])
    a_pk = a.pk
    a.delete()

    resp = client.get(reverse("berechnung:meta_lauf", kwargs={"pk": lauf.pk}))
    assert resp.status_code == 200
    eintraege = {s["pk"]: s["name"] for s in resp.context["szenarien_ergebnis"]}
    assert eintraege[a_pk] == "A"  # gespeicherter Name als Fallback, kein Fehler
    assert eintraege[b.pk] == "B"
