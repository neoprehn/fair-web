from django.apps import AppConfig


class KontenConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.konten"
    verbose_name = "Konten & Rollen"

    def ready(self):
        from django.db.models.signals import post_migrate

        from .gruppen import setup_gruppen
        # Ohne sender: läuft nach jeder App-Migration (idempotent). Der letzte
        # Lauf (nach allen Apps) hat alle Permissions -> Gruppenrechte komplett.
        post_migrate.connect(setup_gruppen, dispatch_uid="konten_setup_gruppen")
