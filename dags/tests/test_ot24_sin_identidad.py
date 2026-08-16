"""T069 — ningún informe de OT24 devuelve identidad de persona (FR-034).

La exclusión es constitucional: no la levanta ninguna autoridad. Y el caso
difícil es el **volumen de evidencia por unidad**, porque el catálogo lo pedía
por técnico de campo y el dato está disponible: `Dim_EvidenciaFoto` trae
`idusuario` y bastaría con copiarlo.

No se copia. Un ranking de qué persona sube menos fotos es una herramienta de
vigilancia laboral, y la pregunta que interesa —qué unidades documentan mal— se
responde igual sin nombrar a nadie.

⚠️ **Esta prueba mira el resultado, no el texto.** La del texto ya existe en
`test_catalogo_consultas.py`, y por sí sola no basta: una columna llamada
`operador` o `responsable` pasaría aquella comprobación y traería una persona.
Las dos juntas cubren el nombre y el contenido.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.almacen import requiere_modelo  # noqa: E402

from lib.consultas import cargar, listar  # noqa: E402
from lib.clickhouse_http_client import query_clickhouse  # noqa: E402

INFORMES = [n for n in listar("emergencias") if n.startswith(("ot24", "ot25"))]

#: Columnas del **origen** que identifican a una persona. Si alguna apareciera en
#: una respuesta, habría llegado copiándola de una fuente que sí la tiene.
DE_PERSONA = (
    "idusuario", "usuario", "idconductor", "conductor", "idimplicado",
    "tecnico", "operador", "responsable", "nombres", "apellidos",
    "identificacion", "gmail", "correo", "telefono",
)

#: Periodo con datos REALES, no la particion de prueba.
#:
#: Es deliberado: sobre la particion vacia la mitad de los informes no devuelve
#: ninguna fila, y una comprobacion que se salta cuando no hay filas no
#: comprueba nada. Aqui hace falta ver columnas de verdad.
PARAMETROS = {
    "desde": "2026-01-01", "hasta": "2026-12-31",
    "tramos_dias": "1,3,7,30", "umbral_seg": "60",
    "ventana_dias": "90", "muestra_minima": "5", "top": "10",
}


def ejecutar(informe: str) -> list[dict]:
    return query_clickhouse(
        cargar(informe, departamento="emergencias"),
        params={k: str(v) for k, v in PARAMETROS.items()},
    )


@requiere_modelo
class TestNingunInformeDevuelveIdentidad:
    @pytest.mark.parametrize("informe", INFORMES)
    def test_ninguna_columna_de_la_respuesta_identifica_a_una_persona(self, informe):
        filas = ejecutar(informe)
        assert filas, (
            f"'{informe}' no devolvio filas sobre datos reales: sin filas esta "
            f"comprobacion no mira ninguna columna"
        )

        for columna in filas[0]:
            bajo = columna.lower()
            for prohibida in DE_PERSONA:
                assert prohibida not in bajo, (
                    f"'{informe}' devuelve '{columna}': identidad de persona"
                )

    def test_el_volumen_se_entrega_por_unidad_y_no_por_persona(self):
        """El caso que el catálogo pedía distinto, y no se hizo.

        Se comprueba que la agrupación **es** la unidad, no solo que no hay
        columnas de persona: un informe agrupado por persona con la columna
        renombrada a `id` pasaría la comprobación anterior.
        """
        filas = ejecutar("ot24_volumen_evidencia_por_unidad")
        assert filas

        assert "idunidad" in filas[0]
        assert "proveedor" in filas[0]


@requiere_modelo
class TestElHechoTampocoLaGuarda:
    def test_hecho_evidencia_no_tiene_ninguna_columna_de_persona(self):
        """La garantía de verdad está en el esquema, no en la consulta.

        Una consulta que no pide el dato lo deja fuera hoy; una tabla que no lo
        tiene lo deja fuera siempre. Mientras la columna exista, el informe que
        la publique está a un `SELECT` de distancia.
        """
        columnas = {
            c["name"].lower()
            for c in query_clickhouse(
                "SELECT name FROM system.columns "
                "WHERE database = currentDatabase() AND table = 'hecho_evidencia'"
            )
        }

        assert columnas, "la tabla hecho_evidencia no existe"
        for prohibida in DE_PERSONA:
            coincidencias = [c for c in columnas if prohibida in c]
            assert not coincidencias, (
                f"hecho_evidencia guarda {coincidencias}: identidad de persona"
            )

    def test_tampoco_guarda_el_enlace_al_material(self):
        # `urlevidenciafoto` no es identidad, pero es una forma de sacar el
        # contenido del sistema por un informe. Tampoco entra.
        columnas = {
            c["name"].lower()
            for c in query_clickhouse(
                "SELECT name FROM system.columns "
                "WHERE database = currentDatabase() AND table = 'hecho_evidencia'"
            )
        }

        assert not [c for c in columnas if "url" in c or "enlace" in c]
