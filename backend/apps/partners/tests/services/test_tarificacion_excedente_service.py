"""Tarificación del excedente (CU-O54, RF-APM-011 a 014).

Reúne T047–T052. Es el único servicio del módulo que mueve dinero, así que casi
todos los tests comprueban que **no cobra de más**:

- no factura dos veces el mismo período
- no emite factura de cero cuando falta la tarifa
- no cobra una factura en disputa
- da el mismo importe en dos ejecuciones
"""

from __future__ import annotations

import pytest

from apps.partners.services.tarificacion_excedente_service import (
    ESPERAS_REINTENTO_MS,
    MAX_REINTENTOS,
    SIN_TARIFA,
    TIPO_EXCEDENTE,
    TarificacionExcedenteService,
)
from conftest import PINOT_STORE

pytestmark = [pytest.mark.django_db, pytest.mark.service]

ID_PARTNER = 870
ID_CLIENTE = 870
ANIO, MES = 2026, 7
PERIODO = "2026-07"


def _partner(cupo=100):
    PINOT_STORE["Dim_Partner"].append({
        "idpartner": ID_PARTNER,
        "idcliente": ID_CLIENTE,
        "nombrepartner": "Demo Excedente",
        "contacto_tecnico_nombre": "Ana",
        "contacto_tecnico_gmail": "ana@demo.com",
        "planapi": "Profesional",
        "limitellamadasmes": cupo,
        "limitellamadasminuto": 120,
        "sandbox_activado": 1,
        "sandbox_expiracion": 253402300799000,
        "fecha_suspension": "",
        "motivo_suspension": "",
        "activo": True,
        "fecha_actualizacion": 1,
    })


def _plan(precio=0.05):
    PINOT_STORE["Dim_Plan"].append({
        "idplan": ID_CLIENTE,
        "nombre": "Profesional",
        "limites": '{"api_calls_mes": 100, "api_calls_minuto": 120}',
        "precio_excedente_llamada": precio,
        "severidades_desbloqueadas": '["Media"]',
        "activo": True,
    })
    PINOT_STORE["Fact_Suscripcion"].append({
        "id_suscripcion": ID_CLIENTE,
        "idcliente": ID_CLIENTE,
        "idplan": ID_CLIENTE,
        "estado": "Activa",
        "activo": True,
        "fecha_inicio": 1,
        "severidades_desbloqueadas": '["Media"]',
    })


def _consumo(cuantas):
    """Consumo dentro del período 2026-07."""
    desde, _ = TarificacionExcedenteService().metricas.periodo_mensual(ANIO, MES)
    for i in range(cuantas):
        PINOT_STORE["Fact_APIIntegracion"].append({
            "idapiintegracion": len(PINOT_STORE["Fact_APIIntegracion"]) + 1,
            "idpartner": ID_PARTNER,
            "idcliente": ID_CLIENTE,
            "idservicio": 1,
            "idestadointegracion": 2,
            "entorno": "Producción",
            "llamadas": 1,
            "errores": 0,
            "latencia": 90.0,
            "activo": True,
            "fechahora": desde + 1000 + i,
            "fecha_actualizacion": desde + 1000 + i,
        })


def _factura_previa(estado="Pendiente"):
    PINOT_STORE["Fact_Factura"].append({
        "id_factura": "factura-previa-1",
        "id_cliente": ID_CLIENTE,
        "tipo": TIPO_EXCEDENTE,
        "periodo": PERIODO,
        "monto": 2.5,
        "estado_pago": estado,
        "reintentos": 0,
        "resultado_ultimo_reintento": "",
        "proximo_reintento": 0,
        "activo": True,
    })


class _Alertas:
    def __init__(self):
        self.avisos = []

    def notificar_excepcion_facturacion(self, *, asunto, cuerpo):
        self.avisos.append({"asunto": asunto, "cuerpo": cuerpo})


def _servicio(alertas=None):
    return TarificacionExcedenteService(alertas=alertas)


