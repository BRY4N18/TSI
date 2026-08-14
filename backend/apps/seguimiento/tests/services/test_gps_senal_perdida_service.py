import pytest

from apps.seguimiento.services.gps_senal_perdida_service import GpsSenalPerdidaService


@pytest.mark.service
class TestGpsSenalPerdidaService:
    def test_evaluar_when_sin_gps_genera_alerta(
        self,
        mock_pinot,
        mock_kafka,
        accidente_activo,
        despacho_confirmado_unidad,
    ):
        # Arrange — despacho confirmado sin posiciones GPS recientes
        svc = GpsSenalPerdidaService()

        # Act
        alertas = svc.evaluar_unidades_en_camino(idusuario_operador=2)

        # Assert
        assert len(alertas) >= 1
        assert alertas[0]["iddespacho"] == despacho_confirmado_unidad["iddespacho"]

    def test_evaluar_when_gps_reciente_no_alerta(
        self,
        mock_pinot,
        mock_kafka,
        accidente_activo,
        despacho_confirmado_unidad,
    ):
        # Arrange
        from datetime import datetime, timezone

        from apps.seguimiento.services.registrar_posicion_gps_service import (
            RegistrarPosicionGpsService,
        )

        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        RegistrarPosicionGpsService().registrar(
            idunidademergencia=1,
            idaccidente=accidente_activo,
            latitud=19.4326,
            longitud=-99.1332,
            fechahora=now,
            idusuario=6,
        )
        svc = GpsSenalPerdidaService()

        # Act
        alertas = svc.evaluar_unidades_en_camino(idusuario_operador=2)

        # Assert
        assert len(alertas) == 0

    def test_una_perdida_de_senal_deja_un_solo_aviso(
        self,
        mock_pinot,
        mock_kafka,
        accidente_activo,
        despacho_confirmado_unidad,
        pinot_store,
    ):
        # Arrange — el job corre cada 30 s. Sin guarda, cada pasada añadía otra
        # nota idéntica y el expediente quedaba sepultado en avisos repetidos.
        svc = GpsSenalPerdidaService()

        # Act — tres ciclos consecutivos con la señal aún perdida
        primera = svc.evaluar_unidades_en_camino(idusuario_operador=2)
        segunda = svc.evaluar_unidades_en_camino(idusuario_operador=2)
        tercera = svc.evaluar_unidades_en_camino(idusuario_operador=2)

        # Assert
        assert len(primera) == 1
        assert segunda == []
        assert tercera == []
        alertas = [
            n
            for n in pinot_store["Dim_NotaAccidente"]
            if n.get("tipo") == "alerta" and "Señal GPS perdida" in n.get("nota", "")
        ]
        assert len(alertas) == 1

    def test_vuelve_a_avisar_si_la_senal_se_pierde_otra_vez(
        self,
        mock_pinot,
        mock_kafka,
        accidente_activo,
        despacho_confirmado_unidad,
        pinot_store,
    ):
        # Arrange — secuencia real: aviso, la unidad reaparece (posición
        # posterior al aviso) y vuelve a quedarse muda más del umbral. Esa
        # segunda interrupción sí es un aviso nuevo: la guarda silencia la
        # repetición de una misma pérdida, no las pérdidas siguientes.
        from datetime import datetime, timezone

        from apps.seguimiento.services.registrar_posicion_gps_service import (
            RegistrarPosicionGpsService,
        )

        svc = GpsSenalPerdidaService()
        assert len(svc.evaluar_unidades_en_camino(idusuario_operador=2)) == 1
        assert svc.evaluar_unidades_en_camino(idusuario_operador=2) == []

        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        for nota in pinot_store["Dim_NotaAccidente"]:
            if nota.get("tipo") == "alerta":
                nota["fechahora"] = now - 300_000  # el aviso fue hace 5 min
        RegistrarPosicionGpsService().registrar(
            idunidademergencia=1,
            idaccidente=accidente_activo,
            latitud=19.44,
            longitud=-99.15,
            fechahora=now - 120_000,  # reapareció después del aviso...
            idusuario=6,
        )

        # Act — ...y lleva 2 min sin dar señal otra vez (umbral: 60 s)
        alertas = svc.evaluar_unidades_en_camino(idusuario_operador=2)

        # Assert
        assert len(alertas) == 1
