# Reparatur-Datenmigration fuer einen durch Migration 0003 verursachten
# Datenverlust: 0003 hat low/mode/high entfernt und params leer (default=dict)
# neu angelegt, ohne die alten Werte vorher zu uebernehmen. Betroffen war zum
# Reparaturzeitpunkt ausschliesslich das eine in Produktion existierende
# CAM-Szenario (Ransomware-Beispiel, https://fair.neoprehn.de/cam/1/) -
# Werte stammen aus apps/cam/beispiele.py (RANSOMWARE_BEISPIEL), unveraendert.
#
# Gezielt ueber szenario_id=1 + leere params gescoped, nicht blind ueber alle
# Zeilen, um kein anderes (ggf. inzwischen neu angelegtes) Szenario zu treffen.

from django.db import migrations

VERLUST_WERTE = {
    "early": {"low": 2_000, "mode": 8_000, "high": 30_000},
    "mid": {"low": 25_000, "mode": 75_000, "high": 250_000},
    "late": {"low": 200_000, "mode": 500_000, "high": 2_000_000},
    "full_impact": {"low": 1_000_000, "mode": 3_000_000, "high": 5_000_000},
    "attacker_fails": {"low": 2_000, "mode": 5_000, "high": 15_000},
}


def reparatur_verlustklassen_params(apps, schema_editor):
    CamVerlustklasse = apps.get_model("cam", "CamVerlustklasse")
    for row in CamVerlustklasse.objects.filter(szenario_id=1, params={}):
        werte = VERLUST_WERTE.get(row.klasse)
        if werte:
            row.verteilung = "pert"
            row.params = werte
            row.save(update_fields=["verteilung", "params"])


def noop_reverse(apps, schema_editor):
    # Nicht rueckgaengig machbar (und soll es auch nicht sein - das waere
    # wieder Datenverlust). Leere Funktion, damit die Migration trotzdem
    # als reversibel gilt (Django verlangt sonst eine explizite Begruendung).
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('cam', '0003_remove_camverlustklasse_high_and_more'),
    ]

    operations = [
        migrations.RunPython(reparatur_verlustklassen_params, noop_reverse),
    ]
