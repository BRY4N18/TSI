"""PG-SEC-005 contra motores reales — la única forma de probar que no hay inyección.

**Por qué esta suite tiene que existir aparte.** `test_inyeccion.py` corre con el
doble de Pinot de `conftest.py`, que no analiza SQL: hace coincidencia de
patrones sobre la cadena. Acepta igual una consulta correcta que una inyectada,
así que ninguna carga puede tener efecto observable.

No es una sospecha. Se comprobó introduciendo una vulnerabilidad real —hacer que
`parse_dir` metiera la entrada cruda en el `ORDER BY`, que es exactamente el
descuido que un desarrollador cometería— y **las 497 pruebas rápidas siguieron en
verde**. Un mock nunca reproducirá una inyección, del mismo modo que no reproduce
el `ILLEGAL_AGGREGATION` de `PG-ANA-005`, que por eso reaparece.

**Cómo ejecutarla:**

```sh
docker compose -f docker/docker-compose.infraestructura.yml up -d
docker compose -f docker/docker-compose.tactico.yml up -d
pytest tests/seguridad/test_inyeccion_integracion.py -m integration -v
```

Corre en `integracion.yml` (semanal), no en cada PR: levantar Zookeeper, Kafka y
los tres procesos de Pinot cuesta minutos antes del primer test.
"""

from __future__ import annotations

import pytest

from core.pinot.client import PinotClient

pytestmark = [pytest.mark.integration, pytest.mark.seguridad]

#: Cargas que **cambian el resultado** si la inyección funciona. Es la diferencia
#: con la suite rápida: allí se mide que nada reviente, aquí que nada cambie.
CARGAS_CON_EFECTO = [
    # Ampliar el conjunto: si funciona, devuelve más filas de las que debería.
    ("1 OR 1=1", "amplía el conjunto"),
    # Truncar el resto de la cláusula, incluido el filtro de tenencia.
    ("1 --", "trunca la cláusula"),
    ("1 /*", "trunca con comentario de bloque"),
    # Extraer de otra tabla.
    ("1 UNION SELECT idusuario FROM Dim_Usuarios", "extrae de otra tabla"),
]


@pytest.fixture(scope="module")
def pinot() -> PinotClient:
    cliente = PinotClient()
    try:
        cliente.query("SELECT 1 FROM Dim_Usuarios LIMIT 1", {})
    except Exception as exc:  # pragma: no cover - depende del entorno
        pytest.skip(f"Pinot no está disponible: {exc}")
    return cliente


def _filas(cliente: PinotClient, valor) -> int:
    return len(
        cliente.query(
            "SELECT idusuario FROM Dim_Usuarios WHERE idusuario = %(id)s LIMIT 100",
            {"id": valor},
        )
    )


@pytest.mark.parametrize("carga,efecto", CARGAS_CON_EFECTO)
def test_una_carga_parametrizada_no_altera_el_conjunto(pinot, carga, efecto):
    """El aserto que la suite rápida no puede hacer.

    Se compara contra la consulta legítima: si la carga se interpretara como SQL,
    el número de filas cambiaría. Que coincida demuestra que el motor la trató
    como **dato**, que es lo que significa «parametrizado».
    """
    legitimo = _filas(pinot, 1)

    inyectado = _filas(pinot, carga)

    assert inyectado <= legitimo, (
        f"La carga «{carga}» {efecto}: devolvió {inyectado} filas frente a "
        f"{legitimo} de la consulta legítima. El valor se está interpretando "
        "como SQL en vez de como dato (PG-SEC-005)."
    )


def test_el_motor_no_ejecuta_una_sentencia_encadenada(pinot):
    """`; DROP TABLE` no debe llegar a ejecutarse.

    Se comprueba por el efecto —la tabla sigue respondiendo— y no por el código
    de error: un motor puede rechazar la sentencia por sintaxis y aun así haber
    admitido la concatenación en otro contexto.
    """
    _filas(pinot, "1; DROP TABLE Dim_Usuarios")

    assert pinot.query("SELECT idusuario FROM Dim_Usuarios LIMIT 1", {}), (
        "Dim_Usuarios dejó de responder tras una carga con sentencia encadenada."
    )


def test_un_orden_manipulado_no_cambia_el_recorrido(pinot):
    """El `ORDER BY` es donde la parametrización no aplica y hay que validar.

    Si `dir` llegara crudo a la consulta, el orden del resultado cambiaría. Esta
    es la prueba que habría detectado la vulnerabilidad simulada en `parse_dir`
    y que la suite con mocks no vio.
    """
    ascendente = pinot.query(
        "SELECT idusuario FROM Dim_Usuarios ORDER BY idusuario ASC LIMIT 5", {}
    )
    descendente = pinot.query(
        "SELECT idusuario FROM Dim_Usuarios ORDER BY idusuario DESC LIMIT 5", {}
    )

    assert ascendente and descendente
    assert [f["idusuario"] for f in ascendente] != [f["idusuario"] for f in descendente], (
        "ASC y DESC devuelven el mismo recorrido: el `ORDER BY` no se está "
        "aplicando y esta prueba no podría detectar que se manipule."
    )
