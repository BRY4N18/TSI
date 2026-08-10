import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile


@pytest.mark.api
class TestImportacionLoteContract:
    def _csv_file(self, filas: list[str], *, with_gmail: bool = True) -> SimpleUploadedFile:
        if with_gmail:
            header = (
                "idcondado,tipopropiedad,placa,contactoproveedor,"
                "unidademergencia,tipounidademergencia,gmail"
            )
        else:
            header = (
                "idcondado,tipopropiedad,placa,contactoproveedor,"
                "unidademergencia,tipounidademergencia"
            )
        content = "\n".join([header, *filas])
        return SimpleUploadedFile("unidades.csv", content.encode("utf-8"), content_type="text/csv")

    def test_post_importacion_lote_when_todas_validas_returns_200(
        self, api_client, proveedor_auth_headers
    ):
        # Arrange
        archivo = self._csv_file(
            [
                "1,Externa,LOTE-API-1,555,Ambulancia 1,Ambulancia,u1@lote.test",
                "1,Externa,LOTE-API-2,555,Ambulancia 2,Ambulancia,u2@lote.test",
            ]
        )

        # Act
        response = api_client.post(
            "/api/v1/red-operativa/unidades/importacion-lote",
            {"archivo": archivo},
            format="multipart",
            **proveedor_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["insertadas"] == 2
        assert data["usuarios_creados"] == 2

    def test_post_importacion_lote_when_gmail_invalido_insertadas_0(
        self, api_client, proveedor_auth_headers
    ):
        # Arrange
        archivo = self._csv_file(
            ["1,Externa,LOTE-BAD,555,Ambulancia Bad,Ambulancia,no-es-email"]
        )

        # Act
        response = api_client.post(
            "/api/v1/red-operativa/unidades/importacion-lote",
            {"archivo": archivo},
            format="multipart",
            **proveedor_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        body = response.json()["data"]
        assert body["insertadas"] == 0
        assert len(body["fallidas"]) == 1

    def test_post_importacion_lote_when_fila_invalida_returns_200_con_fallidas(
        self, api_client, proveedor_auth_headers, mock_unidad_emergencia
    ):
        # Arrange
        archivo = self._csv_file(
            [
                f"1,Externa,{mock_unidad_emergencia['placa']},555,"
                f"Ambulancia Dup,Ambulancia,dup@lote.test"
            ]
        )

        # Act
        response = api_client.post(
            "/api/v1/red-operativa/unidades/importacion-lote",
            {"archivo": archivo},
            format="multipart",
            **proveedor_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        body = response.json()["data"]
        assert body["insertadas"] == 0
        assert len(body["fallidas"]) == 1

    def test_post_importacion_lote_when_plan_no_habilita_returns_403(
        self, api_client, proveedor_auth_headers, pinot_store
    ):
        # Arrange — RF-O40.6: gate depende de la suscripción activa del proveedor.
        pinot_store["Fact_Suscripcion"][0]["carga_lote_habilitada"] = False
        archivo = self._csv_file(["1,Externa,LOTE-GATE,555,Ambulancia Gate,Ambulancia,g@lote.test"])

        # Act
        response = api_client.post(
            "/api/v1/red-operativa/unidades/importacion-lote",
            {"archivo": archivo},
            format="multipart",
            **proveedor_auth_headers,
        )

        # Assert
        assert response.status_code == 403

    def test_post_importacion_lote_when_sin_archivo_returns_400(
        self, api_client, proveedor_auth_headers
    ):
        # Act
        response = api_client.post(
            "/api/v1/red-operativa/unidades/importacion-lote",
            {},
            format="multipart",
            **proveedor_auth_headers,
        )

        # Assert
        assert response.status_code == 400
