"""Casos de borde que los informes tacticos declaraban y los datos no tenian.

Al cerrar el repaso de la capa tactica quedaron cinco comportamientos afirmados
**solo en contrato**: la spec los describe, la prueba unitaria los cubre, y en
el navegador no habia ni una fila que los ejerciera. Este seed los siembra.

| Caso | Que demuestra |
|---|---|
| Region fuera de `Produccion` | Los cinco estados existen y **ninguno se agrupa** |
| Region `En_Alerta` | Opera **degradada**: no es `Despublicada` |
| Unidad sin condado | La fila **no se omite**; el condado se ve ausente |
| Factura `En disputa` vencida | «En disputa» **no es** «en mora» |
| Cuenta dada de baja | La baja es logica: la fila **sobrevive** en el listado |
| Demos activas | El filtro en dos pasos, con los **tres** formatos de fecha |

Dos cuidados que condicionan como esta escrito
----------------------------------------------

**1. La unidad sin condado nace `activo = false`.**
`list_candidatas_por_condado` filtra `activo = true` y cruza por condado, asi
que una unidad de baja no puede entrar nunca al algoritmo de despacho. Sembrarla
activa la dejaria con `idcondado = 0`, fuera de todo condado, y aunque hoy eso
la excluye, dependeria de un detalle de la consulta en vez de una garantia. La
composicion de flota **no filtra por `activo`**, asi que la fila se ve igual.

**2. La cuenta dada de baja es una fila NUEVA, sin usuarios.**
Marcar de baja una cuenta existente **impide iniciar sesion a su personal**
(login comprueba las cuentas del usuario desde la correccion B9 del changelog).
Un caso de borde para un informe no puede sacar gente del sistema.

Idempotente: reescribe por clave primaria (upsert), no acumula.
"""
import json
import subprocess
import time
import urllib.request
from datetime import datetime, timedelta, timezone

BROKER = "http://localhost:8099"
NOW = datetime.now(timezone.utc)
NOW_MS = int(NOW.timestamp() * 1000)
DIA_MS = 86_400_000

# ── Ids reservados para datos de borde ───────────────────────────────────────
# Se eligen por encima de lo que produce la aplicacion para que un upsert nunca
# pise una fila real. Si algun dia colisionan, la fila se sobrescribe y el dato
# de negocio se pierde: por eso van juntos aqui y no dispersos por el archivo.
REGION_DESPUBLICADA = 9101
REGION_EN_ALERTA = 9102
REGION_RECHAZADA = 9103
VALIDACION_BASE = 9100
UNIDAD_SIN_CONDADO = 9101
CLIENTE_DADO_DE_BAJA = 929001
FACTURA_EN_DISPUTA = "b0rde0001-0000-4000-8000-000000000001"
SUSCRIPCION_SUSPENDIDA = 979001
SUSCRIPCION_REACTIVADA = 979002

#: Literales canonicos, importados de donde los define el codigo y **no
#: reescritos aqui**: una spec que citaba literales inventados ya dejo listados
#: vacios respondiendo 200 sin que nadie lo notara.
ESTADO_DESPUBLICADA = "Despublicada"
ESTADO_EN_ALERTA = "En_Alerta"
ESTADO_RECHAZADA = "Rechazada"
ESTADO_FACTURA_EN_DISPUTA = "En disputa"
ESTADO_CLIENTE_BAJA = "Dado de baja"
ESTADO_SUSCRIPCION_SUSPENDIDA = "Suspendida"

#: Cliente y suscripcion reales sobre los que cuelga la factura en disputa.
CLIENTE_FACTURA = 920003
SUSCRIPCION_FACTURA = 970002


def query(sql):
    req = urllib.request.Request(
        f"{BROKER}/query/sql",
        data=json.dumps({"sql": sql}).encode(),
        headers={"Content-Type": "application/json"},
    )
    d = json.load(urllib.request.urlopen(req, timeout=60))
    if d.get("exceptions"):
        raise RuntimeError(f"Pinot: {d['exceptions']}")
    rt = d.get("resultTable")
    if not rt:
        return []
    return [dict(zip(rt["dataSchema"]["columnNames"], r)) for r in rt["rows"]]


def publish(topic, records):
    if not records:
        return
    payload = "\n".join(json.dumps(r, ensure_ascii=False) for r in records)
    proc = subprocess.run(
        [
            "docker", "exec", "-i", "kafka",
            "kafka-console-producer", "--bootstrap-server", "localhost:9092",
            "--topic", topic,
        ],
        input=payload.encode("utf-8"),
        capture_output=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"Error publicando en {topic}: {proc.stderr.decode()}")
    print(f"  -> {len(records)} registro(s) en {topic}")


