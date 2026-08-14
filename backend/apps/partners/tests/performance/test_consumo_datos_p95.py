"""RNF-APM-002 y RNF-APM-003 — coste del registro y capacidad de escritura.

Dos mediciones que responden preguntas distintas:

- **T063:** ¿cuánto le cuesta al partner que midamos su consumo? Se mide el
  endpoint **con y sin** el middleware activo, para aislar ese coste del de
  bcrypt, que es inherente a la autenticación y no se puede quitar.
- **T064:** ¿cuántas escrituras por segundo aguanta el registro? Es la cifra
  que dice si el módulo sobrevive a un partner con tráfico alto.

Si el p95 empieza a acercarse al umbral, la corrección **no** es bajar
`BCRYPT_ROUNDS`: es mirar qué se metió en la ruta. El Tie-Breaker ya resolvió
ese conflicto a favor de Security.
"""

from __future__ import annotations

import time

import pytest

from apps.partners.services.registro_consumo_service import RegistroConsumoService
from conftest import PINOT_STORE

ID_PARTNER = 880

# El endpoint hace bcrypt (coste 12, cientos de ms por diseño) + consulta de
# alcance + registro. El umbral es holgado por la misma razón que en #07.
UMBRAL_P95_MS = 2000
MUESTRAS = 20

# RNF-APM-003: el registro no puede ser el cuello de botella de la API.
UMBRAL_ESCRITURAS_POR_SEGUNDO = 50
ESCRITURAS = 200


@pytest.fixture
def entorno_consumible(credencial_produccion_headers):
    PINOT_STORE["Dim_Plan"].append({
        "idplan": ID_PARTNER,
        "nombre": "Profesional",
        "limites": '{"api_calls_mes": 100000, "api_calls_minuto": 100000}',
        "severidades_desbloqueadas": "null",
        "activo": True,
    })
    PINOT_STORE["Fact_Suscripcion"].append({
        "id_suscripcion": ID_PARTNER,
        "idcliente": ID_PARTNER,
        "idplan": ID_PARTNER,
        "estado": "Activa",
        "activo": True,
        "fecha_inicio": 1,
        "severidades_desbloqueadas": "[1, 2]",
    })
    PINOT_STORE["Dim_Preferencias_Cliente"].append(
        {"id_cliente": ID_PARTNER, "zonas_geograficas": "[10]"}
    )
    # El throttle usa la caché global; sin límite alto, 20 peticiones seguidas
    # devolverían 429 y la medición no mediría el camino feliz.
    for p in PINOT_STORE["Dim_Partner"]:
        if p["idpartner"] == ID_PARTNER:
            p["limitellamadasminuto"] = 100_000
    return credencial_produccion_headers


def _p95(muestras: list[float]) -> float:
    muestras.sort()
    return muestras[max(int(len(muestras) * 0.95) - 1, 0)]


def _medir(api_client, cabeceras) -> list[float]:
    tiempos = []
    for _ in range(MUESTRAS):
        inicio = time.perf_counter()
        respuesta = api_client.get("/api/v1/datos/accidentes", **cabeceras)
        tiempos.append((time.perf_counter() - inicio) * 1000)
        assert respuesta.status_code == 200
    return tiempos


@pytest.mark.slow
@pytest.mark.api
@pytest.mark.django_db
class TestConsumoDatosP95:
    def test_p95_bajo_umbral_y_coste_del_registro_aislado(
        self, api_client, entorno_consumible, settings
    ):
        # Arrange / Act — con el middleware de registro activo
        con_registro = _medir(api_client, entorno_consumible)

        # Sin él: la diferencia es exactamente lo que cuesta medir.
        settings.MIDDLEWARE = [
            m for m in settings.MIDDLEWARE if "registro_consumo" not in m
        ]
        sin_registro = _medir(api_client, entorno_consumible)

        p95_con, p95_sin = _p95(con_registro), _p95(sin_registro)
        coste = p95_con - p95_sin

        print(
            f"\nRNF-APM-002 — GET /datos/accidentes:"
            f"\n  p95 CON registro: {p95_con:.0f} ms"
            f"\n  p95 SIN registro: {p95_sin:.0f} ms"
            f"\n  coste del registro: {coste:.0f} ms"
            f"\n  (n={MUESTRAS}, umbral {UMBRAL_P95_MS} ms; el resto es bcrypt "
            f"coste 12, inherente a la autenticación)"
        )

        # Assert
        assert p95_con <= UMBRAL_P95_MS, (
            f"p95 {p95_con:.0f} ms supera el umbral {UMBRAL_P95_MS} ms. "
            f"Revisar qué se añadió a la ruta; NO bajar BCRYPT_ROUNDS."
        )


@pytest.mark.slow
@pytest.mark.service
@pytest.mark.django_db
class TestCapacidadDeEscritura:
    def test_escrituras_sostenidas_por_segundo(self, mock_pinot, mock_kafka):
        """RNF-APM-003 — el registro no puede ser el cuello de botella."""
        # Arrange
        servicio = RegistroConsumoService()

        # Act
        inicio = time.perf_counter()
        for _ in range(ESCRITURAS):
            servicio.registrar_llamada(
                idpartner=ID_PARTNER,
                idcliente=ID_PARTNER,
                idcredencial=1,
                entorno="Producción",
                endpoint="/api/v1/datos/accidentes",
                metodohttp="GET",
                codigohttp=200,
                latencia_ms=90.0,
            )
        transcurrido = time.perf_counter() - inicio
        por_segundo = ESCRITURAS / transcurrido

        print(
            f"\nRNF-APM-003 — capacidad de escritura del registro:"
            f"\n  {por_segundo:.0f} registros/s "
            f"({ESCRITURAS} en {transcurrido:.2f} s, dos filas por registro)"
            f"\n  umbral {UMBRAL_ESCRITURAS_POR_SEGUNDO}/s"
        )

        # Assert
        assert por_segundo >= UMBRAL_ESCRITURAS_POR_SEGUNDO
        assert len(PINOT_STORE["Fact_APIIntegracion"]) == ESCRITURAS
        assert len(PINOT_STORE["Fact_LogLlamadaAPI"]) == ESCRITURAS
