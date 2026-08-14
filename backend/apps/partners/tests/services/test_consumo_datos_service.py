"""Alcance de datos del partner (RF-APM-002, RF-APM-003).

Los dos filtros fallan de forma **deliberadamente distinta**, y esa diferencia
es el núcleo de este archivo:

- Severidad fuera de plan → **403**. Pidió algo que no le corresponde.
- Cliente sin zonas → **conjunto vacío**. No hay nada contratado que darle.

Devolver lista vacía en el primer caso le diría al partner «no hay accidentes
graves», que es falso y le haría decidir sobre una mentira.
"""

from __future__ import annotations

import json

import pytest

from apps.partners.services.consumo_datos_service import (
    ConsumoDatosError,
    ConsumoDatosService,
)
from conftest import PINOT_STORE

pytestmark = [pytest.mark.django_db, pytest.mark.service]

ID_CLIENTE = 830


def _suscripcion(severidades="[1, 2]", idcliente=ID_CLIENTE):
    PINOT_STORE["Dim_Plan"].append(
        {
            "idplan": idcliente,
            "nombre": "Profesional",
            "limites": json.dumps({"api_calls_mes": 10000, "api_calls_minuto": 120}),
            # El centinela real que tienen los planes sembrados.
            "severidades_desbloqueadas": "null",
            "activo": True,
        }
    )
    PINOT_STORE["Fact_Suscripcion"].append(
        {
            "id_suscripcion": idcliente,
            "idcliente": idcliente,
            "idplan": idcliente,
            "estado": "Activa",
            "activo": True,
            "fecha_inicio": 1,
            "severidades_desbloqueadas": severidades,
        }
    )


def _preferencias(zonas="[10, 20]", idcliente=ID_CLIENTE):
    # La columna real es `id_cliente`, con guion bajo.
    PINOT_STORE["Dim_Preferencias_Cliente"].append(
        {"id_cliente": idcliente, "zonas_geograficas": zonas}
    )


class _Geografia:
    """Doble de GeografiaRepository.

    `Fact_Accidente` **no tiene `idcondado`**: solo `idcalle`. El condado se
    resuelve por catálogo, igual que en `seguimiento`. Aquí se mapea directo
    para que el test hable de condados sin montar Dim_Calle y Dim_Ciudad.
    """

    def __init__(self, por_calle: dict[int, int] | None = None):
        self._por_calle = por_calle or {}

    def resolve_condado_from_idcalle(self, idcalle: int) -> int | None:
        return self._por_calle.get(int(idcalle))


def _servicio(calles_a_condados=None):
    return ConsumoDatosService(
        geografia=_Geografia(calles_a_condados or {100: 10, 200: 20, 900: 99})
    )


def _accidente(idaccidente, idseveridad, idcalle, fecha=1000):
    PINOT_STORE["Fact_Accidente"].append(
        {
            "idaccidente": idaccidente,
            "idseveridad": idseveridad,
            "idcalle": idcalle,
            "fechahoraaccidente": fecha,
            "activo": True,
        }
    )


class TestSeveridadesDelContrato:
    def test_lee_las_severidades_de_la_suscripcion_no_del_plan(
        self, mock_pinot, mock_kafka
    ):
        """Los 5 planes sembrados tienen el centinela `'null'`; leer de ahí
        dejaría a todo partner sin poder consumir nada."""
        # Arrange
        _suscripcion(severidades="[1, 2]")

        # Act
        severidades = ConsumoDatosService().severidades_habilitadas(ID_CLIENTE)

        # Assert
        assert severidades == {1, 2}

    def test_el_centinela_null_no_revienta(self, mock_pinot, mock_kafka):
        """`json.loads('null')` devuelve None; iterarlo lanzaría TypeError."""
        # Arrange
        _suscripcion(severidades="null")

        # Act / Assert — devuelve vacío, no explota
        assert ConsumoDatosService().severidades_habilitadas(ID_CLIENTE) == set()

    def test_un_json_invalido_tampoco_revienta(self, mock_pinot, mock_kafka):
        # Arrange
        _suscripcion(severidades="esto no es json")

        # Act / Assert
        assert ConsumoDatosService().severidades_habilitadas(ID_CLIENTE) == set()

    def test_sin_suscripcion_vigente_lanza(self, mock_pinot, mock_kafka):
        # Act / Assert
        with pytest.raises(ConsumoDatosError) as exc:
            ConsumoDatosService().severidades_habilitadas(999999)
        assert exc.value.code == "sin_suscripcion"

    def test_el_vocabulario_retirado_ya_no_habilita_nada(
        self, mock_pinot, mock_kafka
    ):
        """La escala paralela «Baja/Media/Alta» se retiró el 2026-08-11.

        Si una fila antigua se colara sin migrar, debe dar conjunto vacío —
        fail-closed — y nunca reinterpretarse como una severidad real.
        """
        # Arrange
        _suscripcion(severidades='["Media"]')

        # Act / Assert
        assert ConsumoDatosService().severidades_habilitadas(ID_CLIENTE) == set()


