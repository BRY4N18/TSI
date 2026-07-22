"""Flujo end-to-end: registro → ciclo de vida → cierre → reapertura (quickstart A/C/G).

Marker `service` (no `integration`, reservado para infra real vía docker-compose;
ver decisión ya documentada en test_registro_ticket_integration.py y tasks.md T025).
"""

from __future__ import annotations

import pytest

from apps.soporte_cliente.services.confirmar_cierre_service import ConfirmarCierreService
from apps.soporte_cliente.services.reabrir_ticket_service import ReabrirTicketService
from apps.soporte_cliente.services.registrar_ticket_service import RegistrarTicketService
from apps.soporte_cliente.services.resolver_ticket_service import ResolverTicketService
from apps.soporte_cliente.services.tomar_ticket_service import TomarTicketService
from core.repositories.soporte.historial_ticket_repository import HistorialTicketRepository


@pytest.mark.service
class TestFlujoCompletoTicketIntegration:
    def test_registro_tomar_resolver_confirmar_reabrir(self, mock_pinot, mock_kafka):
        # Arrange / Act — registro (Escenario 1)
        reclamo = RegistrarTicketService().registrar(
            idcliente=1,
            asunto="La API no responde",
            descripcion="error 500 constante desde hace 1 hora",
            tipo="tecnico",
            idusuario=3,
        )
        assert reclamo["estado"] == "Abierto"
        assert reclamo["sla_status"] == "en curso"

        # Act — ciclo de vida (Escenario 3)
        tomado = TomarTicketService().tomar(reclamo["id_reclamo"], id_agente_asignado=10)
        assert tomado["estado_nuevo"] == "En_progreso"

        resuelto = ResolverTicketService().resolver(reclamo["id_reclamo"], idusuario=10)
        assert resuelto["estado_nuevo"] == "Resuelto"
        assert resuelto["sla_status"] == "cumplido"

        cerrado = ConfirmarCierreService().confirmar(reclamo["id_reclamo"], idusuario=3)
        assert cerrado["estado_nuevo"] == "Cerrado"
        assert cerrado["cierreconfirmadocliente"] is True

        # Act — reapertura con renovación de SLA (Escenario 7 + clarificación)
        reabierto = ReabrirTicketService().reabrir(
            reclamo["id_reclamo"], idusuario=3, motivo="La solución no funcionó"
        )
        assert reabierto["estado_nuevo"] == "Reabierto"
        assert reabierto["sla_status"] == "en curso"

        # Assert — historial completo conservado (RNF-TIC-002 insert-only)
        historial = HistorialTicketRepository().list_by_ticket(reclamo["id_reclamo"])
        acciones = [h["tipo_accion"] for h in historial]
        assert acciones == [
            "creacion",
            "asignacion_agente",
            "resolucion",
            "cierre_confirmado",
            "reapertura",
        ]
