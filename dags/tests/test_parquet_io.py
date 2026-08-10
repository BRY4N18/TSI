import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd  # noqa: E402

from lib.parquet_io import read_parquet, stage_path, write_parquet  # noqa: E402


class TestStagePath:
    def test_construye_ruta_fecha_hora_stage(self, tmp_path):
        # Arrange
        ts = "2025-04-10T14:30:00+00:00"

        # Act
        path = stage_path(ts, "extract", etl_root=tmp_path)

        # Assert: HH-MM (guion), no HH:MM -- los dos puntos no son válidos en rutas de Windows
        assert path == tmp_path / "2025-04-10" / "14-30" / "extract_data.parquet"

    def test_cada_stage_tiene_su_propio_nombre_de_archivo(self, tmp_path):
        ts = "2025-04-10T14:30:00+00:00"

        extract_path = stage_path(ts, "extract", etl_root=tmp_path)
        transform_path = stage_path(ts, "transform", etl_root=tmp_path)
        load_path = stage_path(ts, "load", etl_root=tmp_path)

        assert {extract_path.name, transform_path.name, load_path.name} == {
            "extract_data.parquet",
            "transform_data.parquet",
            "loading_data.parquet",
        }

    def test_stage_desconocido_lanza_value_error(self, tmp_path):
        try:
            stage_path("2025-04-10T14:30:00+00:00", "no_existe", etl_root=tmp_path)
        except ValueError:
            return
        raise AssertionError("Se esperaba ValueError para un stage desconocido")


class TestRoundTrip:
    def test_escribir_y_leer_devuelve_el_mismo_contenido(self, tmp_path):
        # Arrange
        df = pd.DataFrame([{"a": 1, "b": "x"}, {"a": 2, "b": "y"}])
        path = tmp_path / "sub" / "archivo.parquet"

        # Act
        write_parquet(df, path)
        result = read_parquet(path)

        # Assert
        assert path.exists()
        pd.testing.assert_frame_equal(result, df)

    def test_write_parquet_crea_carpetas_intermedias(self, tmp_path):
        df = pd.DataFrame([{"a": 1}])
        path = tmp_path / "no" / "existe" / "aun" / "archivo.parquet"

        write_parquet(df, path)

        assert path.exists()