class TestZonasFailClosed:
    def test_cliente_sin_preferencias_no_recibe_nada(self, mock_pinot, mock_kafka):
        """No recibe «todo» por defecto: exponer siniestralidad de zonas no
        contratadas es una fuga de datos, no una comodidad."""
        # Arrange
        _suscripcion()
        _accidente(1, idseveridad=1, idcalle=100)

        # Act
        resultado = _servicio().consultar_accidentes(idcliente=ID_CLIENTE)

        # Assert
        assert resultado["items"] == []
        assert resultado["meta"]["zonas_aplicadas"] == []

    def test_zonas_vacias_tampoco_abren_el_acceso(self, mock_pinot, mock_kafka):
        # Arrange
        _suscripcion()
        _preferencias(zonas="[]")
        _accidente(1, idseveridad=1, idcalle=100)

        # Act
        resultado = _servicio().consultar_accidentes(idcliente=ID_CLIENTE)

        # Assert
        assert resultado["items"] == []

    def test_solo_devuelve_accidentes_de_las_zonas_contratadas(
        self, mock_pinot, mock_kafka
    ):
        # Arrange
        _suscripcion()
        _preferencias(zonas="[10]")
        _accidente(1, idseveridad=1, idcalle=100)
        _accidente(2, idseveridad=1, idcalle=900)

        # Act
        resultado = _servicio().consultar_accidentes(idcliente=ID_CLIENTE)

        # Assert
        assert [a["idaccidente"] for a in resultado["items"]] == [1]


class TestSeveridadFueraDeAlcance:
    def test_pedir_una_severidad_no_habilitada_lanza_403_no_lista_vacia(
        self, mock_pinot, mock_kafka
    ):
        """Lista vacía le diría «no hay accidentes graves», que es falso."""
        # Arrange — «Media» habilita {1,2}; se pide la 4
        _suscripcion(severidades="[1, 2]")
        _preferencias()

        # Act / Assert
        with pytest.raises(ConsumoDatosError) as exc:
            _servicio().consultar_accidentes(
                idcliente=ID_CLIENTE, idseveridad=4
            )
        assert exc.value.code == "severidad_no_habilitada"

    def test_pedir_una_severidad_habilitada_filtra_solo_esa(
        self, mock_pinot, mock_kafka
    ):
        # Arrange
        _suscripcion(severidades="[1, 2]")
        _preferencias(zonas="[10]")
        _accidente(1, idseveridad=1, idcalle=100)
        _accidente(2, idseveridad=2, idcalle=100)

        # Act
        resultado = _servicio().consultar_accidentes(
            idcliente=ID_CLIENTE, idseveridad=2
        )

        # Assert
        assert [a["idaccidente"] for a in resultado["items"]] == [2]

    def test_sin_pedir_severidad_devuelve_todas_las_habilitadas(
        self, mock_pinot, mock_kafka
    ):
        # Arrange
        _suscripcion(severidades="[1, 2]")
        _preferencias(zonas="[10]")
        _accidente(1, idseveridad=1, idcalle=100)
        _accidente(2, idseveridad=2, idcalle=100)
        _accidente(3, idseveridad=4, idcalle=100)

        # Act
        resultado = _servicio().consultar_accidentes(idcliente=ID_CLIENTE)

        # Assert — la severidad 4 no está en «Media»
        assert sorted(a["idaccidente"] for a in resultado["items"]) == [1, 2]


class TestResultadoExplicable:
    def test_meta_expone_las_zonas_y_severidades_aplicadas(
        self, mock_pinot, mock_kafka
    ):
        """Un resultado vacío tiene que ser explicable sin abrir la base."""
        # Arrange
        _suscripcion(severidades="[1]")
        _preferencias(zonas="[10, 20]")

        # Act
        meta = _servicio().consultar_accidentes(idcliente=ID_CLIENTE)["meta"]

        # Assert
        assert meta["zonas_aplicadas"] == [10, 20]
        assert meta["severidades_aplicadas"] == [1]
