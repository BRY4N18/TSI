"""PG-SEC-005 — la entrada de un filtro no puede alterar la consulta.

**Por qué esta suite existe pese a que el código parezca correcto.** Una lectura
de `core/repositories/**` y de `core/clickhouse/client.py` dice que todo está
parametrizado: los `WHERE` usan `%(nombre)s` con un diccionario, ClickHouse liga
del lado del servidor con tipos, y el `ORDER BY` se compone de nombres de columna
que son constantes de código más un `ASC`/`DESC` derivado de un booleano.

Eso es tranquilizador y **no es suficiente**. En esta misma jornada, tres suites
que «claramente» probaban algo resultaron no medir nada
(`changelog.md` C3, C5, C6). Una lectura de código demuestra intención; solo la
ejecución demuestra comportamiento.

⚠️ **LÍMITE DE ESTA SUITE, comprobado y no supuesto.**

Estas pruebas **no demuestran que la inyección sea imposible**, y es importante no
leerlas así. El doble de Pinot de `conftest.py` no analiza SQL: hace coincidencia
de patrones sobre la cadena. Acepta igual una consulta correcta que una
inyectada, así que ninguna carga puede «funcionar» ni «fallar» de forma
observable aquí.

Se verificó introduciendo una vulnerabilidad real —hacer que `parse_dir` metiera
la entrada cruda en el `ORDER BY`— y **las 497 pruebas siguieron en verde**.

Lo que sí demuestran, que no es poco:

1. Ninguna carga produce un `500`. El `500` es el único camino que no pasa por el
   manejador central, y por tanto el único sin garantía de qué muestra.
2. Ninguna respuesta devuelve mensajes del motor de base de datos. Es lo que
   convierte un intento fallido en una guía para el siguiente.

La verificación de que la inyección **no funciona** exige motores reales y vive
en `test_inyeccion_integracion.py`, marcada `integration`.

Contrato: `contracts/respuestas-seguridad.md` §C7 (los errores no filtran).
"""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from apps.partners.domain_constants import ROL_ADMINISTRADOR
from core.jwt_utils import create_access_token
from core.seguridad.inventario_rutas import inventariar

pytestmark = [pytest.mark.api, pytest.mark.seguridad]

USUARIO = 3
SESION = 1

#: Cargas clásicas contra SQL. Se eligen por lo que revelarían si funcionaran:
#: `OR 1=1` amplía el conjunto devuelto, `--` trunca la cláusula siguiente, el
#: `UNION` extrae de otra tabla y `sleep` delata inyección ciega por tiempo.
CARGAS = [
    "1 OR 1=1",
    "1; DROP TABLE Fact_Accidente",
    "1' OR '1'='1",
    "1 UNION SELECT * FROM Dim_Usuarios",
    "' --",
    "1/**/OR/**/1=1",
    "%(limit)s",          # intento de colarse en la sustitución de parámetros
    "{param_desde:Date}",  # sintaxis de parámetro de ClickHouse
]

#: Parámetros de filtro reales, **extraídos del código** con
#: `grep query_params.get(` sobre `apps/`. La primera versión de esta suite los
#: adivinó —usaba `orden` cuando el real es `dir`— y por tanto probaba parámetros
#: que ningún endpoint lee: 83 pruebas en verde sin tocar la superficie que
#: decían cubrir. Adivinar nombres es la forma silenciosa de no probar nada.
PARAMETROS = [
    "activo", "agrupar_por", "anio", "canal", "cancelada_desde", "cancelada_hasta",
    "caso", "comparacion", "confirmar_edicion_critica", "cursor", "desde", "destino",
    "dias_aviso_expiracion", "dias_inactividad", "dir", "eje", "endpoint", "entorno",
    "estado", "estadoregion", "etapa", "etapa_actual", "frecuencia", "granularidad",
    "hasta", "id_prospecto", "id_servicio", "idcliente", "idestadosoporte", "idpartner",
    "idseveridad", "idtipounidad", "idusuario", "incluir_vecinos", "latitud", "limit",
    "longitud", "mes", "mes_cohorte", "minimo", "muestra_minima", "nivel",
    "origen", "percentil", "plan", "prioridad", "q", "regla",
    "regladisparada", "resultado", "rol", "solo_activas", "solo_activos", "solo_errores",
    "tipo", "tipo_asignacion", "tipo_cambio", "tipo_incidencia", "tipo_organizacion", "tipo_unidad",
    "tipounidademergencia", "version",
]

