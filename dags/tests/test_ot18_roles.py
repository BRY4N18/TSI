"""T058–T059 — política vacía de roles incompatibles (SC-007)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.almacen import (  # noqa: E402
    ID_ROL_PRUEBA,
    ID_USUARIO_PRUEBA,
    asegurar_hechos_cuentas,
    asignacion_de_prueba,
    ejecutar_cuentas,
    insertar,
    limpiar_cuentas,
    requiere_modelo,
    rol_de_prueba,
)


@pytest.fixture
def escenario():
    asegurar_hechos_cuentas()
    limpiar_cuentas()
    insertar("dim_rol", [
        rol_de_prueba(ID_ROL_PRUEBA, "Operador"),
        rol_de_prueba(ID_ROL_PRUEBA + 1, "Administrador"),
        rol_de_prueba(ID_ROL_PRUEBA + 2, "Cliente"),
    ])
    insertar("dim_usuario_rol", [
        asignacion_de_prueba(ID_USUARIO_PRUEBA, ID_ROL_PRUEBA, "Operador"),
        asignacion_de_prueba(ID_USUARIO_PRUEBA, ID_ROL_PRUEBA + 1, "Administrador"),
        asignacion_de_prueba(ID_USUARIO_PRUEBA + 1, ID_ROL_PRUEBA, "Operador"),
        asignacion_de_prueba(ID_USUARIO_PRUEBA + 1, ID_ROL_PRUEBA + 2, "Cliente"),
    ])
    yield
    limpiar_cuentas()


@requiere_modelo
class TestRolesIncompatibles:
    def test_sin_politica_cero_filas(self, escenario):
        filas = ejecutar_cuentas("ot18_roles_incompatibles", pares="")
        assert filas == [], (
            "sin pares_incompatibles el multi-rol es el mecanismo previsto"
        )

    def test_con_par_solo_esa_combinacion(self, escenario):
        filas = ejecutar_cuentas(
            "ot18_roles_incompatibles",
            pares="Operador:Administrador",
        )
        assert len(filas) == 1
        fila = filas[0]
        assert int(fila["idusuario"]) == ID_USUARIO_PRUEBA
        roles = {fila["rol_a"], fila["rol_b"]}
        assert roles == {"Operador", "Administrador"}
        assert "nombre" not in fila
        assert "correo" not in fila
