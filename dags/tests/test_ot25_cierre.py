"""T065 y T068 — la cartera de casos abiertos y la calificación ausente.

Las dos vigilan el mismo error con dos caras: **rellenar una ausencia**.

* Si `hora_cierre` se rellenara con la fecha de carga, todos los casos abiertos
  aparecerían cerrados y la cartera saldría vacía para siempre.
* Si `calificacion` ausente se contara como `0`, sería la peor nota posible y el
  promedio se hundiría con casos que nadie evaluó.

Las dos producen un informe que **funciona, no falla y miente en la dirección
tranquilizadora**: «no hay casos atrasados» y «la atención es mala» son
conclusiones que nadie cuestiona hasta que es tarde.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.almacen import (  # noqa: E402
    FECHA_DE_PRUEBA,
    cargar_casos,
    caso,
    ejecutar_informe,
    limpiar_particion,
    requiere_modelo,
)


@pytest.fixture
def particion_limpia():
    limpiar_particion()
    yield
    limpiar_particion()


def _cartera(tramos: str = "1,3,7,30") -> list[dict]:
    return ejecutar_informe("ot25_envejecimiento_cartera", tramos_dias=tramos)


def _resultados() -> dict[str, dict]:
    return {f["resultado"]: f for f in ejecutar_informe("ot25_distribucion_resultados")}


@requiere_modelo
class TestLaCarteraDeCasosAbiertos:
    def test_un_caso_abierto_aparece_en_la_cartera(self, particion_limpia):
        """⚠️ T065. Si `hora_cierre` se rellenara, esto devolvería cero siempre.

        Y devolvería cero **sin error y sin aviso**, con una lectura creíble: «no
        hay casos atrasados». El informe que avisa de los casos olvidados sería
        el primero en olvidarlos.
        """
        cargar_casos([caso("T065-abierto")])

        cartera = _cartera()

        assert cartera, "la cartera salió vacía con un caso abierto cargado"
        assert sum(f["casos_abiertos"] for f in cartera) == 1

    def test_un_caso_cerrado_no_esta_en_la_cartera(self, particion_limpia):
        cargar_casos([caso("T065-cerrado", cerrado=True), caso("T065-abierto")])

        assert sum(f["casos_abiertos"] for f in _cartera()) == 1

    def test_un_caso_descartado_no_cuenta_como_atrasado(self, particion_limpia):
        """Se decidió sobre él, aunque no tenga cierre.

        Arrastrarlo a la cartera de pendientes inflaría el atraso con trabajo ya
        resuelto, y mandaría a perseguir casos que nadie tiene que atender.
        """
        cargar_casos([
            caso("T065-descartado", descartado=True),
            caso("T065-fusionado", duplicado=True),
            caso("T065-abierto"),
        ])

        assert sum(f["casos_abiertos"] for f in _cartera()) == 1

    def test_los_tramos_reparten_por_antiguedad(self, particion_limpia):
        # Los casos de prueba son todos del mismo día, así que caen todos en el
        # mismo tramo: lo que se comprueba es que el tramo se calcula y no que
        # todos acaben en el cubo por defecto.
        cargar_casos([caso(f"T065-{i}") for i in range(3)])

        cartera = _cartera()

        assert len(cartera) == 1
        assert cartera[0]["casos_abiertos"] == 3
        assert cartera[0]["antiguedad_media_dias"] == 0.0

    def test_un_caso_mas_nuevo_que_el_primer_corte_cae_en_el_tramo_cero(self, particion_limpia):
        # Cero significa «más nuevo que el primer corte», no «cero días».
        cargar_casos([caso("T065-nuevo")])

        assert _cartera(tramos="1,3,7")[0]["tramo_dias"] == 0

    def test_los_graves_se_cuentan_aparte(self, particion_limpia):
        # Un caso grave lleva dos días abierto no es lo mismo que uno leve: la
        # cartera sin ese desglose trata igual las dos cosas.
        casos = [caso("T065-leve")]
        grave = caso("T065-grave")
        grave["severidad"] = "Grave"
        grave["idseveridad"] = 3
        cargar_casos(casos + [grave])

        assert _cartera()[0]["graves_o_fatales"] == 1


@requiere_modelo
class TestLaCalificacionAusente:
    def test_el_promedio_excluye_los_casos_sin_calificar(self, particion_limpia):
        """⚠️ T068. Un cero sería la peor nota, no «sin calificar».

        Con dos casos calificados con 4 y 5 y ocho sin calificar, el promedio es
        4,5. Si los ausentes entraran como cero sería 0,9 — y la conclusión, «la
        atención es pésima», sería exactamente la contraria de lo que dicen los
        datos.
        """
        calificados = []
        for i, nota in enumerate((4, 5)):
            c = caso(f"T068-cal-{i}", cerrado=True)
            c["resultado_atencion"] = "Atendido"
            c["calificacion"] = nota
            calificados.append(c)
        sin_calificar = []
        for i in range(8):
            c = caso(f"T068-sin-{i}", cerrado=True)
            c["resultado_atencion"] = "Atendido"
            sin_calificar.append(c)
        cargar_casos(calificados + sin_calificar)

        fila = _resultados()["Atendido"]

        assert fila["casos"] == 10
        assert fila["calificados"] == 2
        assert fila["sin_calificar"] == 8
        assert fila["calificacion_media"] == 4.5, (
            f"el promedio salió {fila['calificacion_media']}: los casos sin "
            f"calificar entraron como cero y hundieron la media"
        )

    def test_el_recuento_de_calificados_se_publica_junto_al_promedio(self, particion_limpia):
        # Un 4,8 sobre tres casos de ochocientos no dice nada de los ochocientos,
        # y sin el recuento nadie podría notarlo.
        c = caso("T068-uno", cerrado=True)
        c["resultado_atencion"] = "Atendido"
        c["calificacion"] = 5
        cargar_casos([c])

        fila = _resultados()["Atendido"]

        assert fila["calificados"] == 1
        assert fila["calificacion_media"] == 5.0

    def test_sin_ninguna_calificacion_el_promedio_es_ausente_y_no_cero(self, particion_limpia):
        c = caso("T068-sin", cerrado=True)
        c["resultado_atencion"] = "Atendido"
        cargar_casos([c])

        assert _resultados()["Atendido"]["calificacion_media"] is None


@requiere_modelo
class TestCerradoSinResultadoNoEsSinCerrar:
    def test_son_dos_grupos_distintos(self, particion_limpia):
        """Un caso cerrado sin resultado registrado **está cerrado**.

        La versión obvia de la consulta —agrupar por el resultado y llamar «sin
        cerrar» a lo que no lo tiene— pondría hoy 3635 casos cerrados en el grupo
        de los abiertos. El informe diría que casi nada se ha terminado cuando lo
        que pasa es que casi nada se documentó al terminar: dos problemas con dos
        responsables distintos.
        """
        cerrado_sin_resultado = caso("T025-cerrado", cerrado=True)
        abierto = caso("T025-abierto")
        cargar_casos([cerrado_sin_resultado, abierto])

        resultados = _resultados()

        assert resultados["Cerrado sin resultado registrado"]["casos"] == 1
        assert resultados["Sin cerrar"]["casos"] == 1
