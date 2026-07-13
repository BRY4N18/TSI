from django.apps import AppConfig


class SeguimientoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.seguimiento"
    verbose_name = "Seguimiento y Cierre de Casos"

    def ready(self) -> None:
        # Jobs O37 / depuración GPS se registran vía scheduler externo (Celery/APScheduler).
        pass
