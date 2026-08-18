"""Ayuda compartida por las pruebas que van contra el almacén de verdad.

Las pruebas de las fases 1 y 2 son de lógica pura y corren en cualquier sitio.
Estas no: comprueban **el modelo cargado**, y por tanto necesitan el stack
táctico levantado. Se saltan solas si no lo encuentran, en vez de fallar — un
fallo rojo por «no hay stack» entrena a ignorar los fallos rojos.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.clickhouse_http_client import query_clickhouse  # noqa: E402

#: Partición muy posterior a cualquier dato real. Las pruebas que necesitan
#: escribir lo hacen aquí y la descartan al terminar, para no tocar nunca las
#: cifras que otra prueba está comprobando.
PARTICION_DE_PRUEBA = 209912
FECHA_DE_PRUEBA = "2099-12-01"


def almacen_disponible() -> bool:
    try:
        query_clickhouse("SELECT 1")
        return True
    except Exception:  # noqa: BLE001
        return False


def modelo_cargado() -> bool:
    """El almacén responde **y** los hechos tienen datos."""
    if not almacen_disponible():
        return False
    try:
        return int(query_clickhouse("SELECT count() AS n FROM hecho_accidente")[0]["n"]) > 0
    except Exception:  # noqa: BLE001
        return False


requiere_modelo = pytest.mark.skipif(
    not modelo_cargado(),
    reason="requiere el stack táctico levantado y el modelo cargado",
)


def contar(sql: str) -> int:
    return int(query_clickhouse(sql)[0]["n"])


# ── Casos de prueba en la partición aislada ──────────────────────────────────
#
# Las pruebas de los informes OT21 escriben casos fabricados y comprueban qué
# cifra sale. Comparten este constructor a propósito: si cada fichero trajera el
# suyo, un cambio en el esquema del hecho habría que perseguirlo por cuatro
# sitios, y el que se olvidara seguiría pasando con datos que ya no existen.


def caso(
    idaccidente: str,
    *,
    severidad: bool = True,
    ubicacion: bool = True,
    condado: str = "Cuauhtemoc",
    idcalle: int | None = 1,
    descartado: bool = False,
    duplicado: bool = False,
    cerrado: bool = False,
    heridos: int = 0,
    fallecidos: int = 0,
) -> dict:
    """Un caso del período de prueba, con cada rasgo puesto o quitado por separado.

    Los rasgos son independientes **porque en el dominio lo son**: descartado,
    fusionado y cerrado no son tres valores de un estado sino tres hechos
    distintos, y un caso puede estar cerrado sin ser ninguno de los otros dos.
    Un constructor que los tratara como excluyentes impediría escribir la prueba
    que comprueba justamente que no se confunden.
    """
    return {
        "idaccidente": idaccidente,
        "fecha": FECHA_DE_PRUEBA,
        "fechahora_accidente": f"{FECHA_DE_PRUEBA} 10:00:00",
        "franja_horaria": "manana",
        "idcalle": idcalle if ubicacion else None,
        "condado": condado if ubicacion else None,
        "ciudad": "Ciudad de Mexico" if ubicacion else None,
        "idseveridad": 1 if severidad else None,
        "severidad": "Leve" if severidad else None,
        "hora_cierre": f"{FECHA_DE_PRUEBA} 11:00:00" if cerrado else None,
        "num_heridos": heridos,
        "num_fallecidos": fallecidos,
        "num_victimas": heridos + fallecidos,
        "fue_descartado": 1 if descartado else 0,
        "es_duplicado": 1 if duplicado else 0,
        "cargado_en": f"{FECHA_DE_PRUEBA} 12:00:00",
        "version": f"{FECHA_DE_PRUEBA} 12:00:00",
    }


def cargar_casos(casos: list[dict]) -> None:
    import json

    from lib.clickhouse_http_client import execute_clickhouse

    payload = "\n".join(json.dumps(c) for c in casos)
    execute_clickhouse(f"INSERT INTO hecho_accidente FORMAT JSONEachRow\n{payload}")


def limpiar_particion() -> None:
    """Descarta la partición de prueba. Nunca toca datos reales: la partición es
    `toYYYYMM('2099-12-01')`, muy posterior a cualquier caso del sistema."""
    from lib.clickhouse_http_client import execute_clickhouse

    execute_clickhouse(f"ALTER TABLE hecho_accidente DROP PARTITION {PARTICION_DE_PRUEBA}")


def ejecutar_informe(nombre: str, **parametros) -> list[dict]:
    """Ejecuta una consulta del catálogo sobre el período de prueba."""
    from lib.clickhouse_http_client import query_clickhouse
    from lib.consultas import cargar

    params = {"desde": FECHA_DE_PRUEBA, "hasta": FECHA_DE_PRUEBA}
    params.update({k: str(v) for k, v in parametros.items()})
    return query_clickhouse(cargar(nombre, departamento="emergencias"), params=params)


def despacho(
    iddespacho: int,
    *,
    idaccidente: str = "T0XX-caso",
    unidad: str = "TEST-001",
    proveedor: str = "Proveedor de prueba",
    condado: str = "Cuauhtemoc",
    severidad: str = "Leve",
    origen: str = "Automatico",
    numero_intento: int = 1,
    resultado: str = "confirmado",
    segundos_transito: int | None = 400,
    segundos_respuesta: int | None = 15,
    fecha: str | None = None,
) -> dict:
    """Un intento de despacho. **Una fila por intento**, no por caso.

    Ese grano es lo que hace calculable el indicador de primer intento: con grano
    de caso, los intentos fallidos no dejan rastro.
    """
    f = fecha or FECHA_DE_PRUEBA
    return {
        "iddespacho": iddespacho,
        "idaccidente": idaccidente,
        "fecha": f,
        "fechahora_despacho": f"{f} 10:00:00",
        "sk_unidad": 900000 + iddespacho,
        "idunidademergencia": 9001,
        "unidad": unidad,
        "proveedor": proveedor,
        "idorigendespacho": 1,
        "origen_despacho": origen,
        "idseveridad": 1,
        "severidad": severidad,
        "condado": condado,
        "hora_llegada": f"{f} 10:07:00" if segundos_transito is not None else None,
        "segundos_respuesta": segundos_respuesta,
        "segundos_transito": segundos_transito,
        "numero_intento": numero_intento,
        "resultado": resultado,
        "retiro_forzado": 0,
        "cargado_en": f"{f} 12:00:00",
        "version": f"{f} 12:00:00",
    }


def cargar_despachos(filas: list[dict]) -> None:
    import json

    from lib.clickhouse_http_client import execute_clickhouse

    payload = "\n".join(json.dumps(f) for f in filas)
    execute_clickhouse(f"INSERT INTO hecho_despacho FORMAT JSONEachRow\n{payload}")


def limpiar_despachos() -> None:
    from lib.clickhouse_http_client import execute_clickhouse

    execute_clickhouse(f"ALTER TABLE hecho_despacho DROP PARTITION {PARTICION_DE_PRUEBA}")


def ping(idping: int, *, segundos_desde_anterior: int | None, proveedor: str = "Proveedor de prueba") -> dict:
    return {
        "idping": idping,
        "fecha": FECHA_DE_PRUEBA,
        "fechahora": f"{FECHA_DE_PRUEBA} 10:00:00",
        "sk_unidad": 900001,
        "idunidademergencia": 9001,
        "proveedor": proveedor,
        "segundos_desde_anterior": segundos_desde_anterior,
        "cargado_en": f"{FECHA_DE_PRUEBA} 12:00:00",
    }


def cargar_pings(filas: list[dict]) -> None:
    import json

    from lib.clickhouse_http_client import execute_clickhouse

    payload = "\n".join(json.dumps(f) for f in filas)
    execute_clickhouse(f"INSERT INTO hecho_ping_unidad FORMAT JSONEachRow\n{payload}")


def limpiar_pings() -> None:
    from lib.clickhouse_http_client import execute_clickhouse

    execute_clickhouse(f"ALTER TABLE hecho_ping_unidad DROP PARTITION {PARTICION_DE_PRUEBA}")


# ── Red Operativa: transiciones de estado y bajas en la particion aislada ────


def transicion(
    idhistorial: int,
    *,
    unidad: str = "TEST-RO",
    idunidad: int = 9101,
    estado: str | None = "Activa",
    hora: str = "00:00:00",
    proveedor: str = "Proveedor de prueba",
) -> dict:
    """Una transicion de estado de unidad.

    `estado` es el **texto**, no un identificador: el hecho lo guarda resuelto
    precisamente para que las consultas no tengan que unir con un catalogo que
    esta incompleto.
    """
    return {
        "idhistorial": idhistorial,
        "fecha": FECHA_DE_PRUEBA,
        "fechahora": f"{FECHA_DE_PRUEBA} {hora}",
        "sk_unidad": 990000 + idunidad,
        "idunidademergencia": idunidad,
        "unidad": unidad,
        "proveedor": proveedor,
        "estado_nuevo": estado,
        "es_cambio_efectivo": 1,
        "cargado_en": f"{FECHA_DE_PRUEBA} 12:00:00",
    }


def cargar_transiciones(filas: list[dict]) -> None:
    import json

    from lib.clickhouse_http_client import execute_clickhouse

    payload = "\n".join(json.dumps(f, ensure_ascii=False) for f in filas)
    execute_clickhouse(f"INSERT INTO hecho_estado_unidad FORMAT JSONEachRow\n{payload}")


def limpiar_transiciones() -> None:
    from lib.clickhouse_http_client import execute_clickhouse

    execute_clickhouse(
        f"ALTER TABLE hecho_estado_unidad DROP PARTITION {PARTICION_DE_PRUEBA}"
    )


def ejecutar_red_operativa(nombre: str, **parametros) -> list[dict]:
    """Ejecuta una consulta de Red Operativa sobre el periodo de prueba."""
    from lib.clickhouse_http_client import query_clickhouse
    from lib.consultas import cargar

    params = {"desde": FECHA_DE_PRUEBA, "hasta": FECHA_DE_PRUEBA}
    params.update({k: str(v) for k, v in parametros.items()})
    return query_clickhouse(cargar(nombre, departamento="red_operativa"), params=params)


# ── Ventas y CRM (partición aislada + dimensión por id alto) ───────────────

ID_PROSPECTO_PRUEBA = 990000


def asegurar_hechos_ventas_crm() -> None:
    from lib.ddl import (
        ensure_hecho_asignacion_prospecto,
        ensure_hecho_interaccion_demo,
        ensure_hecho_notificacion_ventas,
        ensure_hecho_transicion_embudo,
        ensure_dim_prospecto,
        ensure_dim_canal,
    )

    ensure_dim_canal()
    ensure_dim_prospecto()
    ensure_hecho_transicion_embudo()
    ensure_hecho_asignacion_prospecto()
    ensure_hecho_interaccion_demo()
    ensure_hecho_notificacion_ventas()


def insertar(tabla: str, filas: list[dict]) -> None:
    import json

    from lib.clickhouse_http_client import execute_clickhouse

    if not filas:
        return
    payload = "\n".join(json.dumps(f, ensure_ascii=False) for f in filas)
    execute_clickhouse(f"INSERT INTO {tabla} FORMAT JSONEachRow\n{payload}")


def limpiar_ventas_crm() -> None:
    from lib.clickhouse_http_client import execute_clickhouse

    for tabla in (
        "hecho_transicion_embudo",
        "hecho_asignacion_prospecto",
        "hecho_interaccion_demo",
        "hecho_notificacion_ventas",
    ):
        execute_clickhouse(f"ALTER TABLE {tabla} DROP PARTITION {PARTICION_DE_PRUEBA}")
    execute_clickhouse(
        f"ALTER TABLE dim_prospecto DELETE WHERE idprospecto >= {ID_PROSPECTO_PRUEBA} "
        "SETTINGS mutations_sync = 2"
    )
    execute_clickhouse(
        f"ALTER TABLE dim_canal DELETE WHERE idcanal >= {ID_PROSPECTO_PRUEBA} "
        "SETTINGS mutations_sync = 2"
    )


def ejecutar_ventas_crm(nombre: str, **parametros) -> list[dict]:
    """Ejecuta una consulta de Ventas y CRM sobre el periodo de prueba."""
    from lib.clickhouse_http_client import query_clickhouse
    from lib.consultas import cargar

    params = {
        "desde": FECHA_DE_PRUEBA,
        "hasta": FECHA_DE_PRUEBA,
        "idejecutivo": "-1",
        "top": "10",
    }
    params.update({k: str(v) for k, v in parametros.items()})
    return query_clickhouse(cargar(nombre, departamento="ventas_crm"), params=params)


def prospecto_de_prueba(
    idprospecto: int,
    *,
    canal: str = "Web",
    etapa_actual: str = "Contactado",
    desenlace: str = "en_curso",
    valor_estimado: float = 1000.0,
    fecha_registro: str | None = None,
    empresa: str = "Empresa prueba",
) -> dict:
    return {
        "idprospecto": idprospecto,
        "empresa": empresa,
        "tipo_organizacion": "Privada",
        "idcanal": 1,
        "canal": canal,
        "etapa_actual": etapa_actual,
        "desenlace": desenlace,
        "motivo_inactividad": None,
        "valor_estimado": valor_estimado,
        "fecha_registro": fecha_registro or f"{FECHA_DE_PRUEBA} 08:00:00",
        "version": f"{FECHA_DE_PRUEBA} 12:00:00",
    }


# ── Suscripciones y Facturación ─────────────────────────────────────────────

ID_CLIENTE_PRUEBA = 990000
ID_PLAN_PRUEBA = 990000
ID_SUSCRIPCION_PRUEBA = 990000


def asegurar_hechos_suscripciones() -> None:
    from lib.ddl import (
        ensure_columnas_nuevas_dimensiones,
        ensure_dim_plan,
        ensure_dim_cliente,
        ensure_hecho_suscripcion,
        ensure_hecho_factura,
        ensure_hecho_solicitud_cambio_plan,
        ensure_dim_unidad,
        ensure_dim_severidad,
        ensure_hecho_accidente,
    )

    ensure_dim_plan()
    ensure_dim_cliente()
    ensure_columnas_nuevas_dimensiones()
    ensure_hecho_suscripcion()
    ensure_hecho_factura()
    ensure_hecho_solicitud_cambio_plan()
    ensure_dim_unidad()
    ensure_dim_severidad()
    ensure_hecho_accidente()


def limpiar_suscripciones() -> None:
    from lib.clickhouse_http_client import execute_clickhouse

    for tabla in ("hecho_suscripcion", "hecho_factura", "hecho_solicitud_cambio_plan"):
        execute_clickhouse(f"ALTER TABLE {tabla} DROP PARTITION {PARTICION_DE_PRUEBA}")
    execute_clickhouse(
        f"ALTER TABLE dim_plan DELETE WHERE idplan >= {ID_PLAN_PRUEBA} "
        "SETTINGS mutations_sync = 2"
    )
    execute_clickhouse(
        f"ALTER TABLE dim_cliente DELETE WHERE idcliente >= {ID_CLIENTE_PRUEBA} "
        "SETTINGS mutations_sync = 2"
    )
    execute_clickhouse(
        f"ALTER TABLE dim_unidad DELETE WHERE idcliente >= {ID_CLIENTE_PRUEBA} "
        "SETTINGS mutations_sync = 2"
    )


def ejecutar_suscripciones(nombre: str, **parametros) -> list[dict]:
    from lib.clickhouse_http_client import query_clickhouse
    from lib.consultas import cargar

    params = {
        "desde": FECHA_DE_PRUEBA,
        "hasta": FECHA_DE_PRUEBA,
        "mes": FECHA_DE_PRUEBA[:7],
        "escalones_dunning": "3,5",
        "dias_aviso_caducidad": "30",
    }
    params.update({k: str(v) for k, v in parametros.items()})
    return query_clickhouse(cargar(nombre, departamento="suscripciones"), params=params)


def plan_de_prueba(
    idplan: int,
    *,
    nombre: str = "Plan prueba",
    nivel: str = "Profesional",
    precio_lista: float = 100.0,
    limite_unidades: int | None = 25,
    limite_usuarios: int | None = 2500,
    severidades: list[int] | None = None,
) -> dict:
    return {
        "idplan": idplan,
        "nombre": nombre,
        "nivel": nivel,
        "periodicidad": "Mensual",
        "precio_lista": precio_lista,
        "precio_excedente_llamada": None,
        "limite_unidades": limite_unidades,
        "limite_usuarios": limite_usuarios,
        "limite_llamadas_mes": None,
        "limite_llamadas_minuto": None,
        "severidades_habilitadas": severidades or [1],
        "carga_lote_habilitada": 0,
        "es_activo": 1,
        "version": f"{FECHA_DE_PRUEBA} 12:00:00",
    }


def cliente_de_prueba(
    idcliente: int,
    *,
    nombre: str = "Cliente prueba",
    tiene_metodo_pago: int = 0,
    metodo_pago_caduca: str | None = None,
    fecha_alta: str | None = None,
    cohorte_alta: str | None = None,
    fecha_baja: str | None = None,
    motivo_baja: str | None = None,
    etapa_onboarding_actual: str | None = None,
    onboarding_completo: int = 0,
    resultado_solicitud: str | None = None,
    tipo: str = "aseguradora",
    estado_comercial: str = "Activo",
    estado_onboarding: str | None = "Completado",
) -> dict:
    alta = fecha_alta or f"{FECHA_DE_PRUEBA} 08:00:00"
    return {
        "idcliente": idcliente,
        "nombre_comercial": nombre,
        "tipo": tipo,
        "estado_comercial": estado_comercial,
        "estado_onboarding": estado_onboarding,
        "tiene_metodo_pago": tiene_metodo_pago,
        "metodo_pago_caduca": metodo_pago_caduca,
        "fecha_alta": alta,
        "cohorte_alta": cohorte_alta if cohorte_alta is not None else alta[:7],
        "fecha_baja": fecha_baja,
        "motivo_baja": motivo_baja,
        "etapa_onboarding_actual": etapa_onboarding_actual,
        "onboarding_completo": onboarding_completo,
        "resultado_solicitud": resultado_solicitud,
        "version": f"{FECHA_DE_PRUEBA} 12:00:00",
    }


def suscripcion_de_prueba(
    id_suscripcion: int,
    *,
    idcliente: int | None = None,
    idplan: int | None = None,
    plan: str = "Plan prueba",
    estado_derivado: str = "vigente",
    precio: float = 120.0,
    periodicidad: str | None = "Mensual",
    precio_mensualizado: float | None = 120.0,
    fecha_alta: str | None = None,
    fecha_cancelacion: str | None = None,
    vigencia_inconsistente: int = 0,
    motivo_cancelacion: str | None = None,
) -> dict:
    alta = fecha_alta or f"{FECHA_DE_PRUEBA} 08:00:00"
    return {
        "id_suscripcion": id_suscripcion,
        "fecha": FECHA_DE_PRUEBA,
        "idcliente": idcliente if idcliente is not None else ID_CLIENTE_PRUEBA,
        "tipo_cliente": "aseguradora",
        "idplan": idplan if idplan is not None else ID_PLAN_PRUEBA,
        "plan": plan,
        "nivel": "Profesional",
        "fecha_alta": alta,
        "fecha_fin_prevista": f"{FECHA_DE_PRUEBA} 08:00:00",
        "fecha_ultima_renovacion": None,
        "fecha_suspension": None,
        "fecha_reactivacion": None,
        "fecha_cancelacion": fecha_cancelacion,
        "estado_derivado": estado_derivado,
        "motivo_cancelacion": motivo_cancelacion,
        "precio": precio,
        "periodicidad": periodicidad,
        "precio_mensualizado": precio_mensualizado,
        "renovacion_automatica": 1,
        "idplan_programado": None,
        "severidades_contratadas": [1],
        "vigencia_inconsistente": vigencia_inconsistente,
        "cargado_en": f"{FECHA_DE_PRUEBA} 12:00:00",
        "version": f"{FECHA_DE_PRUEBA} 12:00:00",
    }


def factura_de_prueba(
    id_factura: str,
    *,
    idcliente: int | None = None,
    monto_total: float = 100.0,
    es_nota_credito: int = 0,
    estado_pago: str = "Pagada",
    reintentos: int = 0,
    pagada_primer_intento: int | None = None,
    dias_mora: int | None = None,
    plan: str = "Plan prueba",
) -> dict:
    signo = -1 if es_nota_credito else 1
    primer = pagada_primer_intento
    if primer is None:
        primer = 1 if estado_pago == "Pagada" and reintentos == 0 and not es_nota_credito else 0
    return {
        "id_factura": id_factura,
        "fecha": FECHA_DE_PRUEBA,
        "fecha_emision": f"{FECHA_DE_PRUEBA} 10:00:00",
        "fecha_vencimiento": f"{FECHA_DE_PRUEBA} 10:00:00",
        "idcliente": idcliente if idcliente is not None else ID_CLIENTE_PRUEBA,
        "tipo_cliente": "aseguradora",
        "id_suscripcion": ID_SUSCRIPCION_PRUEBA,
        "idplan": ID_PLAN_PRUEBA,
        "plan": plan,
        "estado_pago": estado_pago,
        "es_nota_credito": es_nota_credito,
        "id_factura_original": None,
        "signo": signo,
        "monto_base": monto_total,
        "impuestos": 0,
        "monto_total": monto_total,
        "monto_con_signo": monto_total * signo,
        "reintentos": reintentos,
        "pagada_primer_intento": primer,
        "dias_mora": dias_mora,
        "cargado_en": f"{FECHA_DE_PRUEBA} 12:00:00",
    }


def solicitud_de_prueba(
    idsolicitud: int,
    *,
    idcliente: int | None = None,
    tipo_movimiento: str = "upgrade",
    delta_precio: float = 50.0,
    estado: str = "aprobada",
    segundos_resolucion: int | None = 3600,
    plan_actual: str = "Basico",
    plan_solicitado: str = "Empresarial",
) -> dict:
    resuelta = 0 if estado == "pendiente" else 1
    return {
        "idsolicitud": idsolicitud,
        "fecha": FECHA_DE_PRUEBA,
        "fecha_solicitud": f"{FECHA_DE_PRUEBA} 08:00:00",
        "fecha_resolucion": None if not resuelta else f"{FECHA_DE_PRUEBA} 09:00:00",
        "idcliente": idcliente if idcliente is not None else ID_CLIENTE_PRUEBA,
        "idplan_actual": ID_PLAN_PRUEBA,
        "plan_actual": plan_actual,
        "idplan_solicitado": ID_PLAN_PRUEBA + 1,
        "plan_solicitado": plan_solicitado,
        "tipo_movimiento": tipo_movimiento,
        "delta_precio": delta_precio,
        "estado": estado,
        "esta_resuelta": resuelta,
        "segundos_resolucion": segundos_resolucion if resuelta else None,
        "cargado_en": f"{FECHA_DE_PRUEBA} 12:00:00",
    }


# ── Cuentas y Clientes ──────────────────────────────────────────────────────

ID_USUARIO_PRUEBA = 990000
ID_SESION_PRUEBA = 990000
ID_ONBOARDING_PRUEBA = 990000
ID_ROL_PRUEBA = 990000


def asegurar_hechos_cuentas() -> None:
    from lib.ddl import (
        ensure_columnas_nuevas_dimensiones,
        ensure_dim_cliente,
        ensure_dim_etapa_onboarding,
        ensure_dim_plan,
        ensure_dim_rol,
        ensure_dim_usuario_organizacion,
        ensure_dim_usuario_rol,
        ensure_hecho_onboarding,
        ensure_hecho_sesion,
        ensure_hecho_suscripcion,
    )

    ensure_dim_plan()
    ensure_dim_cliente()
    ensure_columnas_nuevas_dimensiones()
    ensure_dim_usuario_organizacion()
    ensure_dim_etapa_onboarding()
    ensure_dim_rol()
    ensure_dim_usuario_rol()
    ensure_hecho_sesion()
    ensure_hecho_onboarding()
    ensure_hecho_suscripcion()


def limpiar_cuentas() -> None:
    from lib.clickhouse_http_client import execute_clickhouse

    execute_clickhouse(
        f"ALTER TABLE hecho_sesion DROP PARTITION {PARTICION_DE_PRUEBA}"
    )
    execute_clickhouse(
        f"ALTER TABLE hecho_onboarding DROP PARTITION {PARTICION_DE_PRUEBA}"
    )
    execute_clickhouse(
        f"ALTER TABLE hecho_sesion DELETE WHERE idsesion >= {ID_SESION_PRUEBA} "
        "SETTINGS mutations_sync = 2"
    )
    execute_clickhouse(
        f"ALTER TABLE hecho_onboarding DELETE WHERE idonboarding >= {ID_ONBOARDING_PRUEBA} "
        "SETTINGS mutations_sync = 2"
    )
    execute_clickhouse(
        f"ALTER TABLE dim_usuario_organizacion DELETE WHERE idusuario >= {ID_USUARIO_PRUEBA} "
        "SETTINGS mutations_sync = 2"
    )
    execute_clickhouse(
        f"ALTER TABLE dim_usuario_rol DELETE WHERE idusuario >= {ID_USUARIO_PRUEBA} "
        "SETTINGS mutations_sync = 2"
    )
    execute_clickhouse(
        f"ALTER TABLE dim_rol DELETE WHERE idrol >= {ID_ROL_PRUEBA} "
        "SETTINGS mutations_sync = 2"
    )
    execute_clickhouse(
        f"ALTER TABLE dim_cliente DELETE WHERE idcliente >= {ID_CLIENTE_PRUEBA} "
        "SETTINGS mutations_sync = 2"
    )
    execute_clickhouse(
        f"ALTER TABLE dim_plan DELETE WHERE idplan >= {ID_PLAN_PRUEBA} "
        "SETTINGS mutations_sync = 2"
    )
    execute_clickhouse(
        f"ALTER TABLE hecho_suscripcion DELETE WHERE id_suscripcion >= {ID_SUSCRIPCION_PRUEBA} "
        "SETTINGS mutations_sync = 2"
    )


def ejecutar_cuentas(nombre: str, **parametros) -> list[dict]:
    from lib.clickhouse_http_client import query_clickhouse
    from lib.consultas import cargar

    params = {
        "desde": FECHA_DE_PRUEBA,
        "hasta": FECHA_DE_PRUEBA,
        "mes_cohorte": "",
        "dias_inactividad": "90",
        "pares": "",
    }
    params.update({k: str(v) for k, v in parametros.items()})
    return query_clickhouse(cargar(nombre, departamento="cuentas"), params=params)


def etapas_catalogo() -> list[dict]:
    from datetime import datetime

    from lib.dimensiones.dim_etapa_onboarding import construir

    return construir([], datetime(2099, 12, 1, 12, 0, 0))


def usuario_org_de_prueba(
    idusuario: int,
    *,
    idcliente: int | None = None,
    tiene_pertenencia: int | None = None,
    es_activo: int = 1,
) -> dict:
    if tiene_pertenencia is None:
        tiene_pertenencia = 1 if idcliente is not None else 0
    return {
        "idusuario": idusuario,
        "idcliente": idcliente,
        "tiene_pertenencia": tiene_pertenencia,
        "es_activo": es_activo,
        "version": f"{FECHA_DE_PRUEBA} 12:00:00",
    }


def sesion_de_prueba(
    idsesion: int,
    *,
    inicio: str = "2099-12-01 10:00:00",
    cierre: str | None = None,
    desenlace: str | None = None,
    idusuario: int | None = None,
    idcliente: int | None = None,
    duracion_segundos: int | None = None,
) -> dict:
    from datetime import datetime

    ini = datetime.strptime(inicio[:19], "%Y-%m-%d %H:%M:%S")
    dur = duracion_segundos
    if dur is None and cierre:
        fin = datetime.strptime(cierre[:19], "%Y-%m-%d %H:%M:%S")
        dur = int((fin - ini).total_seconds())
    if desenlace is None:
        desenlace = "cerrada" if cierre else "abierta"
    hora = ini.hour
    franja = (
        "madrugada" if hora < 6 else
        "manana" if hora < 12 else
        "tarde" if hora < 18 else
        "noche"
    )
    return {
        "idsesion": idsesion,
        "fecha": inicio[:10],
        "fechahora_inicio": inicio,
        "fechahora_cierre": cierre,
        "idusuario": idusuario if idusuario is not None else ID_USUARIO_PRUEBA,
        "idcliente": idcliente,
        "pertenencia_conocida": 1 if idcliente is not None else 0,
        "desenlace": desenlace,
        "navegador": None,
        "franja_horaria": franja,
        "duracion_segundos": dur,
        "cargado_en": f"{FECHA_DE_PRUEBA} 12:00:00",
    }


def onboarding_de_prueba(
    idonboarding: int,
    *,
    idcliente: int | None = None,
    idetapa: int = 1,
    etapa: str = "cambio_password",
    fecha: str | None = None,
    dias_desde_alta: int = 0,
) -> dict:
    dia = fecha or FECHA_DE_PRUEBA
    return {
        "idonboarding": idonboarding,
        "fecha": dia,
        "fechahora": f"{dia} 08:00:00",
        "idcliente": idcliente if idcliente is not None else ID_CLIENTE_PRUEBA,
        "tipo_cliente": "aseguradora",
        "idetapa": idetapa,
        "etapa": etapa,
        "orden_etapa": idetapa,
        "dias_desde_alta": dias_desde_alta,
        "cargado_en": f"{FECHA_DE_PRUEBA} 12:00:00",
    }


def rol_de_prueba(idrol: int, rol: str) -> dict:
    return {
        "idrol": idrol,
        "rol": rol,
        "descripcion": None,
        "es_activo": 1,
        "version": f"{FECHA_DE_PRUEBA} 12:00:00",
    }


def asignacion_de_prueba(idusuario: int, idrol: int, rol: str) -> dict:
    return {
        "idusuario": idusuario,
        "idrol": idrol,
        "rol": rol,
        "es_activo": 1,
        "version": f"{FECHA_DE_PRUEBA} 12:00:00",
    }


# ── Partners y API ──────────────────────────────────────────────────────────

ID_PARTNER_PRUEBA = 990000
ID_LOG_PRUEBA = 990000
ID_HISTORIAL_PRUEBA = 990000
ID_CREDENCIAL_PRUEBA = 990000
ID_VERSION_PRUEBA = 990000


def asegurar_hechos_partners() -> None:
    from lib.ddl import (
        ensure_columnas_nuevas_hecho_factura,
        ensure_dim_cliente,
        ensure_dim_credencial_api,
        ensure_dim_partner,
        ensure_dim_version_contrato,
        ensure_hecho_accidente,
        ensure_hecho_cambio_acceso,
        ensure_hecho_factura,
        ensure_hecho_llamada_api,
    )

    ensure_dim_partner()
    ensure_dim_credencial_api()
    ensure_dim_version_contrato()
    ensure_dim_cliente()
    ensure_hecho_llamada_api()
    ensure_hecho_cambio_acceso()
    ensure_hecho_factura()
    ensure_columnas_nuevas_hecho_factura()
    ensure_hecho_accidente()


def limpiar_partners() -> None:
    from lib.clickhouse_http_client import execute_clickhouse

    execute_clickhouse(f"ALTER TABLE hecho_llamada_api DROP PARTITION {PARTICION_DE_PRUEBA}")
    execute_clickhouse(f"ALTER TABLE hecho_cambio_acceso DROP PARTITION {PARTICION_DE_PRUEBA}")
    execute_clickhouse(
        f"ALTER TABLE dim_partner DELETE WHERE idpartner >= {ID_PARTNER_PRUEBA} "
        "SETTINGS mutations_sync = 2"
    )
    execute_clickhouse(
        f"ALTER TABLE dim_credencial_api DELETE WHERE idcredencial >= {ID_CREDENCIAL_PRUEBA} "
        "SETTINGS mutations_sync = 2"
    )
    execute_clickhouse(
        f"ALTER TABLE dim_version_contrato DELETE WHERE idversion >= {ID_VERSION_PRUEBA} "
        "SETTINGS mutations_sync = 2"
    )
    execute_clickhouse(
        f"ALTER TABLE dim_cliente DELETE WHERE idcliente >= {ID_CLIENTE_PRUEBA} "
        "SETTINGS mutations_sync = 2"
    )
    execute_clickhouse(
        f"ALTER TABLE hecho_factura DELETE WHERE id_factura LIKE 'P-TEST-%' "
        "SETTINGS mutations_sync = 2"
    )


def ejecutar_partners(nombre: str, **parametros) -> list[dict]:
    from lib.clickhouse_http_client import query_clickhouse
    from lib.consultas import cargar

    params = {
        "desde": FECHA_DE_PRUEBA,
        "hasta": FECHA_DE_PRUEBA,
        "percentil": "95",
        "muestra_minima": "20",
        "mes": "",
        "dias_aviso_expiracion": "30",
    }
    params.update({k: str(v) for k, v in parametros.items()})
    return query_clickhouse(cargar(nombre, departamento="partners"), params=params)


def partner_de_prueba(
    idpartner: int,
    *,
    nombre: str = "Partner prueba",
    idcliente: int | None = None,
    limite_mes: int | None = 1000,
) -> dict:
    return {
        "idpartner": idpartner,
        "nombre_partner": nombre,
        "idcliente": idcliente,
        "plan_api": "pro",
        "limite_llamadas_mes": limite_mes,
        "limite_llamadas_minuto": 10,
        "estado": "activo",
        "fecha_suspension": None,
        "sandbox_activado": None,
        "sandbox_expiracion": None,
        "version": f"{FECHA_DE_PRUEBA} 12:00:00",
    }


def llamada_de_prueba(
    idlog: int,
    *,
    idpartner: int | None = None,
    partner: str = "Partner prueba",
    idcliente: int | None = None,
    endpoint_path: str = "/api/v1/datos/accidentes",
    metodo_http: str = "GET",
    codigo_http: int = 200,
    clase_resultado: str | None = None,
    latencia_ms: int = 80,
    servicio: str = "datos",
    version_contrato: str = "v1",
    inicio: str | None = None,
) -> dict:
    if clase_resultado is None:
        clase_resultado = {
            429: "limite_cupo",
            403: "autorizacion",
            401: "autorizacion",
            500: "error_servicio",
        }.get(codigo_http, "exito" if codigo_http < 400 else "error_cliente")
    cuando = inicio or f"{FECHA_DE_PRUEBA} 10:00:00"
    return {
        "idlog": idlog,
        "fecha": cuando[:10],
        "fechahora": cuando,
        "idpartner": idpartner if idpartner is not None else ID_PARTNER_PRUEBA,
        "partner": partner,
        "idcliente": idcliente,
        "plan_api": "pro",
        "idcredencial": None,
        "entorno": "Producción",
        "endpoint_path": endpoint_path,
        "metodo_http": metodo_http,
        "codigo_http": codigo_http,
        "clase_resultado": clase_resultado,
        "latencia_ms": latencia_ms,
        "servicio": servicio,
        "version_contrato": version_contrato,
        "version_es_derivada": 1,
        "cargado_en": f"{FECHA_DE_PRUEBA} 12:00:00",
    }


def credencial_de_prueba(
    idcredencial: int,
    *,
    idpartner: int | None = None,
    activa: int = 0,
    motivo: str | None = "revocada",
    fecha_expiracion: str | None = None,
    nunca_expira: int = 0,
) -> dict:
    return {
        "idcredencial": idcredencial,
        "idpartner": idpartner if idpartner is not None else ID_PARTNER_PRUEBA,
        "idcliente": None,
        "nombre_credencial": "cred",
        "entorno": "Producción",
        "esta_activa": activa,
        "motivo_inactividad": motivo if not activa else None,
        "fecha_creacion": f"{FECHA_DE_PRUEBA} 08:00:00",
        "fecha_expiracion": fecha_expiracion,
        "nunca_expira": nunca_expira,
        "version": f"{FECHA_DE_PRUEBA} 12:00:00",
    }


def cambio_de_prueba(
    idhistorial: int,
    *,
    idpartner: int | None = None,
    partner: str = "Partner prueba",
    tipo_cambio: str = "registro",
    estado_anterior: str | None = "Registrado",
    estado_nuevo: str | None = "Plan asignado",
    efectivo: int = 1,
    motivo: str | None = None,
    idcredencial: int | None = None,
    cuando: str | None = None,
) -> dict:
    instante = cuando or f"{FECHA_DE_PRUEBA} 08:00:00"
    return {
        "idhistorial": idhistorial,
        "fecha": instante[:10],
        "fechahora": instante,
        "idpartner": idpartner if idpartner is not None else ID_PARTNER_PRUEBA,
        "partner": partner,
        "idcredencial": idcredencial,
        "tipo_cambio": tipo_cambio,
        "estado_anterior": estado_anterior,
        "estado_nuevo": estado_nuevo,
        "es_cambio_efectivo": efectivo,
        "motivo": motivo,
        "cargado_en": f"{FECHA_DE_PRUEBA} 12:00:00",
    }


