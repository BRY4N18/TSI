"""T056–T057 — concurrencia por solape, no por inicios (SC-006)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.almacen import (  # noqa: E402
    ID_SESION_PRUEBA,
    ID_USUARIO_PRUEBA,
    asegurar_hechos_cuentas,
    ejecutar_cuentas,
    insertar,
    limpiar_cuentas,
    requiere_modelo,
    sesion_de_prueba,
)


def _repartidas():
    filas = []
    for i in range(10):
        minuto = f"{i * 6:02d}"
        inicio = f"2099-12-01 10:{minuto}:00"
        cierre = f"2099-12-01 10:{minuto}:59"
        filas.append(sesion_de_prueba(
            ID_SESION_PRUEBA + i,
            inicio=inicio,
            cierre=cierre,
            idusuario=ID_USUARIO_PRUEBA + i,
        ))
    return filas


def _simultaneas():
    return [
        sesion_de_prueba(
            ID_SESION_PRUEBA + 100 + i,
            inicio="2099-12-01 10:00:00",
            cierre="2099-12-01 10:01:00",
            idusuario=ID_USUARIO_PRUEBA + i,
        )
        for i in range(10)
    ]


def _manana(filas):
    return next(
        f for f in filas
        if str(f["fecha"]).startswith("2099-12-01") and f["franja"] == "manana"
    )


@requiere_modelo
class TestConcurrenciaPorSolape:
    def setup_method(self):
        asegurar_hechos_cuentas()
        limpiar_cuentas()

    def teardown_method(self):
        limpiar_cuentas()

    def test_diez_repartidas_y_diez_juntas_no_son_la_misma_carga(self):
        insertar("hecho_sesion", _repartidas())
        max_repartidas = int(_manana(ejecutar_cuentas("ot18_concurrencia_sesiones"))["concurrencia_maxima"])
        limpiar_cuentas()
        insertar("hecho_sesion", _simultaneas())
        simultaneas = _manana(ejecutar_cuentas("ot18_concurrencia_sesiones"))
        max_juntas = int(simultaneas["concurrencia_maxima"])
        iniciadas = int(simultaneas["sesiones_iniciadas"])
        assert iniciadas == 10
        assert max_repartidas == 1
        assert max_juntas == 10
        assert max_juntas != max_repartidas

    def test_declara_sesiones_sin_cierre(self):
        insertar("hecho_sesion", [
            sesion_de_prueba(
                ID_SESION_PRUEBA,
                inicio="2099-12-01 10:00:00",
                cierre="2099-12-01 10:10:00",
            ),
            sesion_de_prueba(
                ID_SESION_PRUEBA + 1,
                inicio="2099-12-01 10:20:00",
                cierre="2099-12-01 10:30:00",
            ),
            sesion_de_prueba(
                ID_SESION_PRUEBA + 2,
                inicio="2099-12-01 10:40:00",
                cierre=None,
                desenlace="abierta",
            ),
        ])
        # La abierta de 2099 no solapa el filtro (now() es 2026). Se declara
        # la columna y, con cierres, la mediana no se finge como total.
        fila = _manana(ejecutar_cuentas("ot18_concurrencia_sesiones"))
        assert "sesiones_sin_cierre" in fila
        assert fila["duracion_mediana"] is not None
        assert int(fila["sesiones_iniciadas"]) == 2
