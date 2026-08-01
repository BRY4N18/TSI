"""Regresión: el doble en memoria de Pinot no puede divergir del esquema real.

`conftest.PINOT_STORE` simula Apache Pinot en los tests. Si contiene tablas que
no existen en `database/esquemas.json`, la suite pasa al 100% mientras el
endpoint real revienta con `TableDoesNotExistError` — exactamente lo que ocurrió
con `Dim_Usuario_Cliente` y `Dim_CondadoVecino`: los tests de contrato daban
verde y `GET /api/v1/cliente/expedientes` respondía 500 en producción.

Este test cierra esa clase de fallo comparando ambos inventarios. También revisa
el camino inverso: una tabla consultada por código productivo que nadie declaró.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_DIR = BACKEND_DIR.parent
ESQUEMAS = REPO_DIR / "database" / "esquemas.json"

# Tablas que el doble puede tener sin estar en el esquema: son auxiliares de
# prueba, no entidades de dominio. Mantener esta lista vacía es lo deseable;
# cada entrada debe justificar por qué no corresponde a una tabla real.
TABLAS_SOLO_DEL_DOBLE: frozenset[str] = frozenset()


def _tablas_declaradas() -> set[str]:
    esquemas = json.loads(ESQUEMAS.read_text(encoding="utf-8"))
    return {e["schemaName"] for e in esquemas}


def _tablas_del_doble() -> set[str]:
    from conftest import _INITIAL_PINOT_STORE

    return set(_INITIAL_PINOT_STORE)


def _tablas_consultadas_por_el_codigo() -> set[str]:
    """Nombres que aparecen tras FROM/JOIN en el código productivo."""
    patron = re.compile(r"\b(?:FROM|JOIN)\s+([A-Za-z_][A-Za-z0-9_]*)", re.IGNORECASE)
    encontradas: set[str] = set()
    for raiz in ("apps", "core"):
        for archivo in (BACKEND_DIR / raiz).rglob("*.py"):
            ruta = archivo.as_posix()
            if "__pycache__" in ruta or "/tests/" in ruta:
                continue
            for nombre in patron.findall(archivo.read_text(encoding="utf-8")):
                # Las tablas del dominio son Dim_* / Fact_*; el resto son alias
                # y palabras sueltas del SQL.
                if nombre.startswith(("Dim_", "Fact_")):
                    encontradas.add(nombre)
    return encontradas


@pytest.mark.unit
class TestDoblePinotVsEsquemas:
    def test_toda_tabla_del_doble_existe_en_esquemas_json(self):
        # Act
        sobrantes = _tablas_del_doble() - _tablas_declaradas() - TABLAS_SOLO_DEL_DOBLE

        # Assert
        assert not sobrantes, (
            "El doble de Pinot simula tablas que no existen en database/esquemas.json: "
            f"{sorted(sobrantes)}. Los tests pasarían mientras el endpoint real "
            "falla con TableDoesNotExistError. Declarar la tabla o quitarla del doble."
        )

    def test_toda_tabla_consultada_por_el_codigo_esta_declarada(self):
        # Act
        declaradas = _tablas_declaradas()
        sin_declarar = {t for t in _tablas_consultadas_por_el_codigo() if t not in declaradas}

        # Assert
        assert not sin_declarar, (
            "Código productivo consulta tablas no declaradas en database/esquemas.json: "
            f"{sorted(sin_declarar)}. En el entorno real responden TableDoesNotExistError."
        )

    def test_el_doble_cubre_las_tablas_que_el_codigo_consulta(self):
        # Arrange — si el código la consulta y el esquema la declara, el doble
        # debe poder responderla o los tests de ese camino no prueban nada.
        declaradas = _tablas_declaradas()
        consultadas = {t for t in _tablas_consultadas_por_el_codigo() if t in declaradas}

        # Act
        faltantes = consultadas - _tablas_del_doble()

        # Assert
        assert not faltantes, (
            "Tablas reales que el código consulta y el doble no simula: "
            f"{sorted(faltantes)}. Agregarlas a _INITIAL_PINOT_STORE en conftest.py."
        )
