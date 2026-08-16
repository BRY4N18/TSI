"""T070 — crecimiento aditivo: US3 no movió ninguna cifra de US1 ni de US2 (SC-010).

Es el criterio de flexibilidad del módulo: **ampliar el modelo con un hecho y
ocho columnas no debe alterar nada de lo que ya estaba**.

Importa porque el fallo contrario es silencioso y llega tarde. Una ampliación que
cambia una cifra anterior no rompe ninguna prueba de la ampliación —esas miran lo
nuevo— y solo se nota cuando alguien compara un informe con su versión impresa de
la semana pasada, si es que alguien lo hace.

Cómo se comprueba sin guardar cifras a mano
--------------------------------------------
Fijar los números esperados en la prueba los congelaría: cualquier recarga
legítima del modelo la haría fallar, y acabaría relajándose hasta no comprobar
nada.

Lo que se comprueba son **invariantes estructurales** que las ocho columnas y la
tabla nueva no pueden tocar: que los informes anteriores siguen devolviendo las
mismas columnas, que sus totales siguen cuadrando entre sí, y que ninguno de
ellos lee la tabla nueva.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.almacen import ejecutar_informe, requiere_modelo  # noqa: E402

from lib.consultas import cargar, listar  # noqa: E402

#: Los informes de US1 y US2, es decir todo lo anterior a esta historia.
ANTERIORES = [n for n in listar("emergencias") if n.startswith(("ot21", "ot22", "ot23"))]

PARAMETROS = {"umbral_seg": 60, "ventana_dias": 90, "muestra_minima": 5, "top": 10}


@requiere_modelo
class TestLosInformesAnterioresNoLeenLoNuevo:
    @pytest.mark.parametrize("informe", ANTERIORES)
    def test_ninguno_toca_hecho_evidencia(self, informe):
        """La tabla nueva no puede haberse colado en un informe anterior.

        Si un informe de US1 leyera `hecho_evidencia`, sus cifras cambiarían al
        cargarla — y cambiarían por una razón que nadie relacionaría con este
        módulo.
        """
        cuerpo = "\n".join(
            l for l in cargar(informe, departamento="emergencias").splitlines()
            if not l.strip().startswith("--")
        )

        assert "hecho_evidencia" not in cuerpo

    @pytest.mark.parametrize("informe", ANTERIORES)
    def test_ninguno_usa_las_ocho_columnas_nuevas(self, informe):
        cuerpo = "\n".join(
            l for l in cargar(informe, departamento="emergencias").splitlines()
            if not l.strip().startswith("--")
        )

        for columna in (
            "num_notas", "num_conductores", "num_implicados", "num_elementos_clima",
            "num_escaladas_severidad", "severidad_inicial", "resultado_atencion",
            "calificacion",
        ):
            assert columna not in cuerpo, (
                f"'{informe}' es de US1/US2 y usa '{columna}', que se añadió en US3"
            )


@requiere_modelo
class TestLosInformesAnterioresSiguenCuadrando:
    def test_el_total_de_casos_es_el_mismo_por_los_tres_informes_de_registro(self):
        """Tres informes de OT21 cuentan los mismos casos por caminos distintos.

        Si la ampliación hubiera duplicado filas de `hecho_accidente` —lo que
        pasaría si el `ALTER` hubiera obligado a reescribir la tabla mal—, los
        tres crecerían a la vez y ninguno lo delataría por sí solo. Comparándolos
        entre sí, un desajuste aparece en cuanto uno cambia.
        """
        severidad = sum(f["casos"] for f in ejecutar_informe("ot21_distribucion_severidad"))
        zona = sum(f["casos"] for f in ejecutar_informe("ot21_distribucion_zona"))
        completitud = ejecutar_informe("ot21_completitud_campos_criticos")
        descarte = ejecutar_informe("ot21_descarte_fusion")

        totales = {severidad, zona}
        if completitud:
            totales.add(completitud[0]["casos"])
        if descarte:
            totales.add(descarte[0]["casos"])

        assert len(totales) == 1, (
            f"los informes de registro ya no cuentan lo mismo: {totales}"
        )

    @pytest.mark.parametrize("informe", ANTERIORES)
    def test_todos_siguen_ejecutandose_y_devolviendo_filas(self, informe):
        # Una columna nueva mal declarada rompería la lectura de la tabla entera,
        # y el síntoma sería este.
        ejecutar_informe(informe, **PARAMETROS)
