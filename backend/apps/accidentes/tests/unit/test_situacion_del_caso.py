"""La situación derivada de los tres hechos del caso.

⚠️ Esta prueba protege una decisión que se tomó **en contra** de un argumento
razonable y documentado: publicar un campo derivado puede empezar a mentir el día
que cambie la garantía en la que se apoya. Se publica igualmente porque no
publicarlo dejaba al lector con `activo`, que confunde tres desenlaces en un
«No» — pero entonces la guarda de contradicción es lo que sostiene la decisión, y
es justo lo que ningún dato de hoy ejercita.
"""

from core.repositories.accidentes.informes_casos_repository import (
    SITUACION_CERRADO,
    SITUACION_DESCARTADO,
    SITUACION_DUPLICADO,
    SITUACION_EN_CURSO,
    SITUACION_INCONSISTENTE,
    situacion_de,
)


class TestSituacionDe:
    def test_activo_es_en_curso(self):
        assert (
            situacion_de(activo=True, hora_fin=None, duplicado_de=None)
            == SITUACION_EN_CURSO
        )

    def test_inactivo_con_hora_de_fin_es_cerrado(self):
        assert (
            situacion_de(activo=False, hora_fin="2026-08-13T13:08:00+00:00", duplicado_de=None)
            == SITUACION_CERRADO
        )

    def test_inactivo_sin_nada_es_descartado(self):
        # Falsa alarma: se dio de baja sin cerrarse y sin fusionarse.
        assert (
            situacion_de(activo=False, hora_fin=None, duplicado_de=None)
            == SITUACION_DESCARTADO
        )

    def test_inactivo_que_apunta_a_otro_caso_es_duplicado(self):
        assert (
            situacion_de(activo=False, hora_fin=None, duplicado_de="ACC-1")
            == SITUACION_DUPLICADO
        )

    def test_el_duplicado_gana_al_cierre_igual_que_en_el_filtro(self):
        """Un duplicado **con** hora de fin sigue siendo duplicado.

        Es la misma precedencia que aplica `_clausulas_situacion`. Si aquí
        ganara `cerrado`, la columna diría «cerrado» sobre una fila que el filtro
        `duplicado` devuelve — y el mismo hecho se contaría dos veces.
        """
        assert (
            situacion_de(activo=False, hora_fin="2026-08-13T13:08:00+00:00", duplicado_de="ACC-1")
            == SITUACION_DUPLICADO
        )

    def test_activo_con_hora_de_fin_es_inconsistente(self):
        """⚠️ El caso que justifica que el campo exista siendo derivado.

        Lo natural es mirar `activo` primero y devolver `en_curso`: una respuesta
        plausible, estable y falsa sobre un origen que se contradice.
        """
        assert (
            situacion_de(activo=True, hora_fin="2026-08-13T13:08:00+00:00", duplicado_de=None)
            == SITUACION_INCONSISTENTE
        )

    def test_activo_que_apunta_a_otro_caso_es_inconsistente(self):
        assert (
            situacion_de(activo=True, hora_fin=None, duplicado_de="ACC-1")
            == SITUACION_INCONSISTENTE
        )

    def test_toda_combinacion_tiene_situacion_y_solo_una(self):
        """La clasificación es total: ninguna fila se queda sin nombre."""
        for activo in (True, False):
            for hora_fin in (None, "2026-08-13T13:08:00+00:00"):
                for duplicado_de in (None, "ACC-1"):
                    resultado = situacion_de(
                        activo=activo, hora_fin=hora_fin, duplicado_de=duplicado_de
                    )
                    assert resultado in {
                        SITUACION_EN_CURSO,
                        SITUACION_CERRADO,
                        SITUACION_DESCARTADO,
                        SITUACION_DUPLICADO,
                        SITUACION_INCONSISTENTE,
                    }
