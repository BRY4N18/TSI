"""`inicio_es_real` distingue una fecha observada de «desde la primera carga»
(T038, FR-021).

Es la columna que impide la mentira más cómoda del modelo: presentar *«no lo
sabemos»* como *«siempre fue así»*.

Sin ella, un informe que agrupe seis meses de despachos por proveedor —con un
versionado que empezó ayer— devolvería el proveedor actual para todo el período
**y parecería correcto**. Con ella, el informe puede decir «desde esta fecha la
atribución es exacta; antes, es el estado conocido al arrancar», que es honesto y
sigue siendo útil.
"""

import sys
from datetime import datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.dimensiones.dim_unidad import construir  # noqa: E402
from lib.dimensiones.reconstruccion import reconstruir_entidad  # noqa: E402
from lib.dimensiones.versionado import (  # noqa: E402
    ATRIBUTOS_VERSIONADOS_UNIDAD,
    INICIO_DESCONOCIDO,
    decidir_version,
)

AHORA = datetime(2026, 8, 14, 12, 0)
OBSERVADO = datetime(2026, 5, 20, 8, 30)

CLIENTES = [
    {"idcliente": 1, "nombre": "Proveedor A", "razon_social": "A"},
    {"idcliente": 2, "nombre": "Proveedor B", "razon_social": "B"},
]
CONDADOS = [{"idcondado": 1, "condado": "Cuauhtemoc"}]


def _origen(idcliente):
    return [
        {
            "idunidademergencia": 7,
            "unidademergencia": "Ambulancia 7",
            "placa": "ABC-123",
            "tipounidademergencia": "Ambulancia",
            "capacidad": "4",
            "idcliente": idcliente,
            "idcondado": 1,
            "zonacobertura": "Norte",
        }
    ]


class TestLoQueNoSeSabe:
    def test_la_primera_version_declara_que_su_inicio_no_es_real(self):
        filas = construir(_origen(1), CLIENTES, CONDADOS, [], AHORA)

        assert filas[0]["inicio_es_real"] == 0
        assert filas[0]["valido_desde"] == INICIO_DESCONOCIDO.strftime("%Y-%m-%d %H:%M:%S")

    def test_un_cambio_detectado_al_cargar_tampoco_declara_inicio_real(self):
        # El cambio pudo ocurrir en cualquier momento desde la carga anterior; lo
        # único que se sabe es que ya había ocurrido al mirar
        primera = construir(_origen(1), CLIENTES, CONDADOS, [], AHORA)
        cambio = construir(_origen(2), CLIENTES, CONDADOS, primera, AHORA)

        nueva = next(f for f in cambio if f["es_vigente"] == 1)
        assert nueva["inicio_es_real"] == 0


class TestLoQueSiSeSabe:
    def test_un_instante_aportado_produce_inicio_real(self):
        resultado = decidir_version(
            {"idunidademergencia": 7, "idcliente": 2, "proveedor": "B"},
            {"idunidademergencia": 7, "idcliente": 1, "proveedor": "A", "valido_desde": INICIO_DESCONOCIDO},
            clave_negocio="idunidademergencia",
            atributos=ATRIBUTOS_VERSIONADOS_UNIDAD,
            ahora=AHORA,
            instante_observado=OBSERVADO,
        )

        assert resultado.version_nueva["inicio_es_real"] == 1
        assert resultado.version_nueva["valido_desde"] == OBSERVADO

    def test_la_reconstruccion_marca_reales_solo_las_versiones_fechadas(self):
        # La primera sale del `estado_anterior` del primer evento: se conoce el
        # valor, no desde cuándo. Las siguientes sí tienen fecha.
        eventos = [
            {"estado_anterior": "Basico", "estado_nuevo": "Pro", "fechahora": OBSERVADO},
            {"estado_anterior": "Pro", "estado_nuevo": "Enterprise", "fechahora": AHORA},
        ]

        versiones = reconstruir_entidad(
            eventos,
            campo_anterior="estado_anterior",
            campo_nuevo="estado_nuevo",
            campo_instante="fechahora",
            ahora=AHORA,
        )

        assert [v["inicio_es_real"] for v in versiones] == [0, 1, 1]
        assert versiones[0]["valido_desde"] == INICIO_DESCONOCIDO
        assert versiones[1]["valido_desde"] == OBSERVADO


class TestLaUnidadNuncaPuedeDeclararInicioReal:
    def test_construir_rechaza_una_version_con_inicio_real(self, monkeypatch):
        # Es una afirmación sobre EL ORIGEN, no sobre este código: nada historiza
        # el cambio de unidad a proveedor. Si algún día lo hiciera, esto salta y
        # obliga a decidir conscientemente en vez de que la marca cambie de
        # significado sin que nadie lo advierta (T033).
        import lib.dimensiones.dim_unidad as modulo

        def versionado_mentiroso(*_args, **_kwargs):
            return [{"idunidademergencia": 7, "inicio_es_real": 1, "valido_desde": AHORA}]

        monkeypatch.setattr(modulo, "versionar_lote", versionado_mentiroso)

        with pytest.raises(ValueError, match="inicio_es_real"):
            construir(_origen(1), CLIENTES, CONDADOS, [], AHORA)