class TestCalculoDelExcedente:
    def test_separa_lo_incluido_de_lo_excedente(self, mock_pinot, mock_kafka):
        # Arrange — cupo 100, consumo 150
        _partner(cupo=100)
        _plan(precio=0.05)
        _consumo(150)

        # Act
        c = _servicio().calcular(ID_PARTNER, anio=ANIO, mes=MES)

        # Assert
        assert c["incluidas"] == 100
        assert c["excedentes"] == 50
        assert c["importe"] == 2.5

    def test_sin_excedente_no_hay_nada_que_facturar(self, mock_pinot, mock_kafka):
        # Arrange
        _partner(cupo=100)
        _plan()
        _consumo(30)

        # Act
        c = _servicio().calcular(ID_PARTNER, anio=ANIO, mes=MES)

        # Assert
        assert c["emitible"] is False
        assert c["motivo"] == "sin_excedente"
        assert c["importe"] == 0.0

    def test_es_determinista(self, mock_pinot, mock_kafka):
        """RNF-APM-001 — dos ejecuciones sobre los mismos datos dan lo mismo.
        Es la base de poder discutir una factura con el cliente."""
        # Arrange
        _partner(cupo=100)
        _plan(precio=0.037)
        _consumo(173)
        servicio = _servicio()

        # Act
        primera = servicio.calcular(ID_PARTNER, anio=ANIO, mes=MES)
        segunda = servicio.calcular(ID_PARTNER, anio=ANIO, mes=MES)

        # Assert
        assert primera == segunda

    def test_el_consumo_de_otro_periodo_no_se_cuenta(self, mock_pinot, mock_kafka):
        # Arrange
        _partner(cupo=100)
        _plan()
        _consumo(150)

        # Act — se corta un mes distinto
        c = _servicio().calcular(ID_PARTNER, anio=2026, mes=6)

        # Assert
        assert c["excedentes"] == 0


class TestCentinelaDeTarifa:
    """RF-APM-011 — sin tarifa NO se emite factura de cero."""

    def test_sin_tarifa_no_emite_y_alerta(self, mock_pinot, mock_kafka):
        """Facturar cero sería ingreso real no cobrado, en silencio."""
        # Arrange
        _partner(cupo=100)
        _plan(precio=SIN_TARIFA)
        _consumo(150)
        alertas = _Alertas()

        # Act
        resultado = _servicio(alertas).emitir(ID_PARTNER, anio=ANIO, mes=MES)

        # Assert
        assert resultado["resultado"] == "no_tarificable"
        assert PINOT_STORE["Fact_Factura"] == []
        assert len(alertas.avisos) == 1

    def test_la_alerta_explica_que_no_se_emitio_nada(self, mock_pinot, mock_kafka):
        # Arrange
        _partner(cupo=100)
        _plan(precio=SIN_TARIFA)
        _consumo(150)
        alertas = _Alertas()

        # Act
        _servicio(alertas).emitir(ID_PARTNER, anio=ANIO, mes=MES)

        # Assert
        assert "no se emitió factura" in alertas.avisos[0]["cuerpo"].lower()

    def test_un_precio_negativo_tambien_cuenta_como_sin_tarifa(
        self, mock_pinot, mock_kafka
    ):
        # Arrange
        _partner(cupo=100)
        _plan(precio=-5.0)
        _consumo(150)

        # Act / Assert
        assert _servicio().emitir(ID_PARTNER, anio=ANIO, mes=MES)["resultado"] == (
            "no_tarificable"
        )


