import pytest

from apps.accidentes.domain_constants import ESTADO_REPORTADO
from apps.despacho.consumers.accidente_reportado_consumer import (
    AccidenteReportadoConsumer,
)
from apps.despacho.services.asignacion_inteligente_service import (
    AsignacionInteligenteService,
)
from core.repositories.accidentes.estado_accidente_repository import (
    EstadoAccidenteRepository,
)


def _evento_real_reportado(mock_kafka, idaccidente: str, idusuario: int = 2) -> dict:
    """Construye el evento tal y como lo publica el productor real, en vez de
    escribirlo a mano. El payload de `Fact_AccidenteTipoEstadoAccidente_topic`
    lleva `idtipoestadoincidente`, no el nombre del estado (B27)."""
    EstadoAccidenteRepository().append_estado(
        idaccidente=idaccidente, estado=ESTADO_REPORTADO, idusuario=idusuario
    )
    publicados = [
        m["payload"]
        for m in mock_kafka
        if m["topic"] == "Fact_AccidenteTipoEstadoAccidente_topic"
    ]
    assert publicados, "el repositorio no publicó el evento de estado"
    return publicados[-1]


@pytest.mark.service
class TestAccidenteReportadoConsumer:
    def test_handle_reconoce_el_payload_real_del_productor(
        self, mock_pinot, mock_kafka, accidente_activo, unidad_con_estado_activa
    ):
        # Arrange — el evento sale del propio repositorio, no de un dict a mano.
        evento = _evento_real_reportado(mock_kafka, accidente_activo)
        assert "estado" not in evento  # el productor real no publica el nombre
        assert evento["idtipoestadoincidente"] == 2
        consumer = AccidenteReportadoConsumer()

        # Act
        result = consumer.handle(evento)

        # Assert
        assert result is not None
        assert result["asignado"] is True
        assert result["iddespacho"] is not None

    def test_handle_no_duplica_si_el_caso_ya_tiene_despacho_activo(
        self, mock_pinot, mock_kafka, accidente_activo, unidad_con_estado_activa
    ):
        # Arrange — la entrega de Kafka es at-least-once: el mismo evento puede
        # repetirse tras un reinicio del worker, y no debe crear un segundo
        # despacho sobre un caso que ya tiene uno.
        evento = _evento_real_reportado(mock_kafka, accidente_activo)
        consumer = AccidenteReportadoConsumer()
        primero = consumer.handle(evento)

        # Act
        segundo = consumer.handle(evento)

        # Assert
        assert primero["asignado"] is True
        assert segundo["asignado"] is False
        assert segundo["motivo"] == "ya_despachado"

    def test_handle_when_reportado_triggers_asignacion(
        self, mock_pinot, mock_kafka, accidente_activo, unidad_con_estado_activa
    ):
        # Arrange
        consumer = AccidenteReportadoConsumer()

        # Act
        result = consumer.handle(
            {
                "idaccidente": accidente_activo,
                "estado": ESTADO_REPORTADO,
                "idusuario": 2,
            }
        )

        # Assert
        assert result is not None
        assert result["asignado"] is True
        assert result["iddespacho"] is not None
        assert len(mock_kafka) >= 2

    def test_handle_when_not_reportado_returns_none(self, mock_pinot, mock_kafka):
        # Arrange
        consumer = AccidenteReportadoConsumer()

        # Act
        result = consumer.handle({"idaccidente": "ACC-X", "estado": "ASIGNADO"})

        # Assert
        assert result is None

    def test_handle_when_no_candidatas_escala_a_vecinos_y_deja_constancia(
        self, mock_pinot, mock_kafka, accidente_activo, pinot_store
    ):
        # Arrange — SRS 3.6.2: sin candidatas locales, el sistema no falla en
        # silencio; escala a vecinos (ReasignacionDespachoService) y, si
        # tampoco hay ahí, deja nota + alerta admin.
        consumer = AccidenteReportadoConsumer()

        # Act
        result = consumer.handle(
            {"idaccidente": accidente_activo, "estado": ESTADO_REPORTADO, "idusuario": 2}
        )

        # Assert
        assert result is not None
        assert result["asignado"] is False
        notas = [
            n
            for n in pinot_store["Dim_NotaAccidente"]
            if n.get("idaccidente") == accidente_activo
        ]
        assert any("Sin unidades disponibles" in n.get("nota", "") for n in notas)