# ── Red Operativa ────────────────────────────────────────────────────────────

def regiones_fuera_de_produccion():
    """Tres regiones que **no** estan en `Produccion`, una por cada matiz.

    `dias_sin_cambio` lo calcula el backend contra `fecha_actualizacion`, asi
    que las fechas van deliberadamente atrasadas: con las tres en el instante
    actual, el filtro «Detenida mas de N dias» no tendria nada que filtrar y
    seguiria sin ejercitarse, que es justo el agujero que este seed cierra.
    """
    idestado = (query("SELECT idestado FROM Dim_Estado LIMIT 1") or [{}])[0].get(
        "idestado", 1
    )
    return [
        {
            "idregionoperativa": REGION_DESPUBLICADA,
            "idestado": idestado,
            "nombreregion": "Rancho Viejo",
            "estadoregion": ESTADO_DESPUBLICADA,
            "activo": True,
            "fecha_actualizacion": NOW_MS - 120 * DIA_MS,
        },
        {
            # ⚠️ Opera con cobertura degradada. Es la region sobre la que OT13
            # puede actuar **antes** de perderla, y la que se agrupa mal con
            # `Despublicada` si nadie la ha visto nunca en pantalla.
            "idregionoperativa": REGION_EN_ALERTA,
            "idestado": idestado,
            "nombreregion": "Sierra Alta",
            "estadoregion": ESTADO_EN_ALERTA,
            "activo": True,
            "fecha_actualizacion": NOW_MS - 45 * DIA_MS,
        },
        {
            "idregionoperativa": REGION_RECHAZADA,
            "idestado": idestado,
            "nombreregion": "Valle Sur",
            "estadoregion": ESTADO_RECHAZADA,
            "activo": True,
            "fecha_actualizacion": NOW_MS - 200 * DIA_MS,
        },
    ]


def validaciones_de_la_region_rechazada():
    """Dos intentos sobre la misma region, **y el primero no se sustituye**.

    FR-005 conserva todos los intentos: el historial de por que se rechazo una
    region es lo que permite ajustar los criterios. Una region `Rechazada` sin
    ninguna validacion detras seria un estado sin causa.
    """
    idusuario = _un_usuario_activo()
    return [
        {
            "idvalidacionregion": VALIDACION_BASE + 1,
            "idregionoperativa": REGION_RECHAZADA,
            "idusuario": idusuario,
            "resultado": ESTADO_RECHAZADA,
            "motivo": "Sin unidades propias ni de proveedor en el condado",
            "fechahora": NOW_MS - 210 * DIA_MS,
            "fecha_actualizacion": NOW_MS - 210 * DIA_MS,
        },
        {
            "idvalidacionregion": VALIDACION_BASE + 2,
            "idregionoperativa": REGION_RECHAZADA,
            "idusuario": idusuario,
            "resultado": ESTADO_RECHAZADA,
            "motivo": "Segundo intento: la cobertura sigue por debajo del minimo",
            "fechahora": NOW_MS - 200 * DIA_MS,
            "fecha_actualizacion": NOW_MS - 200 * DIA_MS,
        },
    ]


def unidad_sin_condado():
    """Una unidad cuyo condado nunca se resolvio.

    Nace **de baja** a proposito: ver el cuidado 1 de la cabecera. `idcondado`
    va como `0`, que es lo que Pinot devuelve en una columna entera sin valor —
    no hay NULL— y lo que el servicio de flota no encuentra en `Dim_Condado`,
    dejando condado y estado geografico **ausentes** sin omitir la fila.
    """
    return [{
        "idunidademergencia": UNIDAD_SIN_CONDADO,
        "unidademergencia": "Grua 99 (sin condado asignado)",
        "placa": "TSI-099",
        "tipounidademergencia": "Grua",
        "capacidad": "2",
        "latitud": 0.0,
        "longitud": 0.0,
        "idcondado": 0,
        "idusuario": 0,
        "idcliente": 1,
        "tipopropiedad": "Proveedor",
        "contactoproveedor": "",
        "zonacobertura": None,
        "activo": False,
        "fecha_creacion": NOW_MS - 300 * DIA_MS,
        "fecha_actualizacion": NOW_MS,
    }]


# ── Suscripciones y Facturacion ──────────────────────────────────────────────