class TestLaFacturaLLevaSuImporte:
    """🐛 Regresión: el importe se escribía en una columna que no existe.

    `_publicar_factura` publicaba `monto`, y `Fact_Factura` **no tiene esa
    columna** — tiene `monto_base` y `monto_total`. Pinot descartaba el campo en
    silencio y la factura se creaba **sin importe**: existía, pero no cobraba
    nada. Es RN-APM-014 incumplida de la forma más difícil de ver, porque la
    factura sí aparece.

    Sobrevivió a 18 tests porque los fixtures sembraban `monto` y lo leían de
    vuelta: el test y el código compartían el mismo error.

    Se detectó al mirar la cola de excepciones en la app real, donde la columna
    de importe salía vacía.
    """

    def test_el_importe_va_en_columnas_que_EXISTEN_en_el_esquema(
        self, mock_pinot, mock_kafka
    ):
        # Arrange
        _partner(cupo=100)
        _plan(precio=0.5)
        _consumo(300)

        # Act
        _servicio().emitir(ID_PARTNER, anio=ANIO, mes=MES)

        # Assert
        factura = PINOT_STORE["Fact_Factura"][-1]
        assert factura["monto_total"] == 100.0
        assert factura["monto_base"] == 100.0
        assert "monto" not in factura, (
            "`monto` no es una columna de Fact_Factura: Pinot la descarta y la "
            "factura queda sin importe"
        )


class TestNoDuplicacion:
    """RF-APM-012 — un doble cobro es peor que no cobrar."""

    def test_con_factura_previa_no_emite_otra(self, mock_pinot, mock_kafka):
        # Arrange
        _partner(cupo=100)
        _plan()
        _consumo(150)
        _factura_previa()

        # Act
        resultado = _servicio().emitir(ID_PARTNER, anio=ANIO, mes=MES)

        # Assert — sigue habiendo una sola
        assert resultado["resultado"] == "ya_emitida"
        assert len(PINOT_STORE["Fact_Factura"]) == 1

    def test_dos_ejecuciones_del_corte_emiten_una_sola_factura(
        self, mock_pinot, mock_kafka
    ):
        """El caso real: el job corre dos veces por un reintento mal contado."""
        # Arrange
        _partner(cupo=100)
        _plan()
        _consumo(150)
        servicio = _servicio()

        # Act
        primera = servicio.emitir(ID_PARTNER, anio=ANIO, mes=MES)
        segunda = servicio.emitir(ID_PARTNER, anio=ANIO, mes=MES)

        # Assert
        assert primera["resultado"] == "emitida"
        assert segunda["resultado"] == "ya_emitida"
        assert len(PINOT_STORE["Fact_Factura"]) == 1

    def test_la_verificacion_distingue_el_tipo_de_factura(
        self, mock_pinot, mock_kafka
    ):
        """Una factura de suscripción del mismo período no bloquea la de
        excedente: son cobros distintos."""
        # Arrange
        _partner(cupo=100)
        _plan()
        _consumo(150)
        PINOT_STORE["Fact_Factura"].append({
            "id_factura": "factura-suscripcion",
            "id_cliente": ID_CLIENTE,
            "tipo": "suscripcion",
            "periodo": PERIODO,
            "monto": 149.0,
            "estado_pago": "Pendiente",
            "activo": True,
        })

        # Act
        resultado = _servicio().emitir(ID_PARTNER, anio=ANIO, mes=MES)

        # Assert
        assert resultado["resultado"] == "emitida"


class TestFacturaEnDisputa:
    """RF-APM-014 — excluida del cobro automático mientras se resuelve."""

    def test_una_factura_en_disputa_no_se_vuelve_a_emitir(
        self, mock_pinot, mock_kafka
    ):
        # Arrange
        _partner(cupo=100)
        _plan()
        _consumo(150)
        _factura_previa(estado="En disputa")

        # Act
        resultado = _servicio().emitir(ID_PARTNER, anio=ANIO, mes=MES)

        # Assert
        assert resultado["resultado"] == "en_disputa"
        assert len(PINOT_STORE["Fact_Factura"]) == 1

    def test_una_factura_en_disputa_no_entra_en_los_reintentos(
        self, mock_pinot, mock_kafka
    ):
        # Arrange
        PINOT_STORE["Fact_Factura"].append({
            "id_factura": "disputada",
            "id_cliente": ID_CLIENTE,
            "tipo": TIPO_EXCEDENTE,
            "periodo": PERIODO,
            "monto": 5.0,
            "estado_pago": "En disputa",
            "reintentos": 1,
            "proximo_reintento": 100,
            "activo": True,
        })

        # Act
        vencidos = _servicio().reintentos_vencidos(ahora_ms=999_999)

        # Assert
        assert vencidos == []

    def test_este_modulo_no_abre_ni_resuelve_disputas(self):
        """Solo respeta la exclusión: las disputas viven en Soporte."""
        # Act
        metodos = {m for m in dir(TarificacionExcedenteService) if not m.startswith("_")}

        # Assert
        assert not any(
            p in m for m in metodos for p in ("abrir_disputa", "resolver_disputa", "disputar")
        )


