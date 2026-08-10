import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.perdida_senal_logic import detectar_huecos  # noqa: E402

UMBRAL = 60  # segundos


def _ping(unidad, fechahora, idaccidente="A1"):
    return {"idunidademergencia": unidad, "idaccidente": idaccidente, "fechahora": fechahora}


class TestDetectarHuecos:
    def test_sin_huecos_dentro_del_umbral(self):
        # Arrange: pings cada 30s, umbral 60s
        pings = [_ping(1, 0), _ping(1, 30_000), _ping(1, 60_000)]

        # Act
        result = detectar_huecos(pings, UMBRAL)

        # Assert
        assert result == []

    def test_detecta_hueco_mayor_al_umbral(self):
        # Arrange: 0s -> 120s, hueco de 120s > umbral 60s
        pings = [_ping(1, 0, "A1"), _ping(1, 120_000, "A2")]

        # Act
        result = detectar_huecos(pings, UMBRAL)

        # Assert
        assert len(result) == 1
        hueco = result[0]
        assert hueco["idunidademergencia"] == 1
        assert hueco["idaccidente"] == "A2"
        assert hueco["duracion_seg"] == 120
        assert hueco["umbral_usado_seg"] == UMBRAL

    def test_intervalo_exactamente_en_el_umbral_no_es_hueco(self):
        # Arrange: intervalo == umbral, no es "mayor al umbral" (spec FR-005: "mayores al umbral")
        pings = [_ping(1, 0), _ping(1, UMBRAL * 1000)]

        # Act
        result = detectar_huecos(pings, UMBRAL)

        # Assert
        assert result == []

    def test_multiples_unidades_no_se_mezclan(self):
        # Arrange: la función procesa una unidad a la vez, se llama por separado
        pings_unidad_1 = [_ping(1, 0), _ping(1, 120_000)]
        pings_unidad_2 = [_ping(2, 0), _ping(2, 30_000)]

        # Act
        result_1 = detectar_huecos(pings_unidad_1, UMBRAL)
        result_2 = detectar_huecos(pings_unidad_2, UMBRAL)

        # Assert
        assert len(result_1) == 1 and result_1[0]["idunidademergencia"] == 1
        assert result_2 == []

    def test_detecta_multiples_huecos_en_secuencia(self):
        # Arrange
        pings = [_ping(1, 0), _ping(1, 120_000), _ping(1, 130_000), _ping(1, 300_000)]

        # Act
        result = detectar_huecos(pings, UMBRAL)

        # Assert
        assert len(result) == 2
        assert result[0]["duracion_seg"] == 120
        assert result[1]["duracion_seg"] == 170

    def test_pings_desordenados_se_procesan_en_orden_cronologico(self):
        # Arrange: llegan desordenados
        pings = [_ping(1, 120_000), _ping(1, 0)]

        # Act
        result = detectar_huecos(pings, UMBRAL)

        # Assert
        assert len(result) == 1
        assert result[0]["inicio_hueco"] < result[0]["fin_hueco"]


class TestIdempotencia:
    def test_procesar_el_mismo_conjunto_dos_veces_produce_el_mismo_resultado(self):
        # Arrange (SC-003): la función es pura — mismo input, mismo output, sin estado acumulado
        pings = [_ping(1, 0, "A1"), _ping(1, 120_000, "A2"), _ping(1, 300_000, "A3")]

        # Act
        primera_corrida = detectar_huecos(pings, UMBRAL)
        segunda_corrida = detectar_huecos(pings, UMBRAL)

        # Assert
        assert primera_corrida == segunda_corrida
        assert len(primera_corrida) == 2
