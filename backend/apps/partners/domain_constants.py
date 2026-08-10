"""Constantes de dominio de Partners y API (CU-O48 a CU-O55).

Compartidas por los tres modulos del departamento.
"""

# --- Roles (Dim_Rol) ---
ROL_ADMINISTRADOR = "Administrador"
ROL_DESARROLLADOR_APIS = "DesarrolladorAPIs"
ROL_PARTNER_INTEGRACION = "PartnerIntegracion"  # idrol 15, creado 2026-08-08
ROL_CLIENTE = "Cliente"

# --- Entornos de credencial ---
ENTORNO_SANDBOX = "Sandbox"
ENTORNO_PRODUCCION = "Producción"
ENTORNOS = frozenset({ENTORNO_SANDBOX, ENTORNO_PRODUCCION})

# --- Estados derivados del partner (spec.md seccion 9) ---
# NO son columnas: se derivan de Dim_Partner (activo, planapi) y del ultimo
# evento de Fact_HistorialAccesoPartner.
ESTADO_REGISTRADO = "Registrado"
ESTADO_PLAN_ASIGNADO = "Plan asignado"
ESTADO_PRUEBAS_ACTIVO = "Pruebas activo"
ESTADO_PENDIENTE_APROBACION = "Pendiente de aprobación"
ESTADO_PRODUCCION_ACTIVA = "Producción activa"
ESTADO_SUSPENDIDO = "Suspendido"

# --- tipo_cambio de Fact_HistorialAccesoPartner escritos por #07 ---
CAMBIO_REGISTRO = "registro"
CAMBIO_ASIGNACION_PLAN = "asignacion_plan"
CAMBIO_ACTIVACION_SANDBOX = "activacion_sandbox"
CAMBIO_EXPIRACION_SANDBOX = "expiracion_sandbox"
CAMBIO_SOLICITUD_PRODUCCION = "solicitud_promocion_produccion"
CAMBIO_ACTIVACION_PRODUCCION = "activacion_produccion"
CAMBIO_RECHAZO_PRODUCCION = "rechazo_promocion_produccion"

# --- Autores de eventos ---
EJECUTADO_POR_PARTNER = "Partner"
EJECUTADO_POR_ADMINISTRADOR = "Administrador"
EJECUTADO_POR_SISTEMA = "Sistema"

# ---------------------------------------------------------------------------
# CENTINELAS — Pinot no almacena NULL en este proyecto
# ---------------------------------------------------------------------------
# Ninguna consulta de este modulo usa IS NULL: las guardas comparan contra
# estos valores. Ver spec.md seccion 15 D2 y decisiones-pendientes.md #16.
SIN_PLAN = ""  # Dim_Partner.planapi — NO 'null' (era el centinela de Pinot)
SIN_CUPO = -1  # Dim_Partner.limitellamadasmes / limitellamadasminuto (0 seria valido)
SIN_ACTIVACION = 0  # Dim_Partner.sandbox_activado / sandbox_expiracion
SIN_SUSPENSION = ""  # Dim_Partner.fecha_suspension / motivo_suspension
SIN_CREDENCIAL = -1  # Fact_HistorialAccesoPartner.idcredencial (evento del partner)
SIN_MOTIVO = ""  # Fact_HistorialAccesoPartner.motivo / estado_anterior
SIN_URL = ""  # Dim_VersionContratoAPI.spec_url
SIN_FECHA_RETIRO = 0  # Dim_VersionContratoAPI.fecha_retiro

# "No expira nunca" (9999-12-31T23:59:59Z). Deliberadamente en el FUTURO: asi
# `fecha_expiracion < ahora` encuentra solo las realmente vencidas y nunca
# alcanza a las credenciales de produccion (RF-PON-008).
NUNCA_EXPIRA = 253402300799000

# --- Estados de version del contrato de integracion (CU-O50) ---
VERSION_VIGENTE = "vigente"
VERSION_SOPORTADA = "soportada"
VERSION_RETIRADA = "retirada"
ESTADOS_VERSION = frozenset({VERSION_VIGENTE, VERSION_SOPORTADA, VERSION_RETIRADA})

# --- Parametros configurables (RNF-20) ---
# Vigencia por defecto de una credencial de pruebas.
SANDBOX_VIGENCIA_DIAS = 30
# Aviso previo al vencimiento de pruebas (RF-PON-006).
SANDBOX_AVISO_PREVIO_DIAS = 7
# Entropia del secreto (RNF-PON-002). 32 bytes -> ~256 bits.
SECRETO_BYTES = 32
