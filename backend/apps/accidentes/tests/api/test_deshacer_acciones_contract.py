import pytest

from apps.accidentes.domain_constants import ESTADO_BORRADOR


@pytest.mark.api
class TestDeshacerDescarteContract:
    def test_deshacer_descarte_when_descartado_returns_200(
        self, api_client, operador_auth_headers, seed_accidente
    ):
        aid = seed_accidente(idaccidente="ACC-UNDO-D1", estado=ESTADO_BORRADOR)
        api_client.post(
            f"/api/v1/accidentes/{aid}/descartar",
            {"motivo": "falso positivo"},
            format="json",
            **operador_auth_headers,
        )

        response = api_client.post(
            f"/api/v1/accidentes/{aid}/deshacer-descarte",
            {},
            format="json",
            **operador_auth_headers,
        )

        assert response.status_code == 200
        assert response.json()["data"]["estado"] == ESTADO_BORRADOR

    def test_deshacer_descarte_when_borrador_returns_409(
        self, api_client, operador_auth_headers, seed_accidente
    ):
        aid = seed_accidente(idaccidente="ACC-UNDO-D2", estado=ESTADO_BORRADOR)
        response = api_client.post(
            f"/api/v1/accidentes/{aid}/deshacer-descarte",
            {},
            format="json",
            **operador_auth_headers,
        )
        assert response.status_code == 409


@pytest.mark.api
class TestDeshacerFusionContract:
    def test_deshacer_fusion_when_fusionado_returns_200(
        self, api_client, operador_auth_headers, seed_accidente
    ):
        principal = seed_accidente(idaccidente="ACC-UNDO-F-P", estado="REPORTADO")
        duplicado = seed_accidente(idaccidente="ACC-UNDO-F-D", estado="REPORTADO")
        api_client.post(
            f"/api/v1/accidentes/{duplicado}/fusionar",
            {"idaccidenteprincipal": principal, "confirmacion": True},
            format="json",
            **operador_auth_headers,
        )

        response = api_client.post(
            f"/api/v1/accidentes/{duplicado}/deshacer-fusion",
            {},
            format="json",
            **operador_auth_headers,
        )

        assert response.status_code == 200
        assert response.json()["data"]["idaccidente"] == duplicado
        assert response.json()["data"]["estado"] in {ESTADO_BORRADOR, "REPORTADO"}
