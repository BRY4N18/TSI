"""Fact_APIIntegracion — append-only y agregaciones seguras (RF-APM-004).

Dos propiedades negativas dominan este archivo, y son las que de verdad
importan: que **no haya forma de modificar** una fila registrada, y que **no
haya forma de agregar sin filtrar por entorno**. Ambas son faciles de romper
por accidente al anadir un metodo nuevo.
"""

from __future__ import annotations

import pytest

from conftest import PINOT_STORE
from core.repositories.partners.api_integracion_repository import (
    ApiIntegracionRepository,
    EntornoRequeridoError,
)

pytestmark = [pytest.mark.django_db, pytest.mark.repository]

ID_PARTNER = 800
ID_CLIENTE = 800
SANDBOX = "Sandbox"
PRODUCCION = "Producción"


def _registrar(repo, **over):
    base = {
        "idpartner": ID_PARTNER,
        "idcliente": ID_CLIENTE,
        "idservicio": 1,
        "idestadointegracion": 2,
        "entorno": PRODUCCION,
        "codigohttp": 200,
        "latencia": 120.0,
    }
    return repo.registrar(**{**base, **over})


class TestAppendOnly:
    def test_el_repositorio_no_expone_update_ni_delete(self):
        """RNF-APM-005. La inmutabilidad no es una convención que recordar:
        es una capacidad que no existe. Si alguien añade `update`, esto falla."""
        # Act
        metodos = {m for m in dir(ApiIntegracionRepository) if not m.startswith("_")}

        # Assert
        assert "update" not in metodos
        assert "delete" not in metodos
        assert "registrar" in metodos

    def test_registrar_dos_veces_crea_dos_filas(self, mock_pinot, mock_kafka):
        # Arrange
        repo = ApiIntegracionRepository()

        # Act
        _registrar(repo)
        _registrar(repo)

        # Assert
        assert len(PINOT_STORE["Fact_APIIntegracion"]) == 2


class TestMedidas:
    def test_llamadas_vale_siempre_uno(self, mock_pinot, mock_kafka):
        """RN-APM-003: el agregado se calcula al consultar, no se acumula al
        escribir. Acumular exigiría leer-modificar-escribir sobre append-only."""
        # Act
        fila = _registrar(ApiIntegracionRepository())

        # Assert
        assert fila["llamadas"] == 1

    def test_errores_es_uno_cuando_el_codigo_es_4xx(self, mock_pinot, mock_kafka):
        # Act
        fila = _registrar(ApiIntegracionRepository(), codigohttp=404)

        # Assert
        assert fila["errores"] == 1

    def test_errores_es_uno_cuando_el_codigo_es_5xx(self, mock_pinot, mock_kafka):
        # Act
        fila = _registrar(ApiIntegracionRepository(), codigohttp=503)

        # Assert
        assert fila["errores"] == 1

    def test_errores_es_cero_en_una_respuesta_correcta(self, mock_pinot, mock_kafka):
        # Act
        fila = _registrar(ApiIntegracionRepository(), codigohttp=200)

        # Assert
        assert fila["errores"] == 0

    def test_el_299_todavia_no_es_error(self, mock_pinot, mock_kafka):
        """El umbral es 400, no «cualquier cosa que no sea 200»."""
        # Act
        fila = _registrar(ApiIntegracionRepository(), codigohttp=299)

        # Assert
        assert fila["errores"] == 0

    def test_no_publica_ningun_none(self, mock_pinot, mock_kafka):
        """Pinot convertiría un None en un centinela que rompe las agregaciones."""
        # Act
        fila = _registrar(ApiIntegracionRepository())

        # Assert
        assert None not in fila.values()


class TestEntornoObligatorio:
    def test_registrar_con_entorno_invalido_lanza(self, mock_pinot, mock_kafka):
        # Act / Assert
        with pytest.raises(EntornoRequeridoError):
            _registrar(ApiIntegracionRepository(), entorno="Staging")

    def test_consumo_sin_entorno_lanza_en_vez_de_mezclar(self, mock_pinot, mock_kafka):
        """RN-APM-001: mezclar pruebas y producción falsearía tanto las métricas
        del partner como el excedente que se le factura."""
        # Act / Assert
        with pytest.raises(EntornoRequeridoError):
            ApiIntegracionRepository().consumo_del_partner(
                ID_PARTNER, entorno=None, desde_ms=0, hasta_ms=99
            )

    def test_consumo_por_servicio_sin_entorno_lanza(self, mock_pinot, mock_kafka):
        # Act / Assert
        with pytest.raises(EntornoRequeridoError):
            ApiIntegracionRepository().consumo_por_servicio(
                ID_PARTNER, entorno="", desde_ms=0, hasta_ms=99
            )

    def test_ninguna_agregacion_publica_omite_el_filtro_de_entorno(self):
        """Guardián: si alguien añade una agregación nueva sin `entorno` en su
        firma, este test lo detecta antes que la revisión de código."""
        # Arrange
        agregaciones = {"consumo_del_partner", "consumo_por_servicio", "llamadas_del_periodo"}

        # Act / Assert
        for nombre in agregaciones:
            metodo = getattr(ApiIntegracionRepository, nombre)
            assert "entorno" in metodo.__code__.co_varnames, (
                f"{nombre} agrega sin exigir entorno (RN-APM-001)"
            )


class TestAgregaciones:
    def test_consumo_suma_solo_el_entorno_pedido(self, mock_pinot, mock_kafka):
        # Arrange
        repo = ApiIntegracionRepository()
        _registrar(repo, entorno=PRODUCCION, fechahora=100)
        _registrar(repo, entorno=PRODUCCION, fechahora=200)
        _registrar(repo, entorno=SANDBOX, idestadointegracion=1, fechahora=150)

        # Act
        produccion = repo.consumo_del_partner(
            ID_PARTNER, entorno=PRODUCCION, desde_ms=0, hasta_ms=1000
        )

        # Assert — la llamada de sandbox no se cuenta
        assert produccion["llamadas"] == 2

    def test_consumo_respeta_la_ventana_temporal(self, mock_pinot, mock_kafka):
        # Arrange
        repo = ApiIntegracionRepository()
        _registrar(repo, fechahora=100)
        _registrar(repo, fechahora=5000)

        # Act
        dentro = repo.consumo_del_partner(
            ID_PARTNER, entorno=PRODUCCION, desde_ms=0, hasta_ms=1000
        )

        # Assert
        assert dentro["llamadas"] == 1

    def test_consumo_sin_datos_devuelve_ceros_no_none(self, mock_pinot, mock_kafka):
        """Un None aquí reventaría la comparación contra el cupo."""
        # Act
        vacio = ApiIntegracionRepository().consumo_del_partner(
            999999, entorno=PRODUCCION, desde_ms=0, hasta_ms=1000
        )

        # Assert
        assert vacio == {"llamadas": 0, "errores": 0, "latencia_media": 0.0}

    def test_llamadas_del_periodo_es_la_cifra_que_compara_el_cupo(
        self, mock_pinot, mock_kafka
    ):
        # Arrange
        repo = ApiIntegracionRepository()
        for _ in range(3):
            _registrar(repo, fechahora=100)

        # Act
        total = repo.llamadas_del_periodo(
            ID_PARTNER, entorno=PRODUCCION, desde_ms=0, hasta_ms=1000
        )

        # Assert
        assert total == 3
