"""T019 — filtros, orden determinista y forma del cursor de los cuatro listados.

El orden determinista no es una preferencia de presentación: **sin él la
paginación por cursor repite o salta filas** (SC-005). Por eso cada listado
ordena por su campo declarado *más* la clave primaria como desempate, salvo
cuando el campo de orden ya es la clave.
"""

from __future__ import annotations

import pytest

from core.informes.paginacion import ASC, DESC
from core.repositories.cuentas_clientes.informes_acceso_repository import (
    CURSOR_ACCESOS,
    CURSOR_CREDENCIALES,
    CURSOR_SESIONES,
    CURSOR_USUARIOS,
    InformesAccesoRepository,
    nombre_completo,
)


@pytest.fixture
def repo(mock_pinot):
    return InformesAccesoRepository()


class TestFormaDelCursor:
    """El cursor es escalar solo cuando el campo de orden ya es clave única."""

    def test_usuarios_es_escalar_porque_idusuario_es_clave(self):
        assert CURSOR_USUARIOS.escalar is True

    def test_accesos_es_escalar(self):
        assert CURSOR_ACCESOS.escalar is True

    @pytest.mark.parametrize("cursor", [CURSOR_SESIONES, CURSOR_CREDENCIALES])
    def test_los_de_fecha_desempatan_por_clave(self, cursor):
        # Dos sesiones abiertas en el mismo milisegundo caerían del mismo lado
        # de la comparación sin el desempate, y una se perdería en el corte.
        assert cursor.escalar is False
        assert len(cursor.campos) == 2

    def test_el_desempate_es_la_clave_primaria(self):
        assert CURSOR_SESIONES.campos[1].nombre == "idsession"
        assert CURSOR_CREDENCIALES.campos[1].nombre == "idcredencial"


class TestOrdenYCursorNoPuedenDivergir:
    """Salen del mismo objeto; esta prueba fija que sigan haciéndolo."""

    def test_el_order_by_nombra_todos_los_campos_del_cursor(self):
        order_by = CURSOR_SESIONES.order_by(DESC)

        assert order_by == "fechahorainiciosesion DESC, idsession DESC"

    def test_la_direccion_del_cursor_sigue_a_la_del_orden(self):
        assert "<" in CURSOR_SESIONES.clausula(DESC)
        assert ">" in CURSOR_SESIONES.clausula(ASC)

    def test_la_clausula_compuesta_anida_el_desempate(self):
        clausula = CURSOR_CREDENCIALES.clausula(ASC)

        assert "fecha_actualizacion > %(cursor_0)s" in clausula
        assert "fecha_actualizacion = %(cursor_0)s" in clausula
        assert "idcredencial > %(cursor_1)s" in clausula


class TestUsuarios:
    def test_devuelve_una_fila_por_usuario(self, repo):
        filas = repo.usuarios(limit=50)

        ids = [f["idusuario"] for f in filas]
        assert len(ids) == len(set(ids))

    def test_orden_ascendente_por_defecto(self, repo):
        ids = [f["idusuario"] for f in repo.usuarios(limit=50)]

        assert ids == sorted(ids)

    def test_pide_una_fila_de_mas_para_detectar_la_pagina_siguiente(self, repo):
        # Es la señal de `has_next`: sin la fila sobrante habría que contar el
        # total con una segunda consulta agregada en cada petición.
        filas = repo.usuarios(limit=2)

        assert len(filas) == 3

    def test_filtra_por_activo(self, repo, mock_pinot):
        from conftest import PINOT_STORE

        PINOT_STORE["Dim_Usuarios"].append(
            {
                "idusuario": 950,
                "nombres": "Inactivo",
                "apellidos": "Prueba",
                "gmail": "inactivo@tsi.com",
                "activo": False,
                "fecha_actualizacion": 0,
            }
        )

        activos = repo.usuarios(limit=500, activo=True)
        inactivos = repo.usuarios(limit=500, activo=False)

        assert 950 not in [f["idusuario"] for f in activos]
        assert [f["idusuario"] for f in inactivos] == [950]

    def test_conjunto_vacio_no_consulta_y_devuelve_nada(self, repo):
        # Un rol sin usuarios debe dar cero filas, no todas: es la lectura
        # contraria y devolvería el padrón entero a quien filtró por nada.
        assert repo.usuarios(limit=50, idusuarios=[]) == []

    def test_el_cursor_arranca_despues_de_la_fila_indicada(self, repo):
        primera = repo.usuarios(limit=2)
        arranque = primera[1]["idusuario"]

        siguiente = repo.usuarios(limit=2, cursor=(arranque,))

        assert all(f["idusuario"] > arranque for f in siguiente)


