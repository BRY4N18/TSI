"""T049 y T050 — las ocho métricas de enriquecimiento y cierre.

Las dos tareas tiran en direcciones opuestas y por eso van juntas en un fichero:

* Los **recuentos** van a `0` cuando el caso existe y no tiene ninguno. Cero
  notas es una medición.
* `severidad_inicial`, `resultado_atencion` y `calificacion` van **ausentes**
  cuando no se registraron.

Aplicar la regla de un bloque al otro rompe el informe en el sentido que peor se
detecta: un caso sin calificar con un `0` es el peor caso del mes, y un caso sin
notas con un ausente desaparece del recuento en vez de contar como no
documentado.

Estas pruebas son de **lógica pura**: `construir` no consulta ni escribe, así que
se le pasan los datos a mano. Es la única forma de probar esto hoy, porque cinco
de las seis fuentes están casi vacías en el origen y con datos reales una métrica
rota y una fuente vacía se ven exactamente igual.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.hechos.hecho_accidente import construir  # noqa: E402

AHORA = datetime(2026, 8, 16, 12, 0, 0, tzinfo=timezone.utc)
CASO = "ACC-1"
OTRO = "ACC-2"


def _datos(**extra):
    """Dos casos mínimos, y las fuentes que se quieran añadir."""
    base = {
        "accidentes": [
            {"idaccidente": CASO, "idseveridad": 2, "fechahoraaccidente": 1786000000000},
            {"idaccidente": OTRO, "idseveridad": 2, "fechahoraaccidente": 1786000000000},
        ],
        "estados": [],
        "despachos": [],
        "tipos": [],
        "evidencia": [],
        "notas": [],
        "conductores": [],
        "implicados": [],
        "clima": [],
        "historial_severidad": [],
        "cierres": [],
        "dim_severidad": [
            {"idseveridad": 1, "severidad": "Leve"},
            {"idseveridad": 2, "severidad": "Moderado"},
            {"idseveridad": 3, "severidad": "Grave"},
        ],
        "dim_geografia": [],
    }
    base.update(extra)
    return base


def _fila(datos, idaccidente=CASO):
    return next(f for f in construir(datos, AHORA) if f["idaccidente"] == idaccidente)


class TestLosRecuentosSonCeroYNoAusentes:
    """Cero notas es una medición: el caso existe y no tiene ninguna."""

    @pytest.mark.parametrize(
        "columna",
        ["num_notas", "num_conductores", "num_implicados", "num_elementos_clima",
         "num_escaladas_severidad"],
    )
    def test_un_caso_sin_ninguna_cuenta_cero(self, columna):
        assert _fila(_datos())[columna] == 0, (
            f"'{columna}' salió ausente en un caso que sí se midió: el informe "
            f"de completitud lo dejaría fuera en vez de contarlo como no documentado"
        )

    def test_los_recuentos_cuentan_lo_que_hay(self):
        fila = _fila(
            _datos(
                notas=[{"idaccidente": CASO}, {"idaccidente": CASO}, {"idaccidente": OTRO}],
                implicados=[{"idaccidente": CASO}],
                clima=[{"idaccidente": OTRO}],
            )
        )

        assert fila["num_notas"] == 2
        assert fila["num_implicados"] == 1
        assert fila["num_elementos_clima"] == 0

    def test_lo_de_otro_caso_no_se_le_suma(self):
        # Un fallo de agrupación daría cifras plausibles en todos los casos y
        # solo se notaría sumando el total, que nadie mira.
        datos = _datos(notas=[{"idaccidente": OTRO}] * 5)

        assert _fila(datos, CASO)["num_notas"] == 0
        assert _fila(datos, OTRO)["num_notas"] == 5


class TestLaCalificacion:
    """⚠️ El bloque opuesto: aquí el cero **no** es una medición."""

    def test_un_cierre_sin_calificar_no_es_un_cero(self):
        """Es el caso vivo hoy en el origen, no uno inventado.

        La única fila de `Fact_CierreAccidente` trae `calificacion = 0` con
        `resultado_atencion = "Cierre automático tras retiro forzado"`: nadie la
        calificó. Copiarla como `0` la convertiría en la peor nota posible.
        """
        fila = _fila(
            _datos(cierres=[{
                "idaccidente": CASO,
                "resultado_atencion": "Cierre automatico tras retiro forzado",
                "calificacion": 0,
            }])
        )

        assert fila["calificacion"] is None, (
            "una calificación de 0 se copió tal cual: un promedio que la "
            "incluyera hundiría la media y diría que la atención es mala"
        )
        assert fila["resultado_atencion"] == "Cierre automatico tras retiro forzado"

    def test_el_centinela_negativo_de_pinot_tampoco_es_una_nota(self):
        fila = _fila(
            _datos(cierres=[{"idaccidente": CASO, "calificacion": -2147483648}])
        )

        assert fila["calificacion"] is None

    def test_una_calificacion_de_verdad_se_conserva(self):
        # La comprobación simétrica: tratar todo como ausente dejaría el informe
        # de resultados permanentemente vacío, que también es una forma de estar
        # roto y bastante más difícil de notar.
        fila = _fila(_datos(cierres=[{"idaccidente": CASO, "calificacion": 4}]))

        assert fila["calificacion"] == 4

    def test_un_caso_sin_cerrar_no_tiene_resultado_ni_calificacion(self):
        fila = _fila(_datos())

        assert fila["calificacion"] is None
        assert fila["resultado_atencion"] is None

    def test_un_resultado_vacio_es_ausencia_y_no_cadena_vacia(self):
        fila = _fila(
            _datos(cierres=[{"idaccidente": CASO, "resultado_atencion": "   "}])
        )

        assert fila["resultado_atencion"] is None


class TestLaSeveridadInicial:
    def test_sin_escaladas_la_inicial_es_la_actual(self):
        """El caso no cambió de gravedad, y eso es un dato, no una ausencia.

        Dejarla ausente en los casos sin historial —que son casi todos— haría
        que el informe de escaladas no pudiera distinguir «no cambió» de «no se
        sabe».
        """
        fila = _fila(_datos())

        assert fila["severidad_inicial"] == "Moderado"
        assert fila["num_escaladas_severidad"] == 0

    def test_con_escaladas_es_la_anterior_de_la_primera(self):
        fila = _fila(
            _datos(historial_severidad=[
                {"idaccidente": CASO, "idseveridadanterior": 3,
                 "idseveridadnueva": 2, "fechahora": 2000},
                {"idaccidente": CASO, "idseveridadanterior": 1,
                 "idseveridadnueva": 3, "fechahora": 1000},
            ])
        )

        # La primera por instante es la de `fechahora = 1000`, cuya severidad
        # anterior es `1` (Leve) — no la que aparece primero en la lista.
        assert fila["severidad_inicial"] == "Leve", (
            "se tomó la escalada equivocada: el orden de llegada de las filas no "
            "es el orden en que ocurrieron"
        )
        assert fila["num_escaladas_severidad"] == 2

    def test_un_caso_sin_severidad_tampoco_tiene_inicial(self):
        datos = _datos()
        datos["accidentes"] = [
            {"idaccidente": CASO, "idseveridad": None, "fechahoraaccidente": 1786000000000}
        ]

        assert _fila(datos)["severidad_inicial"] is None


class TestLoQueNoEntraAlModelo:
    def test_el_texto_libre_de_las_fuentes_no_aparece_en_la_fila(self):
        """`motivo` y `observaciones_finales` son texto interno (FR-016).

        Las dos fuentes los traen. Que la consulta enumere columnas es lo que los
        deja fuera, y esta prueba comprueba el resultado: si alguien cambiara la
        consulta a `SELECT *`, aparecerían en la fila sin que nada más fallara.
        """
        fila = _fila(
            _datos(
                cierres=[{
                    "idaccidente": CASO,
                    "calificacion": 4,
                    "observaciones_finales": "texto interno que no debe salir",
                }],
                historial_severidad=[{
                    "idaccidente": CASO, "idseveridadanterior": 1,
                    "fechahora": 1, "motivo": "texto interno que no debe salir",
                }],
            )
        )

        assert "observaciones_finales" not in fila
        assert "motivo" not in fila
        assert "texto interno que no debe salir" not in str(fila)

    def test_ninguna_columna_de_la_fila_nombra_identidad_de_persona(self):
        fila = _fila(_datos())

        for prohibida in ("idusuario", "idconductor", "idimplicado", "nombres"):
            assert prohibida not in fila


class TestLasFuentesDelFlujoYLasDeLaLogica:
    """⚠️ La prueba que habría evitado el fallo que ocurrió de verdad.

    `extraer()` devuelve un diccionario de fuentes; `hecho_accidente_tasks.FUENTES`
    dice cuáles se guardan y se vuelven a cargar en `transform`. Añadir una
    fuente a la lógica y olvidarla en la tupla **no falla**: `construir` la
    sustituye por una lista vacía y todos los recuentos de esa fuente salen a
    **cero**.

    Y cero es un valor legítimo en esas columnas —cero notas es una medición—,
    así que el resultado es indistinguible de un origen sin datos. Pasó al
    implementar estas métricas: el modelo publicó `0` notas donde el origen tenía
    51, sin un solo error, y solo se vio comparando con el origen a mano.
    """

    def test_la_tupla_del_flujo_cubre_todas_las_fuentes_de_extraer(self):
        from lib.hecho_accidente_tasks import FUENTES
        from lib.hechos.hecho_accidente import extraer

        # Se llama a `extraer` con consultas de mentira: interesan las **claves**,
        # no los datos, y así la prueba no necesita ni Pinot ni el almacén.
        # el tercero es la lectura paginada de accidentes: sin sustituirlo,
        # este test saldria a Pinot de verdad.
        claves = set(
            extraer(lambda _sql: [], lambda _sql: [], lambda *_a, **_kw: [])
        )

        assert claves == set(FUENTES), (
            f"sobran o faltan fuentes en el flujo: {claves ^ set(FUENTES)}. "
            f"Una fuente olvidada no falla, devuelve ceros"
        )
