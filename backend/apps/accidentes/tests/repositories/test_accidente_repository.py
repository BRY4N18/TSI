import pytest

from core.repositories.accidentes.accidente_repository import AccidenteRepository


@pytest.mark.repository
class TestAccidenteRepository:
    def test_create_when_valid_publishes_and_reads_back(self, mock_pinot, mock_kafka):
        # Arrange
        repo = AccidenteRepository()
        payload = {
            "idaccidente": "ACC-TEST-1",
            "latitudinicio": 19.43,
            "longitudinicio": -99.13,
            "fechahoraaccidente": 1_700_000_000_000,
            "idseveridad": 2,
            "descripcion": "Test",
            "idcalle": 1,
            "idusuario": 2,
            "activo": True,
        }

        # Act
        created = repo.create(payload)
        found = repo.find_by_id("ACC-TEST-1")

        # Assert
        assert created["idaccidente"] == "ACC-TEST-1"
        assert found is not None
        assert found["descripcion"] == "Test"
        assert len(mock_kafka) == 1

    def test_list_activos_when_fecha_range_filters_by_fechahoraaccidente(self, mock_pinot, mock_kafka):
        # Arrange
        repo = AccidenteRepository()
        repo.create({"idaccidente": "ACC-OLD", "fechahoraaccidente": 1_000, "activo": True, "idcalle": 1})
        repo.create({"idaccidente": "ACC-NEW", "fechahoraaccidente": 5_000, "activo": True, "idcalle": 1})

        # Act
        rows = repo.list_activos(fecha_desde=3_000, fecha_hasta=6_000)

        # Assert
        ids = [r["idaccidente"] for r in rows]
        assert "ACC-NEW" in ids
        assert "ACC-OLD" not in ids

    def test_list_activos_when_idciudad_filters_by_calle_resuelta(self, mock_pinot, mock_kafka):
        # Arrange
        repo = AccidenteRepository()
        repo.create({"idaccidente": "ACC-CIUDAD-1", "idcalle": 1, "activo": True})
        repo.create({"idaccidente": "ACC-CIUDAD-99", "idcalle": 99, "activo": True})

        # Act
        rows = repo.list_activos(idciudad=1)

        # Assert
        ids = [r["idaccidente"] for r in rows]
        assert "ACC-CIUDAD-1" in ids
        assert "ACC-CIUDAD-99" not in ids

    def test_list_activos_when_idestadoregion_filters_por_jerarquia_completa(self, mock_pinot, mock_kafka):
        # Arrange
        repo = AccidenteRepository()
        repo.create({"idaccidente": "ACC-ESTADO-1", "idcalle": 1, "activo": True})
        repo.create({"idaccidente": "ACC-ESTADO-99", "idcalle": 99, "activo": True})

        # Act
        rows = repo.list_activos(idestadoregion=1)

        # Assert
        ids = [r["idaccidente"] for r in rows]
        assert "ACC-ESTADO-1" in ids
        assert "ACC-ESTADO-99" not in ids

    def test_find_nearby_when_within_window_returns_match(self, mock_pinot, mock_kafka):
        # Arrange
        repo = AccidenteRepository()
        ts = 1_700_000_000_000
        repo.create(
            {
                "idaccidente": "ACC-NEAR",
                "latitudinicio": 19.4326,
                "longitudinicio": -99.1332,
                "fechahoraaccidente": ts,
                "activo": True,
            }
        )

        # Act
        nearby = repo.find_nearby(
            latitud=19.43261,
            longitud=-99.13321,
            fechahoraaccidente=ts,
            window_ms=300_000,
        )

        # Assert
        assert len(nearby) == 1
        assert nearby[0]["idaccidente"] == "ACC-NEAR"