class TestRoles:
    def test_agrupa_los_roles_por_usuario(self, repo, usuario_multirol):
        roles = repo.roles_de([900])

        assert roles[900] == ["Auditor", "Revisor"]

    def test_un_usuario_sin_roles_no_aparece_en_el_mapa(self, repo, usuario_multirol):
        # No aparecer aquí es correcto; el servicio lo traduce a `roles: []`.
        assert 901 not in repo.roles_de([900, 901])

    def test_sin_usuarios_no_consulta(self, repo):
        assert repo.roles_de([]) == {}

    def test_resuelve_usuarios_por_nombre_de_rol(self, repo, usuario_multirol):
        assert repo.idusuarios_con_rol("Auditor") == [900]

    def test_un_rol_inexistente_devuelve_conjunto_vacio(self, repo):
        assert repo.idusuarios_con_rol("NoExiste") == []

    def test_roles_disponibles_devuelve_nombres_no_identificadores(self, repo):
        disponibles = repo.roles_disponibles()

        assert all(isinstance(r, str) for r in disponibles)
        assert "Administrador" in disponibles


class TestSesiones:
    def test_solo_devuelve_las_abiertas(self, repo, sesiones_sembradas):
        ids = [f["idsession"] for f in repo.sesiones_activas(limit=500)]

        assert 5001 in ids and 5002 in ids
        assert 5003 not in ids, "la sesion cerrada no es una sesion abierta"

    def test_orden_descendente_por_defecto(self, repo, sesiones_sembradas):
        fechas = [f["fechahorainiciosesion"] for f in repo.sesiones_activas(limit=500)]

        assert fechas == sorted(fechas, reverse=True)

    def test_filtra_por_usuario(self, repo, sesiones_sembradas):
        filas = repo.sesiones_activas(limit=500, idusuario=2)

        assert all(f["idusuario"] == 2 for f in filas)

    def test_no_trae_el_token(self, repo, sesiones_sembradas):
        for fila in repo.sesiones_activas(limit=500):
            assert "token" not in fila


class TestCredenciales:
    def test_solo_las_pendientes_de_cambio(self, repo, credenciales_temporales_sembradas):
        ids = [f["idcredencial"] for f in repo.credenciales_temporales(limit=500)]

        assert set(ids) == {5101, 5102, 5103}
        assert 5104 not in ids, "una credencial activa no esta pendiente de cambio"

    def test_orden_ascendente_lo_mas_antiguo_primero(
        self, repo, credenciales_temporales_sembradas
    ):
        fechas = [
            f["fecha_actualizacion"] for f in repo.credenciales_temporales(limit=500)
        ]

        assert fechas == sorted(fechas)

    def test_no_trae_la_contrasena(self, repo, credenciales_temporales_sembradas):
        for fila in repo.credenciales_temporales(limit=500):
            assert "contrasena" not in fila


class TestAccesosTecnicos:
    def test_solo_las_cuentas_activas(self, repo, accesos_tecnicos_sembrados):
        ids = [f["idusuarioservidor"] for f in repo.accesos_tecnicos(limit=500)]

        assert set(ids) == {1, 2}

    def test_no_trae_la_contrasena(self, repo, accesos_tecnicos_sembrados):
        for fila in repo.accesos_tecnicos(limit=500):
            assert "contrasena" not in fila

    def test_resuelve_la_cadena_completa(self, repo, accesos_tecnicos_sembrados):
        roles = repo.roles_de_acceso_tecnico([1, 2])

        assert roles[1] == {
            "roles_servidor": ["sysadmin"],
            "roles_negocio": ["Administrador"],
        }

    def test_un_rol_tecnico_sin_mapeo_deja_negocio_vacio(
        self, repo, accesos_tecnicos_sembrados
    ):
        roles = repo.roles_de_acceso_tecnico([2])

        assert roles[2]["roles_servidor"] == ["despliegue"]
        assert roles[2]["roles_negocio"] == []

    def test_sin_cuentas_no_consulta(self, repo):
        assert repo.roles_de_acceso_tecnico([]) == {}


class TestNombreCompleto:
    def test_une_nombres_y_apellidos(self):
        assert nombre_completo({"nombres": "Ana", "apellidos": "Perez"}) == "Ana Perez"

    def test_con_un_solo_componente_no_deja_espacios(self):
        assert nombre_completo({"nombres": "Ana", "apellidos": None}) == "Ana"

    def test_sin_nombre_devuelve_vacio_no_el_identificador(self):
        # Mostrar el número sería exactamente lo que `design-system.md` §8
        # prohíbe, y ocurriría justo en la fila más anómala.
        assert nombre_completo({"idusuario": 42}) == ""
