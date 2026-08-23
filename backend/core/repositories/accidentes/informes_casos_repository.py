"""Consulta del listado de casos — L1 de OT21/OT25.

⛔ Ni coordenadas ni identidad de personas
-------------------------------------------
`latitudinicio` y `longitudinicio` **no están en la lista blanca**, y ninguna
tabla de conductores, implicados o vehículos se consulta desde aquí.

La constitución trata la geolocalización de accidentes y la identidad de los
implicados como dato sensible sujeto a control de acceso y auditoría propios. Un
listado táctico responde **dónde y de qué gravedad**, no *en qué coordenada
exacta ni a quién*. Un volcado paginable de coordenadas de accidentes con su
severidad es un mapa de siniestralidad exportable.

Y **la exención de la autoridad departamental no alcanza a esto** (FR-014b): es
una exclusión constitucional, no de acotamiento, y el cargo no la levanta.

⚠️ El caso no guarda su estado, pero guarda lo suficiente
----------------------------------------------------------
`Fact_Accidente` **no tiene columna de estado**. El estado formal vive en el
histórico y obtenerlo exige el último registro por caso — compuesto, y ya
cubierto por los informes agregados.

Pero tres columnas del propio caso distinguen las tres formas de quedar inactivo:

| Situación | `activo` | `horafin` | `idaccidenteorigen` |
|---|:--:|:--:|:--:|
| En curso | ✅ | — | — |
| **Cerrado** | ❌ | ✅ | — |
| **Fusionado** (duplicado) | ❌ | — | ✅ |
| **Descartado** (falsa alarma) | ❌ | — | — |

El listado devuelve **los tres hechos**, no un estado inferido: la exclusividad
entre cerrado, descartado y fusionado la garantiza el módulo de fusión, no este,
y devolver un campo calculado ataría este listado a una regla que no controla.

⚠️ `horafin` y `idaccidenteorigen` son STRING
-----------------------------------------------
No son marcas de tiempo ni enteros: son texto, con `''` y `'null'` como
centinelas de ausencia. Una guarda por nulidad sería siempre cierta —Pinot no
tiene NULL— y clasificaría **todos** los casos como cerrados.
"""

from __future__ import annotations

from typing import Any, Iterable, Sequence

from core.informes.paginacion import DESC, CampoCursor, Cursor, Orden
from core.pinot.client import PinotClient
from core.informes.catalogos import TOPE_CATALOGO, opciones_catalogo

# ⚠️ `idaccidente` es **texto** —el número de caso—, no un entero. El
# componente por defecto convierte a `int`, y con él un cursor legítimo daría
# `400` en la segunda página: el listado sería inpaginable más allá de la
# primera. El desempate compara cadenas, que es determinista — lo único que un
# cursor necesita garantizar.
CURSOR_CASOS = Cursor(
    CampoCursor("fechahoraaccidente"), CampoCursor("idaccidente", str)
)
ORDEN_CASOS = DESC  # lo reciente primero: es lo que la supervisión mira

#: **Lista blanca.** Sin `latitudinicio` ni `longitudinicio` (research D4).
#: Tampoco `descripcion`, que es el relato libre del reporte.
COLUMNAS_CASO = (
    "idaccidente",
    "idseveridad",
    "idcalle",
    "idtiporeportado",
    "idaccidenteorigen",
    "horafin",
    "activo",
    "duracionminutos",
    "numvehiculos",
    "numvictimas",
    "numheridos",
    "numfallecidos",
    "fechahoraaccidente",
)

#: Centinelas de ausencia en las columnas STRING. Pinot no tiene NULL.
SIN_VALOR = ("", "null")

#: Las cinco situaciones del filtro, derivadas de los tres hechos.
SITUACION_EN_CURSO = "en_curso"
SITUACION_CERRADO = "cerrado"
SITUACION_DUPLICADO = "duplicado"
SITUACION_DESCARTADO = "descartado"

