"""Regresión: los seeds demo y el fixture E2E deben hablar de las mismas cuentas.

Convivían dos convenciones de contraseña ("Demo1234!" en `database/seed_usuarios.py`
y "password123" en `backend/scripts/`), y `e2e/fixtures/auth.fixture.ts` apuntaba a
un tercer conjunto de cuentas `@tsi.com` que solo existe como fixture en memoria de
los tests unitarios. Resultado: la misma cuenta pedía una contraseña u otra según
qué seed hubiera corrido último, y los tests E2E fallaban todos en el login.

También verifica que el valor canónico de `estadocredencial` no se separe entre el
código y los seeds: el código compara contra "Activo" y un seed escribía "ACTIVA",
lo que hacía que `onboarding_service` rechazara la credencial de todos los usuarios
sembrados.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_DIR = BACKEND_DIR.parent
SCRIPTS_DIR = BACKEND_DIR / "scripts"
FIXTURE_E2E = REPO_DIR / "e2e" / "fixtures" / "auth.fixture.ts"

sys.path.insert(0, str(SCRIPTS_DIR))


def _seeds() -> list[Path]:
    archivos = [p for p in SCRIPTS_DIR.glob("seed_*.py")]
    archivos += [p for p in (REPO_DIR / "database").glob("seed_*.py")]
    return archivos


@pytest.mark.unit
class TestCredencialesDemoConsistentes:
    def test_ningun_seed_hardcodea_una_password_distinta(self):
        # Arrange
        from _demo_seed_common import DEMO_PASSWORD

        # Act — cualquier literal que parezca contraseña y no sea la compartida
        sospechosos = []
        patron = re.compile(r'(?:PASSWORD|PASSWORD_PLAIN|DEMO_PASSWORD)\s*=\s*"([^"]+)"')
        for archivo in _seeds():
            for valor in patron.findall(archivo.read_text(encoding="utf-8")):
                if valor != DEMO_PASSWORD:
                    sospechosos.append(f"{archivo.name}: {valor!r}")

        # Assert
        assert not sospechosos, (
            "Seeds con contraseña propia en vez de DEMO_PASSWORD "
            f"(backend/scripts/_demo_seed_common.py): {sospechosos}"
        )

    def test_ningun_seed_escribe_un_estadocredencial_fuera_del_canonico(self):
        # Arrange
        from core.repositories.cuentas_clientes.credential_repository import (
            ESTADOS_CREDENCIAL,
        )

        # Act
        invalidos = []
        patron = re.compile(r'"estadocredencial":\s*"([^"]+)"')
        for archivo in _seeds():
            for valor in patron.findall(archivo.read_text(encoding="utf-8")):
                if valor not in ESTADOS_CREDENCIAL:
                    invalidos.append(f"{archivo.name}: {valor!r}")

        # Assert
        assert not invalidos, (
            f"Seeds con estadocredencial fuera de {sorted(ESTADOS_CREDENCIAL)}: {invalidos}"
        )

    def test_el_catalogo_de_roles_no_repite_nombres(self):
        # Arrange
        from _demo_seed_common import ROLES_DEMO

        # Act
        nombres = [nombre for nombre, _ in ROLES_DEMO.values()]
        repetidos = {n for n in nombres if nombres.count(n) > 1}

        # Assert — dos filas de Dim_Rol con el mismo nombre hacen que los seeds
        # resuelvan el idrol de forma no determinista.
        assert not repetidos, f"Roles duplicados en el catálogo compartido: {sorted(repetidos)}"

    def test_el_fixture_e2e_usa_cuentas_del_dominio_demo(self):
        # Arrange
        contenido = FIXTURE_E2E.read_text(encoding="utf-8")
        from _demo_seed_common import DEMO_DOMAIN

        # Act
        gmails = re.findall(r"gmail:\s*'([^']+)'", contenido)

        # Assert
        assert gmails, "El fixture E2E no declara ninguna cuenta"
        fuera = [g for g in gmails if not g.endswith(f"@{DEMO_DOMAIN}")]
        assert not fuera, (
            f"El fixture E2E apunta a cuentas fuera de @{DEMO_DOMAIN}: {fuera}. "
            "Las cuentas @tsi.com solo existen en el doble de conftest.py, no en el entorno."
        )

    def test_el_fixture_e2e_no_hardcodea_la_password(self):
        # Arrange
        contenido = FIXTURE_E2E.read_text(encoding="utf-8")

        # Act — debe referenciar la constante, no repetir el literal por cuenta
        literales = re.findall(r"password:\s*'([^']+)'", contenido)

        # Assert
        assert not literales, (
            f"El fixture E2E repite la contraseña como literal en {len(literales)} cuentas; "
            "debe usar la constante DEMO_PASSWORD para no divergir de los seeds."
        )
