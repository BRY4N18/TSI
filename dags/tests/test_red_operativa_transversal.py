"""T061–T063 — las tres reglas transversales de Red Operativa.

* **Un período vacío devuelve cero filas**, no una fila de ceros (FR-023).
* **Todo porcentaje viene con su denominador** (FR-022).
* **Añadir dos dimensiones y dos hechos no movió las cifras de Emergencias**
  (SC-009) — el criterio de crecimiento aditivo.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.almacen import requiere_modelo  # noqa: E402

from lib.clickhouse_http_client import query_clickhouse  # noqa: E402
from lib.consultas import cargar, listar  # noqa: E402

DEPARTAMENTO = "red_operativa"
INFORMES = listar(DEPARTAMENTO)

#: Un período muy anterior a cualquier dato. No se escribe nada: se consulta un
#: hueco.
VACIO = {"desde": "1990-01-01", "hasta": "1990-01-02"}

EXTRA = {"umbral_unidades": "5", "top": "10", "dias_objetivo": "30"}


def texto(informe: str) -> str:
    return "\n".join(
        l for l in cargar(informe, departamento=DEPARTAMENTO).splitlines()
        if not l.strip().startswith("--")
    )


def ejecutar(informe: str, params: dict) -> list[dict]:
    return query_clickhouse(cargar(informe, departamento=DEPARTAMENTO), params=params)


def test_el_catalogo_no_esta_vacio():
    # Sin esto, todo lo de abajo recorrería una lista vacía y quedaría en verde
    # sin comprobar una sola regla.
    assert len(INFORMES) == 15, f"se esperaban 15 consultas, hay {len(INFORMES)}"


#: Informes de **corte**, exentos de la regla del periodo vacio.
#:
#: ⚠️ La exencion no es una comodidad. Un informe de corte preguntado «a fecha de
#: 1990» responde con lo que el modelo sabe a esa fecha, y las versiones de
#: dimension **abren por la izquierda** —`inicio_es_real = 0`, «hasta donde
#: sabemos, siempre fue asi»—, asi que la region aparece. No es una fila de ceros
#: inventada: es la consecuencia declarada de que el origen no historice el
#: estado, y es exactamente lo que `medida_exacta_desde` existe para avisar.
#:
#: Los informes de **periodo** si estan sujetos a la regla: ahi un cero afirma
#: que se midio y no hubo nada.
DE_CORTE = frozenset({
    "ot11_mercados_activos",
    "ot11_tiempo_puesta_operacion",
    "ot12_cobertura_flota_por_region",
    "ot12_condados_cobertura_critica",
    "ot12_pendientes_primer_acceso",
    "ot13_regiones_en_riesgo",
    "ot13_tiempo_perdida_a_despublicacion",
    "ot13_casos_activos_al_despublicar",
})


def test_lo_declarado_de_corte_existe():
    """Una entrada muerta dejaria exenta a una consulta futura con ese nombre."""
    assert DE_CORTE <= set(INFORMES), f"sobran: {sorted(DE_CORTE - set(INFORMES))}"


@requiere_modelo
@pytest.mark.parametrize("informe", sorted(set(INFORMES) - DE_CORTE))
def test_un_periodo_vacio_no_afirma_ceros(informe):
    """⚠️ Una fila con `pct: 0` **afirma que se midió y no hubo nada**.

    Una lista vacía dice que no hay nada que repartir. En un tablero con
    umbrales, un `0` es un valor que los umbrales evalúan: un porcentaje de
    cobertura a cero dispara la alarma más grave que hay, en un período en el que
    sencillamente no pasó nada.
    """
    filas = ejecutar(informe, {**VACIO, **EXTRA})

    for fila in filas:
        for columna, valor in fila.items():
            if not (columna.startswith("pct") or columna in ("ratio", "mediana_dias")):
                continue
            assert valor is None, (
                f"'{informe}' devuelve {columna} = {valor} sobre un período sin "
                f"datos: un porcentaje a cero es una alarma, y aquí no pasó nada"
            )


#: Cada porcentaje con la columna que lo produce, **declarada a mano**.
#:
#: Se declara en vez de deducirse del nombre: en Emergencias la versión que los
#: emparejaba por morfología fallaba en siete informes de veintiséis, porque en
#: español el plural del nombre no se deriva del singular del prefijo. Una regla
#: que no funciona se relaja hasta no comprobar nada; un mapa escrito a mano no
#: se relaja, y un informe nuevo sin entrada falla.
NUMERADORES = {
    "ot11_motivos_rechazo": {"pct": "rechazos"},
    "ot11_mercados_activos": {"pct": "regiones"},
    "ot11_tasa_aprobacion_primer_intento": {
        "pct_aprobacion_primer_intento": "aprobadas_al_primero"
    },
    "ot12_unidades_por_estado": {"pct_transiciones": "transiciones"},
    "ot12_disponibilidad_declarada": {"pct_disponible": "segundos_disponible"},
    "ot12_bajas_forzadas": {"pct_forzadas": "bajas"},
    "ot12_rendimiento_proveedor": {"pct_aceptacion": "confirmados"},
}

DENOMINADORES = (
    "casos", "transiciones", "unidades", "intentos", "bajas", "regiones",
    "rechazos", "despachos", "segundos_medidos", "regiones_validadas",
    "condados", "evidencias", "intervalos_medidos",
)


def columnas_de(informe: str) -> list[str]:
    return re.findall(r"\bAS\s+([A-Za-z_][A-Za-z0-9_]*)", texto(informe))


@pytest.mark.parametrize("informe", INFORMES)
def test_todo_porcentaje_va_con_su_denominador(informe):
    """Un 12,5 % sobre 8 y sobre 8 000 se leen igual y son cosas distintas.

    Y sin denominador, las tasas de un período no se pueden recomponer a partir
    de las de sus días: promediarlas da un número distinto y plausible. Es el
    obstáculo que apareció tres veces en Emergencias, en tres informes del diseño
    anterior; esta prueba impide que el catálogo nuevo lo repita.
    """
    columnas = columnas_de(informe)
    porcentajes = [c for c in columnas if c.startswith("pct") or c == "ratio"]
    if not porcentajes:
        pytest.skip(f"'{informe}' no publica ningún porcentaje")

    assert any(
        c == d or c.endswith("_" + d) or c.startswith(d)
        for c in columnas for d in DENOMINADORES
    ), f"'{informe}' publica {porcentajes} y ninguna columna que diga sobre cuántos"

    declarados = NUMERADORES.get(informe)
    assert declarados is not None, (
        f"'{informe}' publica {porcentajes} y no está en NUMERADORES: nadie "
        f"declaró qué columna produce cada tasa"
    )
    for pct in porcentajes:
        numerador = declarados.get(pct)
        assert numerador and numerador in columnas, (
            f"'{informe}' publica '{pct}' sin la columna que lo produce"
        )


def test_no_sobra_ninguna_entrada_en_el_mapa():
    assert set(NUMERADORES) <= set(INFORMES)


@requiere_modelo
class TestCrecimientoAditivo:
    """T063 — SC-009. Dos dimensiones y dos hechos nuevos, cero cifras movidas."""

    #: Lo que Red Operativa aportó al modelo.
    NUEVO = ("dim_region", "hecho_baja_unidad", "hecho_validacion_region")
    COLUMNAS_NUEVAS = ("fecha_alta", "tuvo_primer_acceso", "condados_vecinos",
                       "idregionoperativa")

    EMERGENCIAS = [n for n in listar("emergencias")]

    @pytest.mark.parametrize("informe", EMERGENCIAS)
    def test_ningun_informe_de_emergencias_toca_lo_nuevo(self, informe):
        """Si uno lo tocara, sus cifras cambiarían al cargarlo — y cambiarían por
        una razón que nadie relacionaría con Red Operativa."""
        cuerpo = "\n".join(
            l for l in cargar(informe, departamento="emergencias").splitlines()
            if not l.strip().startswith("--")
        )

        for tabla in self.NUEVO:
            assert tabla not in cuerpo, f"'{informe}' es de Emergencias y toca {tabla}"
        for columna in self.COLUMNAS_NUEVAS:
            assert columna not in cuerpo, (
                f"'{informe}' es de Emergencias y usa '{columna}', que añadió Red Operativa"
            )

    def test_los_informes_de_emergencias_siguen_cuadrando_entre_si(self):
        """Tres informes de OT21 cuentan los mismos casos por caminos distintos.

        Si la ampliación hubiera duplicado filas de `hecho_accidente`, los tres
        crecerían a la vez y ninguno lo delataría por sí solo. Comparándolos
        entre sí, un desajuste aparece en cuanto uno cambia.
        """
        p = {"desde": "2026-01-01", "hasta": "2026-12-31"}

        def total(nombre, campo):
            return sum(
                f[campo] for f in query_clickhouse(
                    cargar(nombre, departamento="emergencias"), params=p
                )
            )

        severidad = total("ot21_distribucion_severidad", "casos")
        zona = total("ot21_distribucion_zona", "casos")
        completitud = total("ot21_completitud_campos_criticos", "casos")

        assert len({severidad, zona, completitud}) == 1, (
            f"los informes de Emergencias ya no cuentan lo mismo: "
            f"{severidad}, {zona}, {completitud}"
        )

    def test_el_modelo_crecio_sin_tablas_por_informe(self):
        """15 informes de Red Operativa, **cero tablas propias**.

        Es la tesis del modelo: si cada informe hubiera traído la suya, el
        almacén tendría quince tablas más y quince flujos que mantener.
        """
        tablas = {
            t["name"] for t in query_clickhouse(
                "SELECT name FROM system.tables WHERE database = currentDatabase()"
            )
        }

        for tabla in self.NUEVO:
            assert tabla in tablas
        # Ninguna tabla con nombre de informe.
        assert not [t for t in tablas if t.startswith(("ot11_", "ot12_", "ot13_"))]