#: ⚠️ **`borrador` NO está aquí, y la spec lo pedía.**
#:
#: `BORRADOR` es un **estado formal**: vive en el histórico de estados, igual que
#: `REPORTADO` o `ASIGNADO`, y `Fact_Accidente` no guarda ninguna columna que lo
#: distinga. Un caso en borrador es `activo = true` sin hora de fin — es decir,
#: **idéntico a cualquier otro caso en curso**.
#:
#: Implementarlo con esas dos condiciones devolvería **todos los casos activos**
#: etiquetados como «detenidos en borrador», que es peor que no ofrecerlo: una
#: respuesta con la forma correcta y el contenido equivocado.
#:
#: Obtenerlo de verdad exige el último registro del histórico por caso, que es lo
#: que FR-008 prohíbe expresamente y lo que haría de este listado un compuesto.
#: FR-002 y FR-008 se contradicen en este punto; se resuelve a favor de FR-008,
#: que es el que protege la honestidad del dato.
SITUACIONES = (
    SITUACION_EN_CURSO,
    SITUACION_CERRADO,
    SITUACION_DUPLICADO,
    SITUACION_DESCARTADO,
)


class InformesCasosRepository:
    """Solo lectura. Ningun metodo escribe ni publica en Kafka."""

    def __init__(self, pinot: PinotClient | None = None):
        self.pinot = pinot or PinotClient()

    def casos(
        self,
        *,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_CASOS,
        idcalles: Iterable[int] | None = None,
        idseveridad: int | None = None,
        idtiporeportado: int | None = None,
        situacion: str | None = None,
        desde_ms: int | None = None,
        hasta_ms: int | None = None,
    ) -> list[dict[str, Any]]:
        """Casos del período, con rango **opcional**.

        `idcalles` es el conjunto de ubicaciones contratadas. ⚠️ **Un conjunto
        vacío devuelve cero filas**, y `None` no filtra: la diferencia es todo
        el control de acceso del eje. Confundirlas daría el listado completo a
        un cliente sin zonas.
        """
        condiciones: list[str] = []
        params: dict[str, Any] = {"limit": limit + 1}

        if idcalles is not None:
            calles = sorted({int(c) for c in idcalles})
            if not calles:
                # Sin zonas contratadas: cero resultados, y **sin ir a Pinot**.
                return []
            condiciones.append("idcalle IN %(idcalles)s")
            params["idcalles"] = calles

        if idseveridad is not None:
            condiciones.append("idseveridad = %(idseveridad)s")
            params["idseveridad"] = idseveridad
        if idtiporeportado is not None:
            condiciones.append("idtiporeportado = %(idtiporeportado)s")
            params["idtiporeportado"] = idtiporeportado

        condiciones.extend(_clausulas_situacion(situacion, params))

        if desde_ms is not None:
            condiciones.append("fechahoraaccidente >= %(desde_ms)s")
            params["desde_ms"] = desde_ms
        if hasta_ms is not None:
            condiciones.append("fechahoraaccidente <= %(hasta_ms)s")
            params["hasta_ms"] = hasta_ms
        if cursor:
            condiciones.append(CURSOR_CASOS.clausula(orden))
            params.update(CURSOR_CASOS.params(cursor))

        sql = (
            f"SELECT {', '.join(COLUMNAS_CASO)} FROM Fact_Accidente"
            f"{_where(condiciones)} "
            f"ORDER BY {CURSOR_CASOS.order_by(orden)} LIMIT %(limit)s"
        )
        return self.pinot.query(sql, params)

    # ── Catalogos, resueltos por lote ────────────────────────────────────────

    def severidades(self, idseveridades: Sequence[int]) -> dict[int, str]:
        ids = _ids(idseveridades)
        if not ids:
            return {}
        filas = self.pinot.query(
            "SELECT idseveridad, severidad FROM Dim_Severidad "
            "WHERE idseveridad IN %(ids)s LIMIT %(limit)s",
            {"ids": ids, "limit": len(ids)},
        )
        return {f["idseveridad"]: f.get("severidad") for f in filas}

    def tipos_reportados(self, idtipos: Sequence[int]) -> dict[int, str]:
        ids = _ids(idtipos)
        if not ids:
            return {}
        filas = self.pinot.query(
            "SELECT idtiporeportado, tiporeportado FROM Dim_TipoReportado "
            "WHERE idtiporeportado IN %(ids)s LIMIT %(limit)s",
            {"ids": ids, "limit": len(ids)},
        )
        return {f["idtiporeportado"]: f.get("tiporeportado") for f in filas}

    def catalogo_severidades(self) -> list[dict]:
        """Severidades para el desplegable del filtro.

        No se acota por cobertura: es un catálogo de referencia del sistema, no
        dice nada sobre dónde opera nadie.
        """
        filas = self.pinot.query(
            "SELECT idseveridad, severidad FROM Dim_Severidad LIMIT %(limit)s",
            {"limit": TOPE_CATALOGO},
        )
        return opciones_catalogo(filas, "idseveridad", "severidad")

    def catalogo_tipos_reportados(self) -> list[dict]:
        """Tipos de reporte para el desplegable. Tampoco se acota."""
        filas = self.pinot.query(
            "SELECT idtiporeportado, tiporeportado FROM Dim_TipoReportado "
            "LIMIT %(limit)s",
            {"limit": TOPE_CATALOGO},
        )
        return opciones_catalogo(filas, "idtiporeportado", "tiporeportado")


