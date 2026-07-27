import pytest

from apps.ventas_crm.services.consulta_planes_publicos_service import (
    ConsultaPlanesPublicosService,
    severidades_para_nivel,
)


@pytest.mark.service
def test_severidades_mapa_canónico():
    # Arrange / Act / Assert
    assert severidades_para_nivel("Básico") == ["Baja"]
    assert severidades_para_nivel("Basico") == ["Baja"]
    assert severidades_para_nivel("Profesional") == ["Baja", "Media"]
    assert severidades_para_nivel("Empresarial") == ["Baja", "Media", "Alta"]
    assert severidades_para_nivel("premium") == []
    assert severidades_para_nivel(None) == []


@pytest.mark.service
def test_listar_proyecta_activos_con_severidades(mock_pinot, mock_kafka):
    # Arrange
    svc = ConsultaPlanesPublicosService()
    # Act
    data = svc.listar()
    # Assert
    assert len(data) >= 3
    by_nivel = {p["nivel"]: p for p in data}
    assert by_nivel["Básico"]["severidades_desbloqueadas"] == ["Baja"]
    assert by_nivel["Profesional"]["severidades_desbloqueadas"] == ["Baja", "Media"]
    assert by_nivel["Empresarial"]["severidades_desbloqueadas"] == ["Baja", "Media", "Alta"]
    assert all("idplan" in p and "precio" in p and "limites" in p for p in data)
    assert not any(p.get("nombre") == "Legacy Off" for p in data)


@pytest.mark.service
def test_nivel_desconocido_incluye_plan_sin_severidades(mock_pinot, mock_kafka):
    # Arrange
    from conftest import PINOT_STORE

    PINOT_STORE["Dim_Plan"].append(
        {
            "idplan": 99,
            "nombre": "Experimental",
            "nivel": "gold",
            "limites": "{}",
            "activo": True,
            "precio": 1.0,
            "fecha_actualizacion": "2026-01-01T00:00:00+00:00",
        }
    )
    # Act
    row = next(p for p in ConsultaPlanesPublicosService().listar() if p["idplan"] == 99)
    # Assert
    assert row["nombre"] == "Experimental"
    assert row["severidades_desbloqueadas"] == []
