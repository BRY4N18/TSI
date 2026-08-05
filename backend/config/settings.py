"""Django settings for Trafico Seguro Integral backend."""

import os
from datetime import timedelta
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

BASE_DIR = Path(__file__).resolve().parent.parent

from dotenv import load_dotenv

load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-dev-only-change-in-production",
)

DEBUG = os.environ.get("DJANGO_DEBUG", "true").lower() == "true"

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "apps.cuentas_clientes",
    "apps.accidentes",
    "apps.despacho",
    "apps.seguimiento",
    "apps.soporte_cliente",
    "apps.red_operativa",
    "apps.ventas_crm",
    "apps.suscripciones",
    "apps.informes_tacticos",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "es-co"
TIME_ZONE = "America/Bogota"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- JWT RS256 ---
def _load_or_generate_rsa_keys():
    keys_dir = BASE_DIR / "config" / "keys"
    private_path = keys_dir / "jwt_private.pem"
    public_path = keys_dir / "jwt_public.pem"

    if private_path.exists() and public_path.exists():
        private_pem = private_path.read_bytes()
        public_pem = public_path.read_bytes()
        return private_pem, public_pem

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    keys_dir.mkdir(parents=True, exist_ok=True)
    private_path.write_bytes(private_pem)
    public_path.write_bytes(public_pem)
    return private_pem, public_pem


JWT_PRIVATE_KEY, JWT_PUBLIC_KEY = _load_or_generate_rsa_keys()
JWT_ALGORITHM = "RS256"
JWT_ACCESS_TOKEN_LIFETIME = timedelta(seconds=3600)
JWT_REFRESH_TOKEN_LIFETIME = timedelta(days=14)
JWT_ISSUER = "tsi-auth"

# --- Pinot / Kafka ---
PINOT_BROKER_URL = os.environ.get("PINOT_BROKER_URL", "http://localhost:8099")
KAFKA_BOOTSTRAP_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

# --- ClickHouse (stack tactico — informes tácticos compuestos, solo lectura desde Django) ---
CLICKHOUSE_URL = os.environ.get("CLICKHOUSE_URL", "http://localhost:8123")
CLICKHOUSE_USER = os.environ.get("CLICKHOUSE_USER", "tactico")
CLICKHOUSE_PASSWORD = os.environ.get("CLICKHOUSE_PASSWORD", "tactico")
CLICKHOUSE_DB = os.environ.get("CLICKHOUSE_DB", "tsi_tactico")

# --- OSRM (ruteo por calles, self-hosted, ver infrastructure.md §6.1) ---
OSRM_URL = os.environ.get("OSRM_URL", "http://localhost:5000")

KAFKA_TOPICS = {
    "session": "Fact_Session_topic",
    "credential": "Dim_Credencial_topic",
    "user": "Dim_Usuarios_topic",
    "role": "Dim_Rol_topic",
    "user_role": "Dim_Usuario_Rol_topic",
    "server_user": "Dim_UsuariosServidor_topic",
    "server_role": "Dim_RolesServidor_topic",
    "server_user_role": "Dim_UsuariosServidorRolesServidor_topic",
    "server_role_mapping": "Dim_RolesServidorRoles_topic",
    "cliente": "Dim_Cliente_topic",
    "preferencias_cliente": "Dim_Preferencias_Cliente_topic",
    "onboarding": "Fact_Onboarding_topic",
    "accidente": "Fact_Accidente_topic",
    "accidente_estado": "Fact_AccidenteTipoEstadoAccidente_topic",
    "elemento_climatico_accidente": "Dim_ElementoClimaticosAccidente_topic",
    "elemento_fisico_accidente": "Dim_ElementoFisicoAccidente_topic",
    "conductor": "Dim_Conductor_topic",
    "vehiculo": "Dim_Vehiculo_topic",
    "conductor_accidente": "Fact_Conductor_Accidente_topic",
    "implicado": "Dim_Implicado_topic",
    "nota_accidente": "Dim_NotaAccidente_topic",
    "evidencia_foto": "Dim_EvidenciaFoto_topic",
    "historial_estado_unidad": "Fact_HistorialEstadoUnidad_topic",
    "despacho": "Fact_Despacho_topic",
    "notificacion_despacho": "Fact_NotificacionDespacho_topic",
    "historial_despacho": "Fact_HistorialDespachoUnidad_topic",
    "despacho_timeout": "DespachoTimeout_topic",
    "parametros_despacho": "Dim_ParametrosDespacho_topic",
    "historial_ubicacion_unidad": "Dim_HistorialUbicacionUnidadEmergencia_topic",
    "unidad_emergencia_snapshot": "Dim_UnidadEmergencia_topic",
    "despacho_abortado": "DespachoAbortado_topic",
    "parametros_seguimiento": "Dim_ParametrosSeguimiento_topic",
    "reclamo": "Fact_Reclamo_topic",
    "historial_ticket": "Fact_Historial_Ticket_topic",
    "sla_config": "Dim_SLAConfig_topic",
    "archivo_adjunto_reclamo": "Fact_ArchivosAdjuntosReclamos_topic",
    "baja_unidad": "Fact_BajaUnidad_topic",
    "region_operativa_snapshot": "Dim_RegionOperativa_topic",
    "validacion_region_snapshot": "Dim_ValidacionRegion_topic",
    "region_operativa_estado_region": "Dim_RegionOperativaEstadoRegion_topic",
    "estado_region": "Dim_EstadoRegion_topic",
    "prospecto": "Dim_Prospecto_topic",
    "asignacion": "Fact_Asignacion_topic",
    "pipeline": "Fact_Pipeline_topic",
    "interaccion_demo": "Fact_Interaccion_Demo_topic",
    "notificacion_ventas": "Fact_NotificacionVentas_topic",
    "plan": "Dim_Plan_topic",
    "metodo_pago": "Dim_MetodoPago_topic",
    "suscripcion": "Fact_Suscripcion_topic",
    "factura": "Fact_Factura_topic",
    "solicitud_cambio_plan": "Fact_Solicitud_Cambio_Plan_topic",
}

