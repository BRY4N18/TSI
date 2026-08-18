"""T022 — el modelo de Cuentas no guarda token ni identidad (SC-008)."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.dimensiones.dim_usuario_organizacion import (  # noqa: E402
    CONSULTA_PERTENENCIA,
    CONSULTA_USUARIOS,
    construir as construir_org,
)
from lib.hechos.hecho_sesion import CONSULTA_SESIONES, construir as construir_sesion  # noqa: E402
from tests.almacen import requiere_modelo  # noqa: E402

from lib.clickhouse_http_client import query_clickhouse  # noqa: E402

TABLAS = (
    "dim_usuario_organizacion",
    "dim_etapa_onboarding",
    "dim_rol",
    "dim_usuario_rol",
    "hecho_sesion",
    "hecho_onboarding",
    "dim_cliente",
)

IDENTIDAD = (
    "nombre", "correo", "email", "telefono", "genero", "nacimiento",
    "identificacion", "token", "refresh_token",
)


@requiere_modelo
class TestEsquemaCuentas:
    @classmethod
    def setup_class(cls):
        from lib.ddl import ensure_modelo_analitico

        ensure_modelo_analitico()

    def test_hecho_sesion_no_tiene_token(self):
        columnas = {
            f["name"]
            for f in query_clickhouse(
                "SELECT name FROM system.columns "
                "WHERE database = currentDatabase() AND table = 'hecho_sesion'"
            )
        }
        assert "token" not in columnas
        assert "refresh_token" not in columnas
        assert "duracion_segundos" in columnas

    def test_ninguna_dimension_guarda_identidad(self):
        tablas = ", ".join(f"'{t}'" for t in TABLAS)
        columnas = query_clickhouse(
            "SELECT table, name FROM system.columns "
            f"WHERE database = currentDatabase() AND table IN ({tablas})"
        )
        for c in columnas:
            bajo = c["name"].lower()
            if c["table"] == "dim_cliente" and c["name"] == "nombre_comercial":
                continue
            if c["table"] == "dim_rol" and c["name"] in {"rol", "descripcion"}:
                continue
            for prohibida in IDENTIDAD:
                assert prohibida not in bajo, f"{c['table']}.{c['name']}"


def test_la_consulta_de_sesion_no_pide_token():
    bajo = CONSULTA_SESIONES.lower()
    assert "token" not in bajo
    assert "refresh_token" not in bajo


def test_la_pertenencia_no_sale_del_administrador():
    assert "admin_local_id" not in CONSULTA_PERTENENCIA.lower()
    assert "admin_local_id" not in CONSULTA_USUARIOS.lower()


def test_sesion_sin_cierre_deja_duracion_ausente():
    ahora = datetime(2026, 8, 17, 12, 0, 0)
    filas = construir_sesion(
        {
            "sesiones": [{
                "idsession": 1,
                "idusuario": 7,
                "navegador": "Chrome",
                "fechahorainiciosesion": "2026-08-17 10:00:00",
                "fechahoracierresesion": None,
                "estadosession": "activa",
            }],
            "pertenencia": [],
        },
        ahora,
    )
    assert filas[0]["duracion_segundos"] is None
    assert filas[0]["desenlace"] == "abierta"
    assert "token" not in filas[0]


def test_sesion_expulsada_no_es_cierre_voluntario():
    ahora = datetime(2026, 8, 17, 12, 0, 0)
    filas = construir_sesion(
        {
            "sesiones": [{
                "idsession": 2,
                "idusuario": 7,
                "navegador": None,
                "fechahorainiciosesion": "2026-08-17 10:00:00",
                "fechahoracierresesion": "2026-08-17 10:05:00",
                "estadosession": "expulsada",
            }],
            "pertenencia": [],
        },
        ahora,
    )
    assert filas[0]["desenlace"] == "expulsada"
    assert filas[0]["duracion_segundos"] == 300


def test_carga_todos_los_usuarios_no_solo_los_con_pertenencia():
    ahora = datetime(2026, 8, 17, 12, 0, 0)
    usuarios = [{"idusuario": i, "activo": True} for i in range(1, 22)]
    pertenencia = [
        {"idusuario": 1, "idcliente": 10, "activo": True},
        {"idusuario": 2, "idcliente": 11, "activo": True},
    ]
    filas = construir_org(
        {"usuarios": usuarios, "pertenencia": pertenencia},
        ahora,
    )
    assert len(filas) == 21
    assert sum(f["tiene_pertenencia"] for f in filas) == 2
    sin_org = [f for f in filas if f["tiene_pertenencia"] == 0]
    assert len(sin_org) == 19
    assert all(f["idcliente"] is None for f in sin_org)
