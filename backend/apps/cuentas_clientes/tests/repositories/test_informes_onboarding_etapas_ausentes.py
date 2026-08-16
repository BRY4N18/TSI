"""T034 — una etapa sin registro no genera fila, y eso es **intencional**.

`Fact_Onboarding` guarda una fila por etapa **iniciada**. No está garantizado
que exista fila para las etapas que aún no han empezado, así que un cliente
recién aprobado no aparece en el listado hasta que empieza su incorporación.

Research D6 lo decidió así: inferir las etapas ausentes exigiría cruzar con un
catálogo de etapas esperadas y calcular la diferencia — una operación de
conjunto que empujaría el listado hacia lo compuesto. Y la pregunta real del
Administrador, «¿quién está detenido y dónde?», ya la responde una fila
pendiente: quien no ha empezado no se ha detenido en ninguna parte.

Esta prueba existe para que ese comportamiento quede **fijado como decisión** y
no como accidente. Sin ella, alguien que note la ausencia podría "arreglarla" y
convertir el listado en compuesto sin darse cuenta de que rompe el contrato.
"""

from __future__ import annotations

import pytest

from conftest import PINOT_STORE
from core.repositories.cuentas_clientes.cliente_repository import (
    ESTADO_CLIENTE_ACTIVO,
)
from core.repositories.cuentas_clientes.informes_incorporacion_repository import (
    InformesIncorporacionRepository,
)
from apps.cuentas_clientes.tests.conftest import BASE_MS


@pytest.fixture
def cliente_sin_ninguna_etapa(mock_pinot):
    """Cliente aprobado que todavía no tiene ninguna fila de incorporación."""
    PINOT_STORE["Dim_Cliente"].append(
        {
            "idcliente": 7900,
            "razon_social": "Recien Aprobada S.A.",
            "tipo": "Corporativo",
            "estado": ESTADO_CLIENTE_ACTIVO,
            "fecha_creacion": BASE_MS,
            "fecha_actualizacion": BASE_MS,
        }
    )
    return 7900


class TestEtapasNoIniciadas:
    def test_un_cliente_sin_ninguna_etapa_no_aparece(
        self, mock_pinot, cliente_sin_ninguna_etapa
    ):
        repo = InformesIncorporacionRepository()

        filas = repo.etapas_pendientes(limit=500)

        assert cliente_sin_ninguna_etapa not in [f["id_cliente"] for f in filas]

    def test_no_se_inventa_una_fila_por_cada_etapa_del_catalogo(
        self, mock_pinot, onboarding_sembrado, cliente_sin_ninguna_etapa
    ):
        # Si el listado infiriera las etapas ausentes, este cliente aparecería
        # con una fila por cada etapa conocida.
        repo = InformesIncorporacionRepository()

        filas = repo.etapas_pendientes(limit=500)

        assert len(filas) == 2, (
            "solo las dos etapas pendientes CON registro; ninguna inferida"
        )

    def test_aparece_en_cuanto_empieza_una_etapa(
        self, mock_pinot, cliente_sin_ninguna_etapa
    ):
        """La contrapartida: nada más iniciarse, ya es visible."""
        PINOT_STORE["Fact_Onboarding"].append(
            {
                "id_onboarding": 7901,
                "id_cliente": cliente_sin_ninguna_etapa,
                "etapa": "verificacion_documental",
                "completado": False,
                "fecha_actualizacion": BASE_MS,
            }
        )

        filas = InformesIncorporacionRepository().etapas_pendientes(limit=500)

        assert cliente_sin_ninguna_etapa in [f["id_cliente"] for f in filas]
