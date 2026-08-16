"""T022 — los dos extremos de research D4 (User Story 1, escenario 2 · FR-023).

`Dim_Usuario_Rol` guarda **una fila por par (usuario, rol)**. Paginar sobre esa
tabla produciría los dos defectos que estas pruebas prohíben a la vez:

* un usuario con dos roles saldría **dos veces**, y sus dos filas podrían caer
  además en páginas distintas;
* un usuario **sin ningún rol** no saldría — y es precisamente la anomalía que
  el Administrador necesita ver.

Por eso se pagina `Dim_Usuarios`. Estas pruebas fijan la consecuencia observable
de esa decisión, para que un refactor que "simplifique" volviendo a la tabla de
relación falle aquí en vez de en producción.
"""

from __future__ import annotations

import pytest

from apps.cuentas_clientes.services.informes_acceso_service import InformesAccesoService


@pytest.fixture
def servicio(mock_pinot):
    return InformesAccesoService()


class TestUsuarioConDosRoles:
    def test_produce_una_sola_fila(self, servicio, usuario_multirol):
        pagina = servicio.usuarios_por_rol(limit=500)

        apariciones = [f for f in pagina.filas if f["gmail"] == "dosroles@tsi.com"]
        assert len(apariciones) == 1

    def test_esa_fila_lleva_los_dos_roles(self, servicio, usuario_multirol):
        pagina = servicio.usuarios_por_rol(limit=500)

        fila = next(f for f in pagina.filas if f["gmail"] == "dosroles@tsi.com")
        assert fila["roles"] == ["Auditor", "Revisor"]

    def test_no_se_parte_entre_dos_paginas(self, servicio, usuario_multirol):
        """El caso que la paginación sobre la relación no puede evitar."""
        from core.repositories.cuentas_clientes.informes_acceso_repository import (
            CURSOR_USUARIOS,
        )

        vistos: list[str] = []
        cursor = None
        for _ in range(20):
            pagina = servicio.usuarios_por_rol(limit=1, cursor=cursor)
            vistos.extend(f["gmail"] for f in pagina.filas)
            if pagina.cursor is None:
                break
            cursor = CURSOR_USUARIOS.decodificar(pagina.cursor)

        assert vistos.count("dosroles@tsi.com") == 1
        assert len(vistos) == len(set(vistos)), "algun usuario salio en dos paginas"


class TestUsuarioSinNingunRol:
    def test_aparece_en_el_listado(self, servicio, usuario_multirol):
        # Que desaparezca sería el fallo, no lo contrario: un usuario sin rol es
        # una cuenta con acceso y sin permisos declarados.
        pagina = servicio.usuarios_por_rol(limit=500)

        assert any(f["gmail"] == "ceroroles@tsi.com" for f in pagina.filas)

    def test_su_lista_de_roles_es_vacia_no_ausente(self, servicio, usuario_multirol):
        pagina = servicio.usuarios_por_rol(limit=500)

        fila = next(f for f in pagina.filas if f["gmail"] == "ceroroles@tsi.com")
        assert fila["roles"] == []
        assert "roles" in fila, "la clave debe estar presente aunque este vacia"


class TestFiltroPorRol:
    def test_acota_a_quienes_lo_ejercen(self, servicio, usuario_multirol):
        pagina = servicio.usuarios_por_rol(limit=500, rol="Auditor")

        assert [f["gmail"] for f in pagina.filas] == ["dosroles@tsi.com"]

    def test_la_fila_conserva_todos_sus_roles_no_solo_el_filtrado(
        self, servicio, usuario_multirol
    ):
        # Filtrar por un rol acota **qué usuarios** salen, no qué roles se ven:
        # recortarlos daría una imagen falsa de los permisos de esa persona.
        pagina = servicio.usuarios_por_rol(limit=500, rol="Auditor")

        assert pagina.filas[0]["roles"] == ["Auditor", "Revisor"]

    def test_un_rol_sin_usuarios_devuelve_vacio_no_todos(self, servicio, mock_pinot):
        from conftest import PINOT_STORE

        PINOT_STORE["Dim_Rol"].append(
            {"idrol": 95, "rol": "Vacante", "activo": True, "fecha_actualizacion": 0}
        )

        pagina = servicio.usuarios_por_rol(limit=500, rol="Vacante")

        assert pagina.filas == []
