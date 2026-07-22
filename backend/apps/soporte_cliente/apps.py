from django.apps import AppConfig


class SoporteClienteConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.soporte_cliente"
    verbose_name = "Gestión de Tickets de Soporte"

    def ready(self) -> None:
        # Job de monitoreo SLA (CU-O96) corre vía management command externo
        # (run_monitoreo_sla_job), no vía consumer Kafka — no requiere registro aquí.
        pass
