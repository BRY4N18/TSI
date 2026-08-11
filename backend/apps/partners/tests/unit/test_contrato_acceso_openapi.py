"""Gate del contrato OpenAPI de #09 (T003).

Contract-first: si el contrato se rompe o filtra secretos, el gate cae antes de
que nadie mire la implementacion.

El invariante que mas importa: **`client_secret` solo puede aparecer en
`RevocacionResponse`**. Si apareciera en `Credencial`, el endpoint de estado de
acceso —que lista todas las credenciales del partner— filtraria secretos en cada
consulta.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.unit

CONTRATO = (
    Path(__file__).resolve().parents[4].parent
    / "specs/003-operational/Partners-API/partner-access-management/backend"
    / "contracts/partner-access-management.openapi.yaml"
)


@pytest.fixture(scope="module")
def contrato() -> dict:
    if not CONTRATO.exists():  # pragma: no cover - guarda de ruta
        pytest.skip(f"Contrato no encontrado en {CONTRATO}")
    return yaml.safe_load(CONTRATO.read_text(encoding="utf-8"))


class TestEstructura:
    def test_declara_los_cinco_endpoints(self, contrato):
        assert set(contrato["paths"]) == {
            "/credenciales/{idcredencial}/revocar",
            "/partners/{idpartner}/suspender",
            "/partners/{idpartner}/reactivar",
            "/partners/{idpartner}/estado-acceso",
            "/partners/cola-acceso",
        }

    def test_no_hay_referencias_rotas(self, contrato):
        """Un `$ref` a un schema inexistente rompe cualquier generador."""
        # Arrange
        definidos = set(contrato["components"]["schemas"])
        definidos |= {f"responses/{r}" for r in contrato["components"].get("responses", {})}
        definidos |= {f"parameters/{p}" for p in contrato["components"].get("parameters", {})}

        # Act
        rotos = []

        def _revisar(nodo):
            if isinstance(nodo, dict):
                for clave, valor in nodo.items():
                    if clave == "$ref" and isinstance(valor, str):
                        destino = valor.replace("#/components/", "")
                        seccion, _, nombre = destino.partition("/")
                        clave_esperada = (
                            nombre if seccion == "schemas" else f"{seccion}/{nombre}"
                        )
                        if clave_esperada not in definidos:
                            rotos.append(valor)
                    else:
                        _revisar(valor)
            elif isinstance(nodo, list):
                for item in nodo:
                    _revisar(item)

        _revisar(contrato)

        # Assert
        assert rotos == []


class TestSeguridad:
    def test_todos_los_endpoints_exigen_bearerAuth(self, contrato):
        """Ninguno acepta credencial de API: si se pudiera revocar con una
        credencial, el atacante que ya robó una podría revocar las demás."""
        for ruta, operaciones in contrato["paths"].items():
            for metodo, operacion in operaciones.items():
                assert operacion.get("security") == [{"bearerAuth": []}], (
                    f"{metodo.upper()} {ruta} no exige bearerAuth"
                )

    def test_el_secreto_solo_aparece_en_RevocacionResponse(self, contrato):
        """🎯 El invariante de seguridad del contrato."""
        # Act
        con_secreto = [
            nombre
            for nombre, definicion in contrato["components"]["schemas"].items()
            if "client_secret" in str(definicion)
        ]

        # Assert
        assert con_secreto == ["RevocacionResponse"]

    def test_el_schema_Credencial_no_expone_el_secreto(self, contrato):
        """Es el que usa la consulta de estado, que lista TODAS las del partner."""
        propiedades = contrato["components"]["schemas"]["Credencial"]["properties"]
        assert "client_secret" not in propiedades
        assert "client_secret_hash" not in propiedades
