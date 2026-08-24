"""PG-RES-006 — respaldo verificado y ensayo en seco para las migraciones.

**El patrón ya existía, escrito a mano y solo en algunas.** `migra_factura_reclamo.py`
hacía lo correcto —exportar antes de tocar, releer el fichero para comprobar que
se escribió entero, y ofrecer `--dry-run`— pero copiado a mano, así que dos de
las nueve migraciones no lo tenían y nada lo señalaba.

**Por qué el respaldo se relee.** Escribir el fichero no prueba que se haya
escrito: un disco lleno o una codificación rota dan un respaldo truncado que
parece correcto hasta el día que hace falta. Releerlo y contar las filas cuesta
un segundo y convierte «creo que hay copia» en «hay copia».

**Por qué la reversión es un fichero y no un script inverso.** Estas tablas son
upsert por clave primaria: reponer el estado anterior es republicar las filas
originales tal cual. El respaldo *es* la reversión, y `revertir()` la aplica.
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import Any, Callable

RAIZ = Path(__file__).resolve().parent
RESPALDOS = RAIZ / "_respaldos"


class RespaldoInvalidoError(RuntimeError):
    """El respaldo no se pudo releer intacto: la migración no debe continuar."""


def respaldar(tabla: str, filas: list[dict[str, Any]], *, sufijo: str = "") -> Path:
    """Exporta las filas y **comprueba** que el fichero se puede releer entero.

    Se llama antes de escribir nada. Si algo falla aquí, la migración aborta con
    los datos todavía intactos — que es el único momento en el que abortar sale
    gratis.
    """
    RESPALDOS.mkdir(exist_ok=True)
    marca = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre = f"{tabla}{('_' + sufijo) if sufijo else ''}_{marca}.json"
    destino = RESPALDOS / nombre
    destino.write_text(json.dumps(filas, indent=2, ensure_ascii=False), encoding="utf-8")

    releido = json.loads(destino.read_text(encoding="utf-8"))
    if len(releido) != len(filas):
        raise RespaldoInvalidoError(
            f"{destino.name}: se escribieron {len(filas)} filas y se releyeron "
            f"{len(releido)}. La migración se aborta con los datos intactos."
        )
    return destino


def revertir(respaldo: Path, publicar: Callable[[dict[str, Any]], None]) -> int:
    """Republica las filas del respaldo, devolviendo el estado anterior.

    `publicar` es la función que envía una fila a Kafka. No se asume ninguna:
    cada migración escribe en su topic y es quien sabe cuál.
    """
    filas = json.loads(Path(respaldo).read_text(encoding="utf-8"))
    for fila in filas:
        publicar(fila)
    return len(filas)


def anadir_dry_run(parser) -> None:
    """El ensayo en seco, con la misma bandera y el mismo texto en todas.

    Una migración que solo se puede ejecutar «de verdad» se ensaya en
    producción, que es donde no se ensaya nada.
    """
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Calcula y muestra los cambios sin escribir nada (el respaldo sí se crea).",
    )
