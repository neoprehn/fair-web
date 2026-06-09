"""Rollen-Gruppen + Rechte. Wird via ``post_migrate`` idempotent eingerichtet."""

# Analyst: voller Szenario-/Vergleichs-CRUD + Simulationen starten.
_ANALYST = [
    ("szenarien", "add_szenario"), ("szenarien", "change_szenario"),
    ("szenarien", "delete_szenario"), ("szenarien", "view_szenario"),
    ("szenarien", "add_faktoreingabe"), ("szenarien", "change_faktoreingabe"),
    ("szenarien", "delete_faktoreingabe"), ("szenarien", "view_faktoreingabe"),
    ("szenarien", "add_vergleich"), ("szenarien", "change_vergleich"),
    ("szenarien", "delete_vergleich"), ("szenarien", "view_vergleich"),
    ("szenarien", "add_cluster"), ("szenarien", "change_cluster"),
    ("szenarien", "delete_cluster"), ("szenarien", "view_cluster"),
    ("berechnung", "add_simulationslauf"), ("berechnung", "view_simulationslauf"),
    ("berechnung", "add_metalauf"), ("berechnung", "view_metalauf"),
]

# Konfigurator: wie Analyst + globale Konfiguration + Angreifertypen.
_KONFIGURATOR = _ANALYST + [
    ("admin_bereich", "change_appkonfiguration"), ("admin_bereich", "view_appkonfiguration"),
    ("szenarien", "add_angreifertyp"), ("szenarien", "change_angreifertyp"),
    ("szenarien", "delete_angreifertyp"), ("szenarien", "view_angreifertyp"),
]

# Betrachter: nur Lesen.
_BETRACHTER = [
    ("szenarien", "view_szenario"), ("szenarien", "view_faktoreingabe"),
    ("szenarien", "view_vergleich"), ("szenarien", "view_cluster"),
    ("berechnung", "view_simulationslauf"), ("berechnung", "view_metalauf"),
]

GRUPPEN_RECHTE = {
    "Betrachter": _BETRACHTER,
    "Analyst": _ANALYST,
    "Konfigurator": _KONFIGURATOR,
}


def setup_gruppen(**kwargs):
    """Legt die Rollen-Gruppen an und setzt ihre Rechte (idempotent)."""
    from django.contrib.auth.models import Group, Permission
    from django.db.models import Q

    def hole(pairs):
        if not pairs:
            return []
        q = Q()
        for app_label, codename in pairs:
            q |= Q(content_type__app_label=app_label, codename=codename)
        return list(Permission.objects.filter(q))

    for name, pairs in GRUPPEN_RECHTE.items():
        gruppe, _ = Group.objects.get_or_create(name=name)
        gruppe.permissions.set(hole(pairs))
