import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile


@pytest.mark.api
class TestImportacionLoteContract:
    def _csv_file(self, filas: list[str]) -> SimpleUploadedFile:
        header = "idcliente,idcondado,tipopropiedad,placa,contactoproveedor,unidademergencia,tipounidademergencia"
        content = "\n".join([header, *filas])
        return SimpleUploadedFile("unidades.csv", content.encode("utf-8"), content_type="text/csv")

    def test_post_importacion_lote_when_todas_validas_returns_200(
        self, api_client, admin_auth_headers
    ):
        # Arrange
        archivo = self._csv_file(
            [
                "1,1,Externa,LOTE-API-1,555,Ambulancia 1,Ambulancia",
                "1,1,Externa,LOTE-API-2,555,Ambulancia 2,Ambulancia",
            ]
        )

        # Act
        response = api_client.post(
            "/api/v1/red-operativa/unidades/importacion-lote",
            {"archivo": archivo},
            format="multipart",
            **admin_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["data"]["insertadas"] == 2

    def test_post_importacion_lote_when_fila_invalida_returns_200_con_fallidas(
        self, api_client, admin_auth_headers, mock_unidad_emergencia
    ):
        # Arrange
        archivo = self._csv_file(
            [f"1,1,Externa,{mock_unidad_emergencia['placa']},555,Ambulancia Dup,Ambulancia"]
        )

        # Act
        response = api_client.post(
            "/api/v1/red-operativa/unidades/importacion-lote",
            {"archivo": archivo},
            format="multipart",
            **admin_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        body = response.json()["data"]
        assert body["insertadas"] == 0
        assert len(body["fallidas"]) == 1

    def test_post_importacion_lote_when_sin_archivo_returns_400(
        self, api_client, admin_auth_headers
    ):
        # Act
        response = api_client.post(
            "/api/v1/red-operativa/unidades/importacion-lote",
            {},
            format="multipart",
            **admin_auth_headers,
        )

        # Assert
        assert response.status_code == 400
