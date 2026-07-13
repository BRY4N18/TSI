from django.apps import AppConfig
from django.conf import settings


class DespachoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.despacho"
    verbose_name = "Despacho y Disponibilidad"

    def ready(self) -> None:
        from apps.despacho.consumers import register_consumer
        from apps.despacho.consumers.accidente_reportado_consumer import (
            handle_accidente_reportado,
        )
        from apps.despacho.consumers.despacho_timeout_consumer import handle_despacho_timeout

        register_consumer(
            settings.KAFKA_TOPICS["accidente_estado"],
            handle_accidente_reportado,
        )
        register_consumer(
            settings.KAFKA_TOPICS["despacho_timeout"],
            handle_despacho_timeout,
        )