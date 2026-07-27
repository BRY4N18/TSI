from unittest.mock import patch

import pytest

from apps.ventas_crm.tasks import run_evaluacion_reglas_demo

pytestmark = pytest.mark.service


def test_task_entrypoint_invokes_service(mock_pinot, mock_kafka):
    # Arrange / Act
    with patch(
        "apps.ventas_crm.tasks.EvaluacionReglasDemoService.run",
        return_value={"created": 0, "skipped": 0},
    ) as run:
        out = run_evaluacion_reglas_demo()
    # Assert
    assert out["created"] == 0
    run.assert_called_once()