# --- Seguimiento (config compartida — no tabla de dominio del módulo) ---
# Fuente normativa Fase 4: flujoscorreguidos/flujo-emergencias-canonico.md
SEGUIMIENTO_PARAMETROS = {
    "gps_umbral_senal_perdida_seg": int(os.environ.get("GPS_UMBRAL_SENAL_PERDIDA_SEG", "60")),
    "gps_job_intervalo_seg": int(os.environ.get("GPS_JOB_INTERVALO_SEG", "30")),
    "geofence_radio_metros": int(os.environ.get("GEOFENCE_RADIO_METROS", "100")),
    "geofence_histeresis_seg": int(os.environ.get("GEOFENCE_HISTERESIS_SEG", "30")),
    "gps_retencion_dias": int(os.environ.get("GPS_RETENCION_DIAS", "90")),
}
# Alias histórico (clave con tilde en Pinot payload)
SEGUIMIENTO_PARAMETROS["geofence_histéresis_seg"] = SEGUIMIENTO_PARAMETROS[
    "geofence_histeresis_seg"
]

# --- Soporte al cliente (Gestión de Tickets) ---
# RN-TIC-005: el supervisor se resuelve por rol SupervisorSoporte en Dim_Usuario_Rol.
# SOPORTE_SUPERVISOR_USER_ID es opcional: preferencia si hay varios usuarios con el rol,
# o fallback si aún nadie tiene el rol asignado.
_soporte_supervisor_raw = os.environ.get("SOPORTE_SUPERVISOR_USER_ID", "").strip()
SOPORTE_SUPERVISOR_USER_ID = int(_soporte_supervisor_raw) if _soporte_supervisor_raw else None

# --- SMTP (Gmail / notificaciones cuenta) ---
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.environ.get("EMAIL_HOST", "")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "").replace(" ", "")
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "true").lower() == "true"
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER or "noreply@tsi.local")

# --- Azure Blob Storage (evidencia fotográfica — CU-O27 / evidencia-unidad) ---
BLOB_STORAGE_BACKEND = os.environ.get("BLOB_STORAGE_BACKEND", "local")
BLOB_STORAGE_LOCAL_PATH = BASE_DIR / "blob_storage"
BLOB_CONTAINER_EVIDENCIA = os.environ.get(
    "AZURE_CONTAINER",
    os.environ.get("BLOB_CONTAINER_EVIDENCIA", "evidencia-fotos"),
)
AZURE_ACCOUNT_NAME = os.environ.get("AZURE_ACCOUNT_NAME", "")
AZURE_ACCOUNT_KEY = os.environ.get("AZURE_ACCOUNT_KEY", "")
AZURE_BLOB_CONNECTION_STRING = os.environ.get("AZURE_BLOB_CONNECTION_STRING", "")
AZURE_BLOB_ACCOUNT_URL = os.environ.get(
    "AZURE_BLOB_ACCOUNT_URL",
    f"https://{AZURE_ACCOUNT_NAME}.blob.core.windows.net" if AZURE_ACCOUNT_NAME else "",
)
BLOB_STORAGE_BASE_URL = os.environ.get(
    "BLOB_STORAGE_BASE_URL",
    f"{AZURE_BLOB_ACCOUNT_URL.rstrip('/')}/{BLOB_CONTAINER_EVIDENCIA}"
    if AZURE_BLOB_ACCOUNT_URL
    else "",
)

# La sincronización diferida de evidencia (CU-O43) agrupa varias fotos
# pendientes (hasta 10MB cada una, ver core/storage/blob_storage_service.py)
# en un solo POST multipart, así que el límite de Django debe cubrir varias
# fotos a la vez, no solo una.
DATA_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "apps.cuentas_clientes.authentication.JWTSessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "core.auth.permissions.IsAuthenticated401",
    ],
    "UNAUTHENTICATED_USER": None,
    "EXCEPTION_HANDLER": "core.api.response_envelope.custom_exception_handler",
    "DEFAULT_THROTTLE_RATES": {
        "prospecto_registro": "10/min",
        "demo_sesion_ip": "20/min",
        "demo_interaccion_token": "60/min",
    },
}

# Demo interactiva (notificacion-ventas) — secrets for grant HMAC + session HS256
DEMO_GRANT_SECRET = os.environ.get(
    "DEMO_GRANT_SECRET", "dev-demo-grant-secret-min-32-chars!!"
)
DEMO_SESSION_SECRET = os.environ.get(
    "DEMO_SESSION_SECRET", "dev-demo-session-secret-min-32-chars!"
)
DEMO_SESSION_MINUTES = int(os.environ.get("DEMO_SESSION_MINUTES", "30"))
DEMO_REEVAL_DAYS = int(os.environ.get("DEMO_REEVAL_DAYS", "7"))
EVALUACION_REGLAS_DEMO_INTERVAL_SECONDS = int(
    os.environ.get("EVALUACION_REGLAS_DEMO_INTERVAL_SECONDS", "60")
)
