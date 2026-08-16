"""T047 — un centinela se presenta como **ausencia**, nunca como `0` ni fecha.

Pinot no almacena `NULL`: ninguna tabla del proyecto habilita
`nullHandlingEnabled`, así que una columna sin valor termina siendo el texto
`"null"` (STRING) o el mínimo del tipo (INT/LONG).

Estas pruebas **no miran el doble en memoria** (research D3). El fake de
`conftest.py` no coerciona nada, así que una prueba contra él no dice nada sobre
lo que ocurre en producción — y en el sentido contrario, tampoco detectaría que
la coerción real dejó de funcionar. Se verifica contra:

* `core/pinot/client.py:_coerce_value`, que es quien coerciona de verdad;
* `core/informes/formato.py`, la segunda línea de defensa por si un valor llega
  sin pasar por el cliente.

Por qué importa tanto
---------------------
Un centinela LONG mal interpretado no produce un valor raro, produce uno
**absurdo pero creíble en su tipo**: `-9223372036854775808` ms se convierte en
«hace 106.752.011.843 días». Ninguna comprobación de tipo lo rechaza, y en una
bandeja ordenada por antigüedad esa fila se va al primer puesto.
"""

from __future__ import annotations

import pytest

from core.informes.formato import a_entero_ms, a_fecha, a_iso, marca_ausente
from core.pinot.client import _coerce_value

SENTINELA_LONG = -9223372036854775808
SENTINELA_INT = -2147483648


class TestElClienteYaCoerciona:
    """research D3 — FR-021 se satisface sin código nuevo, apoyándose en esto."""

    def test_el_texto_null_de_un_string_es_none(self):
        assert _coerce_value("null", "STRING") is None

    def test_un_string_normal_se_conserva(self):
        # La coerción no puede tragarse un valor legítimo parecido.
        assert _coerce_value("nullo", "STRING") == "nullo"

    def test_el_minimo_de_int_es_none(self):
        assert _coerce_value(SENTINELA_INT, "INT") is None

    def test_el_minimo_de_long_es_none(self):
        assert _coerce_value(SENTINELA_LONG, "LONG") is None

    def test_un_cero_real_sigue_siendo_cero(self):
        # La distinción que FR-019 exige: ausencia no es cero.
        assert _coerce_value(0, "INT") == 0
        assert _coerce_value(0, "LONG") == 0

    @pytest.mark.parametrize("token", ["Infinity", "-Infinity", "NaN"])
    def test_los_no_finitos_son_none(self, token):
        assert _coerce_value(token, "DOUBLE") is None

    def test_el_limite_conocido_de_float_sigue_ahi(self):
        """research D3 lo documenta: FLOAT/DOUBLE no distinguen 0.0 de vacío.

        Ninguno de los ocho listados expone una métrica flotante, así que no les
        afecta — pero sí afectará a los compuestos, y fijarlo aquí evita que
        alguien asuma una garantía que no existe.
        """
        assert _coerce_value(0.0, "DOUBLE") == 0.0


class TestLaSegundaLineaDeDefensa:
    """`core/informes/formato.py`, por si un valor no pasó por el cliente."""

    @pytest.mark.parametrize("valor", [None, "", SENTINELA_LONG, SENTINELA_INT])
    def test_se_reconocen_como_ausencia(self, valor):
        assert marca_ausente(valor) is True

    @pytest.mark.parametrize("valor", [0, 1_786_000_000_000, "1786000000000"])
    def test_un_valor_real_no_es_ausencia(self, valor):
        assert marca_ausente(valor) is False

    def test_el_cero_epoch_es_un_valor_no_una_ausencia(self):
        # 1970-01-01 es una fecha rara pero real; ausencia es otra cosa.
        assert marca_ausente(0) is False
        assert a_iso(0) == "1970-01-01T00:00:00+00:00"

    @pytest.mark.parametrize("valor", [None, SENTINELA_LONG, SENTINELA_INT])
    def test_a_iso_devuelve_none_nunca_la_epoca(self, valor):
        # `1970-01-01` para un hito que no ocurrió es una fecha creíble que
        # nadie va a cuestionar — peor que no devolver nada.
        assert a_iso(valor) is None

    @pytest.mark.parametrize("valor", [None, SENTINELA_LONG])
    def test_a_fecha_devuelve_none(self, valor):
        assert a_fecha(valor) is None

    @pytest.mark.parametrize("valor", [None, SENTINELA_LONG])
    def test_a_entero_ms_devuelve_none_no_cero(self, valor):
        assert a_entero_ms(valor) is None

    def test_un_valor_no_interpretable_es_ausencia_no_una_excepcion(self):
        # Un endpoint de solo lectura no debe caerse por un dato corrupto.
        assert a_iso("no soy una fecha") is None


class TestLasDosLecturasNoPuedenDiscrepar:
    """La fecha mostrada y los días calculados salen del mismo criterio.

    Si cada una decidiera por su cuenta qué es ausencia, una fila podría salir
    con la fecha en `null` y a la vez con una antigüedad calculada — algo
    contradictorio y difícil de explicar a quien lo vea.
    """

    @pytest.mark.parametrize("valor", [None, "", SENTINELA_LONG, SENTINELA_INT, "basura"])
    def test_si_a_iso_da_none_a_entero_ms_tambien(self, valor):
        assert (a_iso(valor) is None) == (a_entero_ms(valor) is None)


class TestLaProhibicionDeIsNotNull:
    """FR-022 — `IS NOT NULL` como filtro de completitud es siempre cierto.

    Es independiente de la coerción: ésta ocurre **al leer el resultado**, no al
    filtrar. Pinot evalúa `IS NOT NULL` sobre el centinela, que existe, así que
    la condición nunca descarta nada. Es el defecto que hace que el informe de
    completitud de campos críticos mida la nada.
    """

    @pytest.mark.parametrize(
        "modulo",
        [
            "core.repositories.cuentas_clientes.informes_acceso_repository",
            "core.repositories.cuentas_clientes.informes_incorporacion_repository",
            "core.repositories.cuentas_clientes.informes_cuenta_repository",
        ],
    )
    def test_ningun_repositorio_de_informes_lo_usa(self, modulo):
        import importlib
        import inspect
        import re

        fuente = inspect.getsource(importlib.import_module(modulo))
        consultas = re.findall(r'"(SELECT [^"]+)"', fuente, re.IGNORECASE)

        for consulta in consultas:
            assert not re.search(r"IS\s+NOT\s+NULL", consulta, re.IGNORECASE), consulta
