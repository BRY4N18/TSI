import pytest

from apps.ventas_crm.services.reglas_demo_catalog import evaluar_reglas_mvp

pytestmark = pytest.mark.unit


def test_reglas_catalog_umbrales():
    # Arrange
    eventos = [
        {
            "idinteraccion": 1,
            "tipo_evento": "tiempo_seccion",
            "seccion": "precios",
            "metadata": {"duracion_ms": 300000},
        },
        {"idinteraccion": 2, "tipo_evento": "click", "seccion": "pricing", "metadata": "{}"},
        {"idinteraccion": 3, "tipo_evento": "click", "seccion": "precios", "metadata": "{}"},
        {"idinteraccion": 4, "tipo_evento": "click", "seccion": "precios", "metadata": "{}"},
    ]
    # Act
    rules = {r["regladisparada"] for r in evaluar_reglas_mvp(eventos)}
    # Assert
    assert "tiempo_seccion_precios_5min" in rules
    assert "visito_pricing_3x" in rules