def factura_en_disputa():
    """Vencida hace 40 dias **y sin dias de mora**.

    Es el punto entero del caso: `ESTADOS_EN_MORA` son `Pendiente` y `Fallida`,
    y `En disputa` no esta. Una factura vencida que no acumula mora solo se
    puede leer bien si existe una; hasta ahora la regla vivia unicamente en una
    tupla del repositorio.
    """
    emision = NOW_MS - 70 * DIA_MS
    return [{
        "id_factura": FACTURA_EN_DISPUTA,
        "numero_factura": "FAC-202606-00009001",
        "id_cliente": CLIENTE_FACTURA,
        "id_suscripcion": SUSCRIPCION_FACTURA,
        "periodo": _periodo(emision),
        "tipo": "suscripcion",
        "es_nota_credito": False,
        "id_factura_original": "null",
        "desglose_cargos": json.dumps(
            [{"concepto": "Suscripcion plan Profesional", "monto": 149.0}]
        ),
        "monto_base": 149.0,
        "impuestos": 17.88,
        "monto_total": 166.88,
        "estado_pago": ESTADO_FACTURA_EN_DISPUTA,
        "idmetodopago": 3,
        "reintentos": 0,
        "resultado_ultimo_reintento": "null",
        "motivo_anulacion": "null",
        "fecha_emision": emision,
        "fecha_vencimiento": NOW_MS - 40 * DIA_MS,
        "activo": True,
        "fecha_actualizacion": NOW_MS,
    }]


def cuenta_dada_de_baja():
    """Cuenta de baja **sin personal**: ver el cuidado 2 de la cabecera.

    La baja es logica y la fila conserva su razon social y su historial. Que
    siga apareciendo en el listado no es un descuido: excluirla convertiria el
    informe de cuentas en un censo de cuentas vivas, que es otro informe.
    """
    return [{
        "idcliente": CLIENTE_DADO_DE_BAJA,
        "idprospecto": 0,
        "razon_social": "Transportes Del Litoral S.A. (baja)",
        "nombre": "Transportes Del Litoral",
        "nit_identificacion": "0999000001001",
        # ⚠️ `Corporativo`, no `Privado`. `Dim_Cliente.tipo` y
        # `Dim_Prospecto.tipo_organizacion` usan **vocabularios distintos**, y
        # copiar el del prospecto dejaba esta fila con un tipo que el filtro
        # «Tipo» no ofrece: la cuenta salia en el listado y **desaparecia** en
        # cuanto alguien filtraba por cualquier tipo. Visto en el navegador.
        "tipo": "Corporativo",
        "estado": ESTADO_CLIENTE_BAJA,
        "estado_onboarding": "Completado",
        "plan_suscripcion": "Basico",
        "logo_url": "null",
        "admin_local_id": 0,
        "fecha_inicio_contrato": NOW_MS - 500 * DIA_MS,
        "fecha_creacion": NOW_MS - 500 * DIA_MS,
        "fecha_actualizacion": NOW_MS - 30 * DIA_MS,
    }]


def suscripcion_suspendida():
    """Una suscripcion `Suspendida`, el unico estado que faltaba.

    `hecho_suscripcion` solo tenia `vigente` y `cancelada`, asi que el informe
    de suspension y reactivacion no devolvia nada. `estado_derivado` lee el
    estado del origen, de modo que basta con que exista una fila suspendida.

    Es una fila **nueva**, no el cambio de estado de una existente: suspender
    una suscripcion viva la sacaria del MRR y de la cartera, y este seed no
    debe mover cifras de negocio para llenar una pantalla.

    Se siembran **dos**: una que sigue suspendida y otra que ya volvio. Sin la
    segunda, `reactivadas` seria cero y no se distinguiria «nadie vuelve» de «el
    indicador no sabe contar vueltas» — que es como estuvo hasta el 2026-08-23,
    cuando `fecha_reactivacion` estaba fijada a `None` en el cargador.
    """
    reactivada = {
        **_suscripcion_base(SUSCRIPCION_REACTIVADA),
        "estado": "Activa",
        # El par completo: se suspendio hace 40 dias y volvio hace 12.
        "fechasuspension": NOW_MS - 40 * DIA_MS,
        "fechareactivacion": NOW_MS - 12 * DIA_MS,
    }
    suspendida = {
        **_suscripcion_base(SUSCRIPCION_SUSPENDIDA),
        "estado": ESTADO_SUSCRIPCION_SUSPENDIDA,
        "fechasuspension": NOW_MS - 25 * DIA_MS,
        # Sigue fuera: sin fecha de vuelta, y **ausente no es cero**.
        "fechareactivacion": -9223372036854775808,
    }
    return [suspendida, reactivada]


