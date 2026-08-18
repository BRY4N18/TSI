"""Tareas del flujo de dimensiones (T019).

Viven aquí y no en el fichero del DAG por la misma razón que las de los tres
flujos anteriores: así otro DAG puede reutilizarlas sin importar un fichero de
DAG desde otro fichero de DAG.

**Este flujo debe correr antes que cualquier flujo de hechos.** No es una
preferencia de orden: los hechos copian severidad, condado y proveedor **desde
las dimensiones ya cargadas**, y sin ellas cargarían esas columnas vacías.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from lib.clickhouse_http_client import insert_rows, query_clickhouse
from lib.ddl import ensure_modelo_analitico
from lib.dimensiones import (
    dim_canal,
    dim_cliente,
    dim_condado_vecino,
    dim_estado_soporte,
    dim_etapa_onboarding,
    dim_geografia,
    dim_credencial_api,
    dim_origen_despacho,
    dim_partner,
    dim_plan,
    dim_prospecto,
    dim_region,
    dim_rol,
    dim_servicio,
    dim_severidad,
    dim_sla_config,
    dim_tiempo,
    dim_unidad,
    dim_usuario_organizacion,
    dim_version_contrato,
)
from lib.dimensiones.desconocido import FILAS_DESCONOCIDAS
from lib.etl_modelo import cargar, guardar, ruta
from lib.hechos.comun import a_datetime
from lib.pinot_http_client import query_pinot
from lib.tipos_almacen import ajustar_tipos

FLUJO = "dimensiones"

#: Margen del calendario alrededor de los datos observados. Genera días que aún
#: no tienen actividad **a propósito**: un informe del mes en curso debe poder
#: mostrar sus días vacíos como vacíos, no como ausentes.
MARGEN_DIAS = 400

#: ⚠️ `dim_region` entra en **este** flujo y no en uno propio. Un flujo por
#: dimensión es el mismo error que un flujo por informe: multiplica la plomería y
#: garantiza que unas dimensiones se carguen sin las otras, con lo que un hecho
#: puede acabar apuntando a una versión que todavía no existe.
DIMENSIONES = (
    "dim_tiempo", "dim_geografia", "dim_severidad", "dim_origen_despacho",
    "dim_unidad", "dim_region", "dim_canal", "dim_prospecto",
    "dim_condado_vecino", "dim_plan", "dim_cliente",
    "dim_sla_config", "dim_servicio", "dim_estado_soporte",
    "dim_usuario_organizacion", "dim_etapa_onboarding",
    "dim_rol", "dim_usuario_rol",
    "dim_partner", "dim_credencial_api", "dim_version_contrato",
)


def _prefijo(nombre: str) -> str:
    return f"{FLUJO}_{nombre}_"


def _ahora() -> datetime:
    return datetime.now(tz=timezone.utc).replace(tzinfo=None, microsecond=0)


def extract(ts: str, **_) -> None:
    """Trae los catálogos del origen y las versiones de unidad ya cargadas."""
    ensure_modelo_analitico()

    catalogos = dim_geografia.extraer()
    for nombre, filas in catalogos.items():
        guardar(filas, ruta(ts, "extract", _prefijo(nombre)))

    guardar(dim_severidad.extraer(), ruta(ts, "extract", _prefijo("severidad")))
    guardar(dim_origen_despacho.extraer(), ruta(ts, "extract", _prefijo("origen")))

    for nombre, filas in dim_condado_vecino.extraer().items():
        guardar(filas, ruta(ts, "extract", _prefijo(f"vecino_{nombre}")))

    guardar(dim_prospecto.extraer(), ruta(ts, "extract", _prefijo("prospectos")))
    guardar(dim_plan.extraer(), ruta(ts, "extract", _prefijo("planes")))
    guardar(dim_sla_config.extraer(), ruta(ts, "extract", _prefijo("sla_config")))
    guardar(dim_servicio.extraer(), ruta(ts, "extract", _prefijo("servicios")))
    guardar(dim_estado_soporte.extraer(), ruta(ts, "extract", _prefijo("estados_soporte")))
    catalogo_clientes = dim_cliente.extraer()
    guardar(catalogo_clientes["clientes"], ruta(ts, "extract", _prefijo("clientes_dim")))
    guardar(catalogo_clientes["metodos"], ruta(ts, "extract", _prefijo("metodos_pago")))
    guardar(catalogo_clientes.get("onboarding", []), ruta(ts, "extract", _prefijo("onboarding_dim")))

    pertenencia = dim_usuario_organizacion.extraer()
    guardar(pertenencia["usuarios"], ruta(ts, "extract", _prefijo("usuarios_org")))
    guardar(pertenencia["pertenencia"], ruta(ts, "extract", _prefijo("pertenencia_org")))

    roles = dim_rol.extraer()
    guardar(roles["roles"], ruta(ts, "extract", _prefijo("roles")))
    guardar(roles["asignaciones"], ruta(ts, "extract", _prefijo("usuario_rol")))

    guardar(dim_partner.extraer(), ruta(ts, "extract", _prefijo("partners")))
    creds = dim_credencial_api.extraer()
    guardar(creds["credenciales"], ruta(ts, "extract", _prefijo("credenciales_api")))
    guardar(creds["bitacora"], ruta(ts, "extract", _prefijo("bitacora_acceso")))
    versiones_contrato = dim_version_contrato.extraer()
    guardar(versiones_contrato["versiones"], ruta(ts, "extract", _prefijo("versiones_contrato")))

    for nombre, filas in dim_region.extraer().items():
        guardar(filas, ruta(ts, "extract", _prefijo(f"region_{nombre}")))

    unidades, clientes, condados, vigentes, credenciales, unidad_usuario = dim_unidad.extraer()
    guardar(unidades, ruta(ts, "extract", _prefijo("unidades")))
    guardar(clientes, ruta(ts, "extract", _prefijo("clientes")))
    guardar(condados, ruta(ts, "extract", _prefijo("condados_unidad")))
    guardar(vigentes, ruta(ts, "extract", _prefijo("vigentes")))
    guardar(credenciales, ruta(ts, "extract", _prefijo("credenciales")))
    guardar(unidad_usuario, ruta(ts, "extract", _prefijo("unidad_usuario")))

    # El rango del calendario sale de los datos, no de una constante: así el
    # modelo no depende de que alguien recuerde ampliarlo cada año.
    rango = query_pinot(
        "SELECT MIN(fechahoraaccidente) AS minimo, MAX(fechahoraaccidente) AS maximo "
        "FROM Fact_Accidente LIMIT 1"
    )
    guardar(rango, ruta(ts, "extract", _prefijo("rango")))


def transform(ts: str, **_) -> None:
    ahora = _ahora()

    def leido(nombre):
        return cargar(ruta(ts, "extract", _prefijo(nombre)))

    rango = leido("rango")
    minimo = a_datetime(rango[0].get("minimo")) if rango else None
    maximo = a_datetime(rango[0].get("maximo")) if rango else None
    desde = (minimo or ahora).date()
    hasta = (maximo or ahora).date()
    guardar(
        dim_tiempo.generar(desde, hasta + timedelta(days=MARGEN_DIAS), ahora),
        ruta(ts, "transform", _prefijo("dim_tiempo")),
    )

    # ⚠️ Los nombres salen de `dim_geografia.CONSULTAS`, **no de una lista a
    # mano**. Con una lista fija, anadir un catalogo al modulo de logica y
    # olvidarlo aqui **no falla**: `construir` lo sustituye por una lista vacia.
    #
    # Paso exactamente eso con `vecinos`: el `extract` lo guardaba y el
    # `transform` no lo leia, asi que todos los condados salieron **sin vecinos
    # declarados** — que en el informe de cobertura critica es la marca de «sin
    # alternativas», la situacion mas grave que reporta. Un olvido de lectura se
    # habria publicado como una emergencia operativa, y sin un solo error.
    catalogos = {n: leido(n) for n in dim_geografia.CONSULTAS}
    guardar(
        dim_geografia.construir(catalogos, ahora) + [FILAS_DESCONOCIDAS["dim_geografia"](ahora)],
        ruta(ts, "transform", _prefijo("dim_geografia")),
    )
    guardar(
        dim_severidad.construir(leido("severidad"), ahora)
        + [FILAS_DESCONOCIDAS["dim_severidad"](ahora)],
        ruta(ts, "transform", _prefijo("dim_severidad")),
    )
    guardar(
        dim_origen_despacho.construir(leido("origen"), ahora)
        + [FILAS_DESCONOCIDAS["dim_origen_despacho"](ahora)],
        ruta(ts, "transform", _prefijo("dim_origen_despacho")),
    )
    guardar(
        dim_condado_vecino.construir(leido("vecino_vecinos"), leido("vecino_condados"), ahora)
        + [FILAS_DESCONOCIDAS["dim_condado_vecino"](ahora)],
        ruta(ts, "transform", _prefijo("dim_condado_vecino")),
    )

    versiones = dim_unidad.construir(
        leido("unidades"), leido("clientes"), leido("condados_unidad"), leido("vigentes"), ahora,
        leido("credenciales"), leido("unidad_usuario"),
    )
    # La fila desconocida solo se escribe si aún no está: es fija, y reescribirla
    # en cada corrida ensuciaría la tabla con versiones idénticas.
    if not leido("vigentes"):
        versiones.append(FILAS_DESCONOCIDAS["dim_unidad"](ahora))
    guardar(versiones, ruta(ts, "transform", _prefijo("dim_unidad")))

    # ⚠️ `dim_canal` primero: `dim_prospecto` necesita sus identificadores para
    # resolver el canal de cada prospecto. Al reves, todos caerian en la fila
    # desconocida y el informe por canal saldria entero bajo «Desconocido».
    canales = dim_canal.construir(leido("prospectos"), ahora)
    guardar(
        canales + [FILAS_DESCONOCIDAS["dim_canal"](ahora)],
        ruta(ts, "transform", _prefijo("dim_canal")),
    )
    guardar(
        dim_prospecto.construir(leido("prospectos"), canales, ahora),
        ruta(ts, "transform", _prefijo("dim_prospecto")),
    )
    guardar(
        dim_plan.construir(leido("planes"), ahora)
        + [FILAS_DESCONOCIDAS["dim_plan"](ahora)],
        ruta(ts, "transform", _prefijo("dim_plan")),
    )
    guardar(
        dim_cliente.construir(
            {
                "clientes": leido("clientes_dim"),
                "metodos": leido("metodos_pago"),
                "onboarding": leido("onboarding_dim"),
            },
            ahora,
        )
        + [FILAS_DESCONOCIDAS["dim_cliente"](ahora)],
        ruta(ts, "transform", _prefijo("dim_cliente")),
    )
    guardar(
        dim_usuario_organizacion.construir(
            {"usuarios": leido("usuarios_org"), "pertenencia": leido("pertenencia_org")},
            ahora,
        ),
        ruta(ts, "transform", _prefijo("dim_usuario_organizacion")),
    )
    guardar(
        dim_etapa_onboarding.construir([], ahora),
        ruta(ts, "transform", _prefijo("dim_etapa_onboarding")),
    )
    guardar(
        dim_rol.construir_roles(leido("roles"), ahora),
        ruta(ts, "transform", _prefijo("dim_rol")),
    )
    guardar(
        dim_rol.construir_asignaciones(leido("usuario_rol"), leido("roles"), ahora),
        ruta(ts, "transform", _prefijo("dim_usuario_rol")),
    )
    guardar(
        dim_sla_config.construir(leido("sla_config"), ahora),
        ruta(ts, "transform", _prefijo("dim_sla_config")),
    )
    guardar(
        dim_servicio.construir(leido("servicios"), ahora),
        ruta(ts, "transform", _prefijo("dim_servicio")),
    )
    guardar(
        dim_estado_soporte.construir(leido("estados_soporte"), ahora),
        ruta(ts, "transform", _prefijo("dim_estado_soporte")),
    )
    guardar(
        dim_partner.construir(leido("partners"), ahora)
        + [FILAS_DESCONOCIDAS["dim_partner"](ahora)],
        ruta(ts, "transform", _prefijo("dim_partner")),
    )
    guardar(
        dim_credencial_api.construir(
            {"credenciales": leido("credenciales_api"), "bitacora": leido("bitacora_acceso")},
            ahora,
        ),
        ruta(ts, "transform", _prefijo("dim_credencial_api")),
    )
    guardar(
        dim_version_contrato.construir(
            {"versiones": leido("versiones_contrato"), "servicios": leido("servicios")},
            ahora,
        ),
        ruta(ts, "transform", _prefijo("dim_version_contrato")),
    )

    versiones_region = dim_region.construir(
        leido("region_regiones"), leido("region_estados_geo"),
        leido("region_relacion_geo"), leido("region_vigentes"), ahora,
    )
    if not leido("region_vigentes"):
        versiones_region.append(FILAS_DESCONOCIDAS["dim_region"](ahora))
    guardar(versiones_region, ruta(ts, "transform", _prefijo("dim_region")))


def load(ts: str, **_) -> None:
    """Inserta las dimensiones.

    Sin descarte de partición: las dimensiones no están particionadas y el motor
    deduplica por clave. Lo que sí importa es que **una versión cerrada y su
    sustituta se escriben juntas**, para que no exista un instante con dos
    versiones vigentes de la misma unidad.
    """
    for nombre in DIMENSIONES:
        filas = cargar(ruta(ts, "transform", _prefijo(nombre)))
        if filas:
            insert_rows(nombre, ajustar_tipos(nombre, filas))

    # Una dimensión vacía no rompe la carga del hecho —caería en la fila
    # desconocida— pero dejaría **todas** sus columnas desnormalizadas en blanco,
    # que es un fallo silencioso. Mejor detenerse aquí.
    vacias = [
        d for d in DIMENSIONES
        if int(query_clickhouse(f"SELECT count() AS n FROM {d}")[0]["n"]) == 0
    ]
    if vacias:
        raise RuntimeError(f"dimensiones vacías tras la carga: {vacias}")