#: Rastros del motor de base de datos. Si aparecen, la carga llegó al motor y su
#: mensaje volvió al cliente — que es media inyección aunque la otra media falle.
RASTROS_MOTOR = (
    "QueryExecutionError", "PinotException", "brokerException",
    "DB::Exception", "Syntax error", "SQL_PARSING",
    "ILLEGAL_AGGREGATION", "UNKNOWN_IDENTIFIER",
)


def _cliente() -> APIClient:
    api = APIClient()
    api.credentials(
        HTTP_AUTHORIZATION=(
            f"Bearer {create_access_token(user_id=USUARIO, roles=[ROL_ADMINISTRADOR], session_id=SESION)}"
        )
    )
    return api


def _endpoints_de_informe():
    return [
        r for r in inventariar()
        if "informe" in r.patron and "get" in r.metodos and not r.parametros_id
    ]


RUTAS = _endpoints_de_informe()


@pytest.mark.parametrize("carga", CARGAS)
@pytest.mark.parametrize("parametro", PARAMETROS)
def test_una_carga_de_inyeccion_no_rompe_ni_filtra(parametro, carga):
    """Recorre los 70 informes con una carga en un parámetro.

    Comprueba **robustez y discreción**, no ausencia de inyección: que la carga
    no reviente el endpoint y que la respuesta no devuelva mensajes del motor.
    Ver el límite declarado en la cabecera del módulo.
    """
    cliente = _cliente()
    fallos = []

    for ruta in RUTAS:
        respuesta = cliente.get(f"/{ruta.patron}", {parametro: carga})

        if respuesta.status_code >= 500:
            fallos.append(f"{ruta.patron} -> {respuesta.status_code}")
            continue

        cuerpo = respuesta.content.decode("utf-8", errors="replace")
        delatores = [r for r in RASTROS_MOTOR if r.lower() in cuerpo.lower()]
        if delatores:
            fallos.append(f"{ruta.patron} revela {delatores}")

    assert not fallos, (
        f"Parámetro «{parametro}» con carga «{carga}»:\n  " + "\n  ".join(fallos[:10])
    )


def test_un_orden_fuera_de_la_lista_blanca_no_llega_a_la_consulta():
    """El `ORDER BY` es la superficie donde la parametrización **no** aplica.

    Un motor no admite un nombre de columna como parámetro ligado, así que ahí
    hay que validar contra lista blanca — y es fácil de olvidar precisamente
    porque el resto del `WHERE` sí está parametrizado y da sensación de estar
    cubierto.
    """
    cliente = _cliente()

    for valor in ("idaccidente; DROP TABLE x", "(SELECT 1)", "1,2,3", "gmail"):
        respuesta = cliente.get("/api/v1/informes/emergencias/casos", {"dir": valor})
        assert respuesta.status_code < 500, (valor, respuesta.status_code)

        cuerpo = respuesta.content.decode("utf-8", errors="replace")
        assert not [r for r in RASTROS_MOTOR if r.lower() in cuerpo.lower()], (
            f"dir={valor!r} produce un mensaje del motor: {cuerpo[:160]}"
        )


def test_un_limite_absurdo_no_agota_el_servidor():
    """`?limit=999999999` es la inyección del pobre: no altera la consulta, la
    hace enorme. El techo debe aplicarse en el servidor (`PG-API-005`).
    """
    cliente = _cliente()

    for valor in ("999999999", "-1", "0", "abc", "1e10"):
        respuesta = cliente.get("/api/v1/informes/emergencias/casos", {"limit": valor})
        assert respuesta.status_code < 500, (valor, respuesta.status_code)


def test_el_conteo_de_endpoints_cubiertos_no_baja():
    """Si alguien mueve un informe fuera del prefijo, esta suite dejaría de verlo.

    Sin este aserto, la cobertura se reduciría en silencio y el informe seguiría
    diciendo «todo verde» sobre un conjunto más pequeño.
    """
    assert len(RUTAS) >= 70, (
        f"Solo se ven {len(RUTAS)} endpoints de informe; la referencia son 70. "
        "Si se retiraron a propósito, actualizar el número; si no, la suite "
        "está examinando menos superficie de la que cree."
    )
