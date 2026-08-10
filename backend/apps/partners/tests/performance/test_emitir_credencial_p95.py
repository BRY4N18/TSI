"""RNF-PON-001 — p95 de la emision de credenciales <= 2 s.

Por que el umbral es tan holgado comparado con otros endpoints
--------------------------------------------------------------
La emision hace un hash bcrypt con coste 12, que tarda del orden de cientos
de milisegundos POR DISENO: es lo que encarece un ataque de fuerza bruta
contra el hash almacenado. El Tie-Breaker de la constitucion resolvio este
conflicto a favor de Security, asi que la mitigacion admisible es un umbral
generoso, nunca bajar el factor de coste.

Si este test empieza a fallar, la correccion NO es subir el umbral ni bajar
`BCRYPT_ROUNDS`: es mirar que se metio en la ruta de emision.
"""

from __future__ import annotations

import time

import pytest

from apps.partners.services.secreto_service import BCRYPT_ROUNDS
from conftest import PINOT_STORE

ID_CLIENTE_DEL_PARTNER = 1
ID_PARTNER = 970


@pytest.fixture
def partner_con_plan(mock_pinot, mock_kafka):
    PINOT_STORE["Dim_Partner"].append(
        {
            "idpartner": ID_PARTNER,
            "idcliente": ID_CLIENTE_DEL_PARTNER,
            "nombrepartner": "Demo P95",
            "contacto_tecnico_nombre": "Ana",
            "contacto_tecnico_gmail": "ana@demo.com",
            "planapi": "Profesional",
            "limitellamadasmes": 10000,
            "limitellamadasminuto": 120,
            "sandbox_activado": 0,
            "sandbox_expiracion": 0,
            "fecha_suspension": "",
            "motivo_suspension": "",
            "activo": True,
            "fecha_actualizacion": 1,
        }
    )
    return ID_PARTNER


@pytest.mark.slow
@pytest.mark.api
@pytest.mark.django_db
class TestEmitirCredencialP95:
    UMBRAL_MS = 2000
    MUESTRAS = 20

    def test_emitir_p95_bajo_umbral(self, api_client, partner_con_plan, partner_auth_headers):
        # Arrange
        duraciones_ms: list[float] = []

        # Act — cada emision usa un nombre distinto (RN-PON-014)
        for i in range(self.MUESTRAS):
            inicio = time.perf_counter()
            response = api_client.post(
                f"/api/v1/partners/{ID_PARTNER}/credenciales",
                {"nombre_credencial": f"carga-{i}", "entorno": "Sandbox"},
                format="json",
                **partner_auth_headers,
            )
            duraciones_ms.append((time.perf_counter() - inicio) * 1000)
            assert response.status_code == 201

        duraciones_ms.sort()
        indice = max(int(len(duraciones_ms) * 0.95) - 1, 0)
        p95_ms = duraciones_ms[indice]
        # Se imprime para poder registrar la evidencia en traceability.md
        # sin tener que instrumentar el test cada vez.
        print(
            f"\nRNF-PON-001 — emision de credencial: p95 = {p95_ms:.0f} ms "
            f"(mediana {duraciones_ms[len(duraciones_ms) // 2]:.0f} ms, "
            f"max {duraciones_ms[-1]:.0f} ms, n={self.MUESTRAS}, "
            f"bcrypt rounds={BCRYPT_ROUNDS}, umbral {self.UMBRAL_MS} ms)"
        )

        # Assert
        assert p95_ms <= self.UMBRAL_MS, (
            f"p95 de emision {p95_ms:.1f} ms supera el umbral {self.UMBRAL_MS} ms "
            f"(bcrypt rounds={BCRYPT_ROUNDS}). Revisar que se anadio a la ruta de "
            f"emision; NO subir el umbral ni bajar el factor de coste."
        )