class TestReintentosPersistidos:
    """RF-APM-013 — estado guardado, nunca `sleep`.

    Con `sleep`, un reinicio del contenedor perdería el reintento y el cobro
    quedaría a medias sin que nadie se entere.
    """

    def _factura(self, reintentos=0):
        return {
            "id_factura": "f-1",
            "id_cliente": ID_CLIENTE,
            "tipo": TIPO_EXCEDENTE,
            "periodo": PERIODO,
            "monto": 2.5,
            "estado_pago": "Pendiente",
            "reintentos": reintentos,
            "resultado_ultimo_reintento": "",
            "proximo_reintento": 0,
            "activo": True,
        }

    def test_los_escalones_son_1h_6h_y_24h(self, mock_pinot, mock_kafka):
        # Arrange
        servicio = _servicio()
        esperas = []

        # Act — tres fallos sucesivos
        factura = self._factura()
        for _ in range(MAX_REINTENTOS):
            r = servicio.programar_reintento(factura, "timeout", ahora_ms=0)
            esperas.append(r["espera_ms"])
            factura = {k: v for k, v in r.items() if k in factura}

        # Assert
        assert tuple(esperas) == ESPERAS_REINTENTO_MS

    def test_cada_intento_persiste_su_resultado(self, mock_pinot, mock_kafka):
        # Arrange / Act
        r = _servicio().programar_reintento(
            self._factura(), "Kafka caído", ahora_ms=1000
        )

        # Assert
        assert r["reintentos"] == 1
        assert r["resultado_ultimo_reintento"] == "Kafka caído"
        assert r["proximo_reintento"] == 1000 + ESPERAS_REINTENTO_MS[0]

    def test_agotados_los_tres_queda_pendiente_de_emision_manual(
        self, mock_pinot, mock_kafka
    ):
        # Arrange
        alertas = _Alertas()

        # Act — el cuarto intento
        r = _servicio(alertas).programar_reintento(
            self._factura(reintentos=MAX_REINTENTOS), "sigue fallando", ahora_ms=0
        )

        # Assert
        assert r["resultado"] == "reintentos_agotados"
        assert r["proximo_reintento"] == 0
        assert len(alertas.avisos) == 1
        assert "manual" in alertas.avisos[0]["cuerpo"].lower()

    def test_el_servicio_no_usa_sleep(self):
        """Guardián: un `sleep` aquí no sobreviviría a un reinicio."""
        # Arrange
        import inspect

        from apps.partners.services import tarificacion_excedente_service as modulo

        # Act
        fuente = inspect.getsource(modulo)

        # Assert
        assert "time.sleep" not in fuente
        assert "sleep(" not in fuente

    def test_solo_devuelve_los_reintentos_ya_vencidos(self, mock_pinot, mock_kafka):
        # Arrange
        for idf, proximo in (("vencido", 500), ("futuro", 50_000), ("sin_reintento", 0)):
            PINOT_STORE["Fact_Factura"].append({
                "id_factura": idf,
                "id_cliente": ID_CLIENTE,
                "tipo": TIPO_EXCEDENTE,
                "periodo": PERIODO,
                "monto": 1.0,
                "estado_pago": "Pendiente",
                "reintentos": 1,
                "proximo_reintento": proximo,
                "activo": True,
            })

        # Act
        vencidos = _servicio().reintentos_vencidos(ahora_ms=1000)

        # Assert
        assert [f["id_factura"] for f in vencidos] == ["vencido"]
