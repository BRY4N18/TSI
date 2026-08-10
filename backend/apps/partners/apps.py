from django.apps import AppConfig


class PartnersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.partners"
    verbose_name = "Partners y API"

    def ready(self) -> None:
        # App compartida por los tres módulos del departamento:
        #   #07 partner-api-onboarding      (CU-O48, O49, O50)
        #   #08 api-monitoring-and-billing  (CU-O51, O52, O53, O54)
        #   #09 partner-access-management   (CU-O55)
        # El job de expiración de credenciales (RF-PON-006) corre vía management
        # command externo (run_expiracion_credenciales_job), no vía consumer Kafka.
        pass
