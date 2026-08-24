"""Sonda de salud que comprueba de verdad sus dependencias (PG-RES-004).

**Una sonda que devuelve `200` sin comprobar nada es peor que no tenerla.** No
es una exageracion retorica: convierte una caida en un silencio. El orquestador
ve el servicio sano, no lo reinicia, no alerta a nadie, y las peticiones siguen
llegando a un proceso que no puede atenderlas. Sin sonda, al menos el primer
error de un usuario delata el problema.

Por eso aqui cada dependencia se **ejerce**, con una consulta trivial pero real:

| Dependencia | Comprobacion | Por que importa |
|---|---|---|
| Pinot | `SELECT 1 FROM Dim_Usuarios LIMIT 1` | Es la fuente de verdad; sin ella no hay lecturas |
| Kafka | productor accesible | Es el unico canal de escritura |
| ClickHouse | `SELECT 1` | Los informes tacticos salen de aqui |

**Distincion deliberada entre esencial y accesorio.** Que ClickHouse este caido
degrada los informes, pero **no impide registrar un accidente ni despachar una
unidad**. Marcar el servicio entero como no disponible por eso provocaria un
reinicio que no arregla nada y que si interrumpe la cadena critica. Solo las
dependencias esenciales tumban la sonda.
"""

from __future__ import annotations

from dataclasses import dataclass

#: Dependencias sin las cuales el sistema **no puede cumplir su funcion**: ni
#: registrar un accidente ni despachar una unidad. Su caida hace fallar la sonda.
ESENCIALES = ("pinot", "kafka")

#: Dependencias cuya caida **degrada** el servicio sin impedirlo. Se reportan,
#: no tumban la sonda.
ACCESORIAS = ("clickhouse",)


@dataclass(frozen=True)
class Comprobacion:
    nombre: str
    ok: bool
    detalle: str = ""

    @property
    def esencial(self) -> bool:
        return self.nombre in ESENCIALES


def _comprobar_pinot() -> Comprobacion:
    try:
        from core.pinot.client import PinotClient

        PinotClient().query("SELECT 1 FROM Dim_Usuarios LIMIT 1", {})
        return Comprobacion("pinot", True)
    except Exception as exc:  # noqa: BLE001 - cualquier fallo es indisponibilidad
        return Comprobacion("pinot", False, _resumir(exc))


def _comprobar_kafka() -> Comprobacion:
    try:
        from core.repositories.cuentas_clientes.kafka_writer import KafkaWriter

        # Construir el productor ya obliga a resolver el bootstrap server. No se
        # publica nada: una sonda no debe escribir en el bus de eventos.
        KafkaWriter()
        return Comprobacion("kafka", True)
    except Exception as exc:  # noqa: BLE001
        return Comprobacion("kafka", False, _resumir(exc))


def _comprobar_clickhouse() -> Comprobacion:
    try:
        from core.clickhouse.client import ClickHouseClient

        ClickHouseClient().query("SELECT 1", {})
        return Comprobacion("clickhouse", True)
    except Exception as exc:  # noqa: BLE001
        return Comprobacion("clickhouse", False, _resumir(exc))


def _resumir(exc: Exception) -> str:
    """Motivo acotado y sin rastros internos.

    La sonda suele quedar expuesta al orquestador y a veces a la red: un
    traceback aqui filtraria rutas, nombres de tabla y credenciales de conexion
    (PG-SEC-007).
    """
    return type(exc).__name__


def comprobar_todo() -> list[Comprobacion]:
    return [_comprobar_pinot(), _comprobar_kafka(), _comprobar_clickhouse()]


def esta_sano(comprobaciones: list[Comprobacion]) -> bool:
    """Solo las dependencias esenciales deciden."""
    return all(c.ok for c in comprobaciones if c.esencial)


def como_respuesta(comprobaciones: list[Comprobacion]) -> dict:
    return {
        "estado": "ok" if esta_sano(comprobaciones) else "degradado",
        "dependencias": {
            c.nombre: {
                "ok": c.ok,
                "esencial": c.esencial,
                **({"motivo": c.detalle} if not c.ok else {}),
            }
            for c in comprobaciones
        },
    }
