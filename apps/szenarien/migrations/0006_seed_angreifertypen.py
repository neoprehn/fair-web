"""Seed der Standard-Angreifertypen (Threat Capability)."""

from django.db import migrations


TYPEN = [
    ("Script Kiddie", "Opportunistisch, wenig Know-how", 0.05, 0.10, 0.20,
     "nutzt Standard-Tools, kaum Anpassung", "Virus"),
    ("Commodity Cybercrime / Standard User (Insider)", "Ransomware, Phishing-Kits / Insider",
     0.20, 0.35, 0.55, "automatisiert, aber effektiv",
     "Phishing, Ransomware / unbeabsichtigter Fehler, Shadow IT"),
    ("Professional Cybercrime", "organisierte Gruppen", 0.40, 0.60, 0.80,
     "gezielte Angriffe, gute Tools", "Ransomware, Supply Chain"),
    ("Privilegierter User", "Insider", 0.50, 0.70, 0.90,
     "Erhöhtes Fraud Risiko", "Betrug, Datenverlust"),
    ("Advanced Persistent Threat (APT)", "hoch spezialisiert", 0.60, 0.80, 0.95,
     "maßgeschneiderte Angriffe", "Gezielter Angriff, KRITIS"),
    ("Administrator/DevOps", "Insider", 0.70, 0.85, 0.95,
     "Sehr hohes Fraud Risiko", "Betrug, Sabotage, Datenverlust"),
    ("Nation State (Top Tier)", "staatlich, sehr hoch", 0.80, 0.95, 0.99,
     "nahezu keine Limitierung", "KRITIS"),
]


def seed(apps, schema_editor):
    Angreifertyp = apps.get_model("szenarien", "Angreifertyp")
    for i, (name, besch, low, mode, high, begr, szen) in enumerate(TYPEN):
        Angreifertyp.objects.get_or_create(
            name=name,
            defaults={
                "beschreibung": besch, "low": low, "mode": mode, "high": high,
                "begruendung": begr, "typisches_szenario": szen, "reihenfolge": i,
            },
        )


def entferne(apps, schema_editor):
    Angreifertyp = apps.get_model("szenarien", "Angreifertyp")
    Angreifertyp.objects.filter(name__in=[t[0] for t in TYPEN]).delete()


class Migration(migrations.Migration):
    dependencies = [("szenarien", "0005_angreifertyp")]
    operations = [migrations.RunPython(seed, entferne)]
