"""Pruebas del versionado de dimensiones (T011).

Verifican la regla de la que depende la corrección histórica del modelo entero:
una versión nueva nace **solo** cuando algo cambió, y toda versión declara si su
fecha de inicio es real o solo el momento en que el modelo empezó a mirar.
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.dimensiones.versionado import (  # noqa: E402
    ATRIBUTOS_VERSIONADOS_UNIDAD,
    INICIO_DESCONOCIDO,
    decidir_version,
    sk_de_version,
    version_vigente_en,
    versionar_lote,
)

AHORA = datetime(2026, 8, 14, 12, 0, 0)
ANTES = datetime(2026, 2, 1, 0, 0, 0)


def _unidad(idcliente=1, proveedor="Proveedor A", **extra):
    fila = {
        "idunidademergencia": 7,
        "placa": "ABC-123",
        "idcliente": idcliente,
        "proveedor": proveedor,
        "idcondado": 10,
        "zona_cobertura": "Norte",
    }
    fila.update(extra)
    return fila


def _vigente(**extra):
    fila = _unidad()
    fila.update(
        sk_unidad=sk_de_version(7, ANTES),
        valido_desde=ANTES,
        valido_hasta=None,
        es_vigente=1,
        inicio_es_real=0,
        version=ANTES,
    )
    fila.update(extra)
    return fila


def _decidir(origen, vigente, **kwargs):
    return decidir_version(
        origen,
        vigente,
        clave_negocio="idunidademergencia",
        atributos=ATRIBUTOS_VERSIONADOS_UNIDAD,
        ahora=AHORA,
        **kwargs,
    )


class TestAtributoSinCambios:
    def test_no_abre_version_ni_escribe_nada(self):
        # Arrange: la fila del origen es idéntica a la versión vigente
        resultado = _decidir(_unidad(), _vigente())

        # Assert: el caso común no debe costar una escritura
        assert resultado.sin_cambios is True
        assert resultado.filas == []

    def test_un_atributo_no_versionado_cambiado_tampoco_abre_version(self):
        # Arrange: cambia la placa, que no está entre los atributos versionados
        resultado = _decidir(_unidad(placa="XYZ-999"), _vigente())

        # Assert: versionar por cualquier cambio llenaría la dimensión de ruido
        assert resultado.sin_cambios is True


class TestAtributoCambiado:
    def test_cierra_la_vigente_y_abre_una_nueva(self):
        # Arrange: la unidad pasa al proveedor B
        resultado = _decidir(_unidad(idcliente=2, proveedor="Proveedor B"), _vigente())

        # Assert
        assert resultado.sin_cambios is False
        assert len(resultado.filas) == 2

        cerrada = resultado.version_cerrada
        assert cerrada["valido_hasta"] == AHORA
        assert cerrada["es_vigente"] == 0
        assert cerrada["proveedor"] == "Proveedor A"

        nueva = resultado.version_nueva
        assert nueva["valido_desde"] == AHORA
        assert nueva["valido_hasta"] is None
        assert nueva["es_vigente"] == 1
        assert nueva["proveedor"] == "Proveedor B"

    def test_la_vigencia_no_deja_hueco_ni_solapa(self):
        # Arrange
        resultado = _decidir(_unidad(idcliente=2, proveedor="Proveedor B"), _vigente())

        # Assert: el cierre de una y el inicio de la otra son el MISMO instante.
        # Un hueco perdería los despachos de ese intervalo; un solapamiento los
        # contaría dos veces.
        assert resultado.version_cerrada["valido_hasta"] == resultado.version_nueva["valido_desde"]

    def test_las_dos_versiones_tienen_claves_distintas(self):
        # Arrange
        resultado = _decidir(_unidad(idcliente=2, proveedor="Proveedor B"), _vigente())

        # Assert: es lo que permite que cada despacho conserve su proveedor
        assert resultado.version_cerrada["sk_unidad"] != resultado.version_nueva["sk_unidad"]


class TestPrimeraVersion:
    def test_lleva_inicio_es_real_cero(self):
        # Arrange: la entidad no existía en el modelo
        resultado = _decidir(_unidad(), None)

        # Assert: no se sabe desde cuándo es así, y la marca lo declara
        assert resultado.version_cerrada is None
        assert resultado.version_nueva["inicio_es_real"] == 0

    def test_abre_por_la_izquierda_para_cubrir_el_historico(self):
        # Arrange
        resultado = _decidir(_unidad(), None)

        # Assert: si la primera versión empezara en el instante de la carga,
        # NINGÚN hecho anterior tendría versión que lo cubriera y todos se
        # atribuirían a "desconocido" — el modelo perdería de golpe la
        # atribución del histórico completo, que es peor que el defecto que vino
        # a corregir.
        assert resultado.version_nueva["valido_desde"] == INICIO_DESCONOCIDO
        assert INICIO_DESCONOCIDO < ANTES < AHORA

    def test_un_cambio_detectado_al_cargar_tampoco_es_real(self):
        # Arrange: se detecta un cambio, pero nadie sabe CUÁNDO ocurrió
        resultado = _decidir(_unidad(idcliente=2, proveedor="Proveedor B"), _vigente())

        # Assert: solo se sabe que ya había ocurrido al mirar
        assert resultado.version_nueva["inicio_es_real"] == 0

    def test_solo_un_instante_aportado_produce_inicio_real(self):
        # Arrange: el origen SÍ historizó el cambio y se conoce su fecha
        observado = datetime(2026, 5, 20, 8, 30)
        resultado = _decidir(
            _unidad(idcliente=2, proveedor="Proveedor B"),
            _vigente(),
            instante_observado=observado,
        )

        # Assert
        assert resultado.version_nueva["inicio_es_real"] == 1
        assert resultado.version_nueva["valido_desde"] == observado
        assert resultado.version_cerrada["valido_hasta"] == observado


class TestVersionVigenteEn:
    def test_la_primera_version_cubre_todo_el_pasado(self):
        # Es la garantía que hace útil el modelo desde el día uno
        primera = _decidir(_unidad(), None).version_nueva
        assert version_vigente_en([primera], ANTES) is primera

    def test_tras_un_cambio_cada_lado_cae_en_su_version(self):
        # Arrange: una unidad que cambia de proveedor AHORA
        primera = _decidir(_unidad(), None).version_nueva
        cambio = _decidir(
            _unidad(idcliente=2, proveedor="Proveedor B"),
            primera,
        )
        versiones = [cambio.version_cerrada, cambio.version_nueva]

        # Assert: el pasado conserva el proveedor A, el presente ve el B
        assert version_vigente_en(versiones, ANTES)["proveedor"] == "Proveedor A"
        assert version_vigente_en(versiones, datetime(2027, 1, 1))["proveedor"] == "Proveedor B"

    def test_el_instante_exacto_del_cambio_cae_en_la_nueva_y_solo_en_ella(self):
        # Arrange
        primera = _decidir(_unidad(), None).version_nueva
        cambio = _decidir(_unidad(idcliente=2, proveedor="Proveedor B"), primera)
        versiones = [cambio.version_cerrada, cambio.version_nueva]

        # Assert: con ambos extremos cerrados, un despacho ocurrido justo en ese
        # instante encajaría en dos versiones y se contaría dos veces
        cubren = [v for v in versiones if version_vigente_en([v], AHORA) is not None]
        assert len(cubren) == 1
        assert cubren[0]["proveedor"] == "Proveedor B"


class TestClaveSustituta:
    def test_es_determinista(self):
        # Recargar el mismo período debe producir la MISMA clave, o el hecho
        # quedaría apuntando a una versión huérfana
        assert sk_de_version(7, ANTES) == sk_de_version(7, ANTES)

    def test_distingue_entidad_e_instante(self):
        assert sk_de_version(7, ANTES) != sk_de_version(8, ANTES)
        assert sk_de_version(7, ANTES) != sk_de_version(7, AHORA)

    def test_nunca_colisiona_con_la_clave_desconocida(self):
        # `0` está reservado a la fila desconocida
        assert sk_de_version(7, ANTES) != 0

    def test_cabe_en_un_entero_sin_signo_de_64_bits(self):
        assert 0 < sk_de_version(7, ANTES) < 2**64


class TestLote:
    def test_solo_devuelve_filas_de_lo_que_cambio(self):
        # Arrange: tres unidades, una sola cambia de proveedor
        origen = [
            {**_unidad(), "idunidademergencia": 1},
            {**_unidad(), "idunidademergencia": 2},
            {**_unidad(idcliente=2, proveedor="Proveedor B"), "idunidademergencia": 3},
        ]
        vigentes = {
            1: {**_vigente(), "idunidademergencia": 1},
            2: {**_vigente(), "idunidademergencia": 2},
            3: {**_vigente(), "idunidademergencia": 3},
        }

        # Act
        filas = versionar_lote(
            origen,
            vigentes,
            clave_negocio="idunidademergencia",
            atributos=ATRIBUTOS_VERSIONADOS_UNIDAD,
            ahora=AHORA,
        )

        # Assert: 2 filas (el cierre y la apertura de la unidad 3), no 6
        assert len(filas) == 2
        assert {f["idunidademergencia"] for f in filas} == {3}

    def test_una_entidad_nueva_produce_solo_su_apertura(self):
        # Act
        filas = versionar_lote(
            [{**_unidad(), "idunidademergencia": 99}],
            {},
            clave_negocio="idunidademergencia",
            atributos=ATRIBUTOS_VERSIONADOS_UNIDAD,
            ahora=AHORA,
        )

        # Assert
        assert len(filas) == 1
        assert filas[0]["es_vigente"] == 1
        assert filas[0]["inicio_es_real"] == 0
