"""T109 — Hook plan/severidad es no-op (CA-DES-014 fail-open)."""

import pytest

from apps.despacho.services.consulta_candidatas_service import ConsultaCandidatasService


@pytest.mark.unit
class TestElegibilidadPlanHook:
    def test_filtrar_por_plan_severidad_returns_input_unchanged(self):
        # Arrange
        svc = ConsultaCandidatasService()
        candidatas = [
            {"idunidademergencia": 1, "tipounidademergencia": "Ambulancia"},
            {"idunidademergencia": 2, "tipounidademergencia": "Grua"},
        ]
        accidente = {"idaccidente": "ACC-1", "idseveridad": 4}

        # Act
        result = svc.filtrar_por_plan_severidad(candidatas, accidente)

        # Assert — fail-open: no filtra ni reordena hoy
        assert result is candidatas
        assert len(result) == 2
        assert result[0]["idunidademergencia"] == 1

    def test_listar_puntuadas_invokes_hook_without_changing_scores(
        self, mock_pinot, mock_kafka, accidente_activo, unidad_con_estado_activa, monkeypatch
    ):
        # Arrange
        svc = ConsultaCandidatasService()
        calls: list[tuple] = []

        original = ConsultaCandidatasService.filtrar_por_plan_severidad

        def _spy(self, candidatas, accidente):
            calls.append((list(candidatas), dict(accidente)))
            return original(self, candidatas, accidente)

        monkeypatch.setattr(
            ConsultaCandidatasService, "filtrar_por_plan_severidad", _spy
        )

        # Act
        ranked = svc.listar_puntuadas(accidente_activo)

        # Assert
        assert len(calls) == 1
        assert len(ranked) >= 1
        assert ranked[0]["puntuacion"] > 0