def _suscripcion_base(id_suscripcion):
    return {
        "id_suscripcion": id_suscripcion,
        "idcliente": CLIENTE_FACTURA,
        "idplan": 1,
        "nivel": "Basico",
        "precio": 49.0,
        "periodicidad": "Mensual",
        "renovacionautomatica": False,
        "fecha_inicio": NOW_MS - 200 * DIA_MS,
        "fecha_fin": NOW_MS + 30 * DIA_MS,
        "fechacancelacion": -9223372036854775808,
        "motivocancelacion": "null",
        "idplan_programado": 0,
        "severidades_desbloqueadas": "[1]",
        "carga_lote_habilitada": False,
        "activo": True,
        "fecha_actualizacion": NOW_MS,
    }


# ── Ventas y CRM ─────────────────────────────────────────────────────────────

#: ⚠️ Los **tres** formatos que `demo_tokens.py` acepta defensivamente. Sembrar
#: las tres demos con el mismo sufijo dejaria sin ejercitar justo lo que hace
#: falta filtrar en dos pasos: si el formato fuera uniforme, la comparacion
#: lexicografica en SQL bastaria y el refinamiento del servicio sobraria.
FORMATOS_EXPIRACION = (
    lambda d: d.strftime("%Y-%m-%dT%H:%M:%SZ"),
    lambda d: d.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
    lambda d: d.strftime("%Y-%m-%dT%H:%M:%S"),
)


def demos_activas():
    """Pone expiracion futura a tres prospectos.

    Se reescriben filas existentes en vez de inventar prospectos: la demo es un
    atributo del prospecto, y un prospecto nuevo solo para colgarle una demo
    ensuciaria a la vez el listado de prospectos y el embudo.

    Los tres dias son distintos —3, 9 y 21— para que el orden ascendente del
    listado (las que vencen antes, primero) se pueda comprobar mirando.

    ⚠️ **Los candidatos se eligen por id, no por «no tiene demo».**
    Filtrando `demo_expiracion IN ('', 'null')` el script dejaba de ser
    idempotente: en la segunda pasada los tres primeros ya tenian demo, elegia
    otros tres, y cada ejecucion sumaba tres demos activas mas. Ordenar por
    `idprospecto` y tomar los mismos tres hace que reejecutar **reescriba**, que
    es lo que promete la cabecera. El precio —pisar una expiracion real en uno
    de esos tres— es aceptable en un dataset de demostracion y no lo seria en
    otro sitio.
    """
    candidatos = [
        f for f in query(
            "SELECT * FROM Dim_Prospecto WHERE activo = true "
            "ORDER BY idprospecto LIMIT 50"
        )
        if f.get("idusuario") not in (None, -2147483648)
    ][:3]
    if len(candidatos) < 3:
        print(f"  ! solo hay {len(candidatos)} prospecto(s) activo(s) con ejecutivo")

    filas = []
    for prospecto, dias, formato in zip(candidatos, (3, 9, 21), FORMATOS_EXPIRACION):
        filas.append({
            **prospecto,
            "demo_expiracion": formato(NOW + timedelta(days=dias)),
            "fecha_actualizacion": NOW_MS,
        })
        print(f"     {prospecto['empresa']}: expira en {dias} dias "
              f"({filas[-1]['demo_expiracion']})")
    return filas


# ── Utilidades ───────────────────────────────────────────────────────────────

def _un_usuario_activo():
    filas = query("SELECT idusuario, activo FROM Dim_Usuarios LIMIT 10000")
    activos = sorted(f["idusuario"] for f in filas if f.get("activo"))
    if not activos:
        raise RuntimeError("No hay usuarios activos: sin autor no hay validacion")
    return activos[0]


def _periodo(ms):
    return datetime.fromtimestamp(ms / 1000, timezone.utc).strftime("%Y-%m")


def main():
    print("Red Operativa")
    publish("Dim_RegionOperativa_topic", regiones_fuera_de_produccion())
    publish("Dim_ValidacionRegion_topic", validaciones_de_la_region_rechazada())
    publish("Dim_UnidadEmergencia_topic", unidad_sin_condado())

    print("Suscripciones y Facturacion")
    publish("Fact_Factura_topic", factura_en_disputa())
    publish("Dim_Cliente_topic", cuenta_dada_de_baja())
    publish("Fact_Suscripcion_topic", suscripcion_suspendida())

    print("Ventas y CRM")
    publish("Dim_Prospecto_topic", demos_activas())

    print("\nListo. Pinot ingiere de forma asincrona: la verificacion va aparte.")


if __name__ == "__main__":
    main()
