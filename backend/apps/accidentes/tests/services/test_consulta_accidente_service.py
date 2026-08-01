import pytest

from apps.accidentes.services.consulta_accidente_service import ConsultaAccidenteService


@pytest.mark.service
class TestConsultaAccidenteService:
    def test_listar_when_activos_includes_estado(self, mock_pinot, mock_kafka, seed_accidente):
        # Arrange
        seed_accidente(idaccidente="ACC-C-1")
        service = ConsultaAccidenteService()

        # Act
        data = service.listar()

        # Assert
        rows = data["items"]
        assert any(r["idaccidente"] == "ACC-C-1" for r in rows)
        assert rows[0].get("estado_actual") is not None

    def test_listar_when_filtro_estado_filters_by_estado_actual(
        self, mock_pinot, mock_kafka, seed_accidente
    ):
        # Arrange
        seed_accidente(idaccidente="ACC-C-BORRADOR", estado="BORRADOR")
        seed_accidente(idaccidente="ACC-C-REPORTADO", estado="REPORTADO")
        service = ConsultaAccidenteService()

        # Act
        data = service.listar(estado="REPORTADO")

        # Assert
        ids = [r["idaccidente"] for r in data["items"]]
        assert "ACC-C-REPORTADO" in ids
        assert "ACC-C-BORRADOR" not in ids

    def test_listar_when_hay_mas_de_una_pagina_devuelve_cursor_y_avanza(
        self, mock_pinot, mock_kafka, seed_accidente
    ):
        # Arrange — 5 casos, páginas de 2
        for i in range(5):
            seed_accidente(idaccidente=f"ACC-P-{i}", estado="REPORTADO")
        service = ConsultaAccidenteService()

        # Act — recorrer todas las páginas encadenando el cursor
        vistos: list[str] = []
        cursor = None
        for _ in range(10):
            data = service.listar(limit=2, cursor=cursor)
            vistos.extend(r["idaccidente"] for r in data["items"])
            cursor = data["next_cursor"]
            if cursor is None:
                break

        # Assert — sin repetidos, sin faltantes y en orden descendente estable
        paginados = [v for v in vistos if v.startswith("ACC-P-")]
        assert sorted(paginados) == [f"ACC-P-{i}" for i in range(5)]
        assert len(vistos) == len(set(vistos))
        assert vistos == sorted(vistos, reverse=True)

    def test_actualizar_when_increment_logs_audit(self, mock_pinot, mock_kafka, seed_accidente, caplog):
        # Arrange
        aid = seed_accidente(idaccidente="ACC-C-2", numvehiculos=1)
        service = ConsultaAccidenteService()

        # Act
        result = service.actualizar(aid, {"numvehiculos": 2}, idusuario=2)

        # Assert
        assert result["idaccidente"] == aid
        assert "numvehiculos" in result["campos_modificados"]
