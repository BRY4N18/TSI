import pytest

from apps.ventas_crm.services.consulta_planes_publicos_service import (
    ConsultaPlanesPublicosService,
    _parse_severidades,
)


@pytest.mark.service
def test_parse_severidades_acepta_json_string_y_lista():
    # Arrange / Act / Assert
    assert _parse_severidades("[1, 2]") == [1, 2]
    assert _parse_severidades([3]) == [3]
    assert _parse_severidades(None) == []
    assert _parse_severidades("no es json") == []


@pytest.mark.service
def test_listar_proyecta_activos_con_severidades(mock_pinot, mock_kafka):
    # Arrange: severidades_desbloqueadas es un campo independiente y configurable
    # por el Director (RN-SUSF-002 corregida 2026-08-08) — ya no se deriva de `nivel`.
    svc = ConsultaPlanesPublicosService()
    # Act
    data = svc.listar()
    # Assert
    assert len(data) >= 3
    by_nivel = {p["nivel"]: p for p in data}
    assert by_nivel["Básico"]["severidades_desbloqueadas"] == ["Leve"]
    assert by_nivel["Profesional"]["severidades_desbloqueadas"] == ["Leve", "Moderado"]
    assert by_nivel["Empresarial"]["severidades_desbloqueadas"] == ["Leve", "Moderado", "Grave", "Fatal"]
    assert all("idplan" in p and "precio" in p and "limites" in p for p in data)
    assert not any(p.get("nombre") == "Legacy Off" for p in data)


@pytest.mark.service
def test_plan_configurado_con_severidades_independientes_del_nivel(mock_pinot, mock_kafka):
    """Un plan con nivel 'Básico' pero con muchos usuarios/unidades y severidades
    amplias — exactamente el caso que motivó volver severidad configurable."""
    # Arrange
    from conftest import PINOT_STORE

    PINOT_STORE["Dim_Plan"].append(
        {
            "idplan": 99,
            "nombre": "Básico Plus",
            "nivel": "Básico",
            "limites": '{"unidades_max": 200, "usuarios_max": 100, "api_calls_mes": 500000, "api_calls_minuto": 1200}',
            "periodicidad": "Mensual",
            "severidades_desbloqueadas": "[1, 2, 3, 4]",
            "activo": True,
            "precio": 1.0,
            "fecha_actualizacion": "2026-01-01T00:00:00+00:00",
        }
    )
    # Act
    row = next(p for p in ConsultaPlanesPublicosService().listar() if p["idplan"] == 99)
    # Assert: nivel Básico, pero severidades de Empresarial — no está ligado.
    assert row["nivel"] == "Básico"
    assert row["severidades_desbloqueadas"] == ["Leve", "Moderado", "Grave", "Fatal"]


@pytest.mark.service
def test_sin_severidades_configuradas_incluye_plan_vacio(mock_pinot, mock_kafka):
    # Arrange
    from conftest import PINOT_STORE

    PINOT_STORE["Dim_Plan"].append(
        {
            "idplan": 98,
            "nombre": "Sin configurar",
            "nivel": "Básico",
            "limites": "{}",
            "activo": True,
            "precio": 1.0,
            "fecha_actualizacion": "2026-01-01T00:00:00+00:00",
        }
    )
    # Act
    row = next(p for p in ConsultaPlanesPublicosService().listar() if p["idplan"] == 98)
    # Assert
    assert row["severidades_desbloqueadas"] == []
