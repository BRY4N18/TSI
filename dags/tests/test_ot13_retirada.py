"""T057–T060 — la retirada de regiones, y las tres formas de leerla al revés.

1. **Despublicar una región no reescribe su pasado** (SC-010). Un informe de
   marzo tiene que seguir diciendo lo que decía en marzo.
2. **Un histórico vacío no es «nunca pasó»** (SC-011), es «no lo vimos». Las dos
   se ven igual y la primera es tranquilizadora.
3. **Una región sin despublicar no tardó cero días** (FR-035). Un cero sería la
   mejor marca posible para la peor situación.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.base_propia import base_propia, vaciar  # noqa: F401,E402
from tests.almacen import ejecutar_red_operativa, requiere_modelo  # noqa: E402

from lib.clickhouse_http_client import execute_clickhouse, query_clickhouse  # noqa: E402

REGION = 9601
ANTES = "2026-03-15 00:00:00"
DESPUES = "2026-09-01 00:00:00"


def _version(sk: int, estado: str, desde: str, hasta: str | None, *,
             vigente: int, inicio_real: int) -> dict:
    return {
        "sk_region": sk,
        "idregionoperativa": REGION,
        "nombre_region": "Region T057",
        "estado_ciclo_vida": estado,
        "idestado_geo": None,
        "estado_geo": None,
        "pais": None,
        "valido_desde": desde,
        "valido_hasta": hasta,
        "es_vigente": vigente,
        "inicio_es_real": inicio_real,
        "version": "2026-09-01 12:00:00",
    }


def _insertar(filas: list[dict]) -> None:
    payload = "\n".join(json.dumps(f, ensure_ascii=False) for f in filas)
    execute_clickhouse(f"INSERT INTO dim_region FORMAT JSONEachRow\n{payload}")


@pytest.fixture
def limpio(base_propia):  # noqa: F811
    """⚠️ **Base propia, y no es cosmético.**

    `borrar()` solo quita la región de prueba, así que estas pruebas convivían
    con las regiones reales. Pasaban **por accidente**: ninguna llevaba
    `inicio_es_real = 1` —el cargador no lo producía— y por eso
    «despublicaciones medidas» siempre daba 0.

    El 2026-08-23 el origen empezó a sellar el instante del cambio de estado
    (`region_operativa_repository`), una región real pasó a tener su
    despublicación fechada, y el contador subió a 1 sin que nada se hubiera
    roto. Sobre una base vacía la prueba vuelve a medir lo que dice medir.
    """
    def borrar():
        execute_clickhouse(
            f"ALTER TABLE dim_region DELETE WHERE idregionoperativa = {REGION} "
            f"SETTINGS mutations_sync = 2"
        )
    borrar()
    yield
    borrar()


def _riesgo(hasta: str, umbral: int = 5) -> dict:
    filas = [
        f for f in query_clickhouse(
            _sql("ot13_regiones_en_riesgo"),
            params={"desde": "2026-01-01", "hasta": hasta, "umbral_unidades": str(umbral)},
        )
        if f["idregion"] == REGION
    ]
    return filas[0] if filas else {}


def _sql(nombre: str) -> str:
    from lib.consultas import cargar

    return cargar(nombre, departamento="red_operativa")


@requiere_modelo
class TestElPasadoDeLaRegionNoSeReescribe:
    """T057 — SC-010. Es la razón de que `dim_region` esté versionada."""

    def test_despublicarla_hoy_no_la_saca_del_informe_de_marzo(self, limpio):
        """⚠️ Y el informe de marzo es la evidencia de que el riesgo se veía venir.

        Si el estado se leyera de la versión actual, despublicar una región
        borraría de golpe todos los informes de riesgo que la señalaban — es
        decir, desaparecería la prueba de que alguien lo advirtió a tiempo.
        """
        _insertar([
            _version(1, "Producción", "2026-01-01 00:00:00", DESPUES,
                     vigente=0, inicio_real=0),
            _version(2, "Despublicada", DESPUES, None, vigente=1, inicio_real=1),
        ])

        en_marzo = _riesgo("2026-03-31")
        hoy = _riesgo("2026-12-31")

        assert en_marzo, "la región desapareció del informe de marzo al despublicarla hoy"
        assert en_marzo["estado_ciclo_vida"] == "Producción"
        assert not hoy, "una región despublicada no está en riesgo: ya se retiró"

    def test_una_region_despublicada_no_cuenta_como_en_riesgo(self, limpio):
        # El riesgo ya se materializó. Volver a señalarla es ruido sobre una
        # decisión ya tomada, y el informe de riesgo se lee para actuar.
        _insertar([_version(1, "Despublicada", "2026-01-01 00:00:00", None,
                            vigente=1, inicio_real=1)])

        assert not _riesgo("2026-12-31")

    def test_una_region_en_validacion_tampoco_esta_en_riesgo(self, limpio):
        """Todavía no opera: es normal que no tenga unidades.

        Meterla aquí llenaría la lista de falsas alarmas con las regiones que
        están haciendo lo correcto, y la lista dejaría de mirarse.
        """
        _insertar([_version(1, "En validación", "2026-01-01 00:00:00", None,
                            vigente=1, inicio_real=0)])

        assert not _riesgo("2026-12-31")


@requiere_modelo
class TestUnaRegionConCoberturaNoEstaEnRiesgo:
    """T060 — la comprobación simétrica."""

    def test_el_umbral_decide_y_viaja_en_la_respuesta(self, limpio):
        _insertar([_version(1, "Producción", "2026-01-01 00:00:00", None,
                            vigente=1, inicio_real=0)])

        # Con umbral 0 nadie está por debajo: ninguna región aparece.
        assert not _riesgo("2026-12-31", umbral=0)
        # Con umbral 5 y cero unidades, sí.
        fila = _riesgo("2026-12-31", umbral=5)
        assert fila["umbral_aplicado"] == 5
        assert fila["unidades_faltantes"] == 5


@requiere_modelo
class TestElTiempoHastaDespublicar:
    """T059 — FR-035. Sin despublicar no es «despublicada en cero días»."""

    def _tiempo(self) -> dict:
        return ejecutar_red_operativa("ot13_tiempo_perdida_a_despublicacion")[0]

    def test_una_region_sin_despublicar_no_entra_en_el_calculo(self, limpio):
        """⚠️ Un cero la pondría a la cabeza de las reacciones más rápidas.

        Y es justo la región que sigue publicada sin cobertura — el caso que este
        informe existe para encontrar.
        """
        _insertar([_version(1, "Producción", "2026-01-01 00:00:00", None,
                            vigente=1, inicio_real=0)])

        fila = self._tiempo()

        assert fila["despublicaciones_medidas"] == 0
        assert fila["mediana_dias"] is None, (
            f"la mediana salió {fila['mediana_dias']}: una región sin despublicar "
            f"entró en el cálculo como cero días"
        )

    def test_aparece_en_el_recuento_de_las_que_siguen_publicadas_sin_flota(self, limpio):
        # La alarma contraria: aquella mide reacción, esta mide inacción.
        _insertar([_version(1, "Producción", "2026-01-01 00:00:00", None,
                            vigente=1, inicio_real=0)])

        assert self._tiempo()["aun_publicadas_sin_flota"] >= 1

    def test_una_despublicacion_observada_si_se_mide(self, limpio):
        """La comprobación simétrica: un informe que devolviera siempre ausente
        pasaría las dos anteriores y estaría igual de roto."""
        _insertar([
            _version(1, "Producción", "2026-01-01 00:00:00", DESPUES,
                     vigente=0, inicio_real=0),
            _version(2, "Despublicada", DESPUES, None, vigente=1, inicio_real=1),
        ])

        fila = self._tiempo()

        assert fila["despublicaciones_medidas"] >= 1
        assert fila["mediana_dias"] is not None

    def test_una_version_que_abre_por_la_izquierda_no_fecha_la_despublicacion(self, limpio):
        """⚠️ `inicio_es_real = 0` dice «ya estaba así cuando empezamos a mirar».

        Restar contra esa fecha daría cincuenta y seis años, y el informe de
        reacción diría que se tardó medio siglo en retirar una región.

        ⚠️ La región **tiene que haber estado en producción** para que esta
        prueba comprometa algo. La primera versión que escribí solo tenía la
        versión despublicada, y entonces `publicada_en` salía nulo y el resultado
        era ausente **por otra razón**: la prueba pasaba aunque se quitara la
        guarda de `inicio_es_real`. Lo destapó una mutación.
        """
        _insertar([
            _version(1, "Producción", "1970-01-01 00:00:00", "2026-05-01 00:00:00",
                     vigente=0, inicio_real=0),
            _version(2, "Despublicada", "2026-05-01 00:00:00", None,
                     vigente=1, inicio_real=0),
        ])

        fila = self._tiempo()

        assert fila["despublicaciones_medidas"] == 0
        assert fila["mediana_dias"] is None


@requiere_modelo
class TestLaMedidaExacta:
    """T058 — SC-011. Sin esto, un histórico vacío se lee como «nunca pasó»."""

    def test_el_denominador_se_publica_aunque_valga_cero(self, limpio):
        """Es lo que convierte una tabla vacía en una tabla que dice algo.

        «0 días de media» sin el recuento sería un elogio; con
        `despublicaciones_medidas = 0` al lado, se lee como lo que es: no se ha
        medido ninguna.
        """
        _insertar([_version(1, "Producción", "2026-01-01 00:00:00", None,
                            vigente=1, inicio_real=0)])

        fila = ejecutar_red_operativa("ot13_tiempo_perdida_a_despublicacion")[0]

        assert "despublicaciones_medidas" in fila
        assert fila["despublicaciones_medidas"] == 0

    def test_casos_activos_devuelve_vacio_y_no_una_fila_de_ceros(self, limpio):
        """Sin despublicaciones observadas no hay nada que informar.

        Una fila con `casos_activos: 0` afirmaría que se despublicó una región y
        no había casos abiertos — una buena noticia que nadie ha comprobado.
        """
        _insertar([_version(1, "Producción", "2026-01-01 00:00:00", None,
                            vigente=1, inicio_real=0)])

        assert ejecutar_red_operativa("ot13_casos_activos_al_despublicar") == []

    def test_el_endpoint_declara_los_tres_como_dependientes_del_versionado(self):
        """La lista de la vista es lo que hace llegar el aviso a quien consulta.

        Un informe que dependa del versionado y no esté en ella devolvería su
        cifra **sin decir desde cuándo es exacta**, que es el fallo que este
        campo existe para evitar.
        """
        fuente = (
            Path(__file__).resolve().parents[2]
            / "backend" / "apps" / "informes_tacticos" / "views"
            / "red_operativa_compuestos_views.py"
        )
        if not fuente.exists():
            pytest.skip("el backend no está montado en este contenedor")

        texto = fuente.read_text(encoding="utf-8")
        for informe in (
            "tiempo-perdida-a-despublicacion",
            "casos-activos-al-despublicar",
            "regiones-en-riesgo",
        ):
            assert informe in texto