#: Situación de una fila cuyos tres hechos **se contradicen** entre sí.
#:
#: ⚠️ No es un quinto estado del negocio: es la señal de que la garantía en la
#: que se apoya la derivación dejó de cumplirse.
SITUACION_INCONSISTENTE = "inconsistente"


def situacion_de(*, activo: bool, hora_fin: str | None, duplicado_de: str | None) -> str:
    """La situación de un caso a partir de sus **tres hechos**.

    Misma regla que `_clausulas_situacion`, en el otro sentido: aquella traduce
    una situación a condiciones para filtrar; esta traduce los hechos de una fila
    a su situación para mostrarla. **Las dos tienen que decir lo mismo**, y por
    eso viven juntas: separarlas es lo que dejaría que una cambiara sin la otra y
    que el filtro y la columna discreparan sin que nada fallara.

    Sobre los tres hechos la clasificación es **total y excluyente**, así que no
    hay fila sin situación ni fila con dos.

    ⚠️ **`inconsistente` no sobra.** El servicio documenta —con razón— que un
    campo derivado «empezaría a mentir el día que cambiara» la garantía de
    exclusividad, que vive en el módulo de fusión. Este es el caso: un caso
    `activo` **con** hora de fin, o `activo` apuntando a otro caso, es un origen
    que se contradice. Lo natural sería devolver `en_curso` —`activo` es lo
    primero que se mira— y esa respuesta sería plausible, estable y falsa.
    Devolver `inconsistente` convierte ese día en algo que se ve.
    """
    contradictorio = activo and (hora_fin is not None or duplicado_de is not None)
    if contradictorio:
        return SITUACION_INCONSISTENTE
    if activo:
        return SITUACION_EN_CURSO
    # El duplicado se reconoce por apuntar a otro caso **sea cual sea** su hora
    # de fin, igual que en el filtro: si no, un duplicado que conservara hora de
    # fin se contaría como cerrado y los dos conjuntos dejarían de ser disjuntos.
    if duplicado_de is not None:
        return SITUACION_DUPLICADO
    if hora_fin is not None:
        return SITUACION_CERRADO
    return SITUACION_DESCARTADO


def _clausulas_situacion(situacion: str | None, params: dict) -> list[str]:
    """Traduce una situación a condiciones sobre los **tres hechos del caso**.

    No se consulta el histórico de estados: es lo que haría de este listado un
    compuesto (research D2).
    """
    if situacion is None:
        return []

    params["sin_valor"] = list(SIN_VALOR)

    if situacion == SITUACION_EN_CURSO:
        return ["activo = true"]
    if situacion == SITUACION_CERRADO:
        # ⚠️ Se exige **además** que no apunte a otro caso. Sin esa condición, un
        # duplicado que conservara hora de fin saldría en los dos filtros, y
        # «cerrados» y «duplicados» dejarían de ser conjuntos disjuntos —
        # contando el mismo hecho dos veces.
        return [
            "activo = false",
            "horafin NOT IN %(sin_valor)s",
            "idaccidenteorigen IN %(sin_valor)s",
        ]
    if situacion == SITUACION_DUPLICADO:
        # ⚠️ El duplicado se reconoce por apuntar a otro caso, **sea cual sea**
        # su hora de fin: es lo que el caso registra sobre sí mismo.
        return ["activo = false", "idaccidenteorigen NOT IN %(sin_valor)s"]
    if situacion == SITUACION_DESCARTADO:
        # Falsa alarma: inactivo sin hora de fin **y sin** caso origen.
        return [
            "activo = false",
            "horafin IN %(sin_valor)s",
            "idaccidenteorigen IN %(sin_valor)s",
        ]

    raise ValueError(f"Situacion desconocida: '{situacion}'.")


def _ids(valores: Sequence[Any]) -> list[int]:
    return sorted({int(v) for v in valores if v is not None and int(v) > 0})


def _where(condiciones: Sequence[str]) -> str:
    return f" WHERE {' AND '.join(condiciones)}" if condiciones else ""
