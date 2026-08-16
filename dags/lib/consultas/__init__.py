"""Cargador del catálogo de consultas.

Un informe compuesto es **un fichero SQL**, no una cadena construida en Python.
La diferencia importa: la definición de lo que mide un informe vive en un solo
sitio, se lee entera de una vez y se compara entre versiones. Repartirla entre un
DAG y un repositorio es lo que hacía el diseño anterior, y es lo que permitía que
dos caminos calcularan lo mismo de forma distinta sin que nadie lo notara.

Aquí no se construye SQL: se lee.
"""

from __future__ import annotations

from pathlib import Path

RAIZ = Path(__file__).resolve().parent


class ConsultaNoEncontrada(FileNotFoundError):
    """El nombre pedido no corresponde a ningún fichero del catálogo."""


def cargar(nombre: str, *, departamento: str | None = None) -> str:
    """Devuelve el SQL del informe, tal como está escrito en su fichero.

    `nombre` va sin extensión: `ot21_distribucion_severidad`. `departamento` es
    el subdirectorio; omitirlo busca en la raíz, donde viven las tres consultas
    de la fase 6 del modelo.

    Falla con el **camino que buscó**, no con un `KeyError` pelado: quien se
    equivoca de nombre necesita saber dónde se miró para corregirlo, y un
    `KeyError` con el nombre mal escrito no dice nada que no supiera ya.
    """
    carpeta = RAIZ / departamento if departamento else RAIZ
    ruta = carpeta / f"{nombre}.sql"

    if not ruta.is_file():
        disponibles = sorted(p.stem for p in carpeta.glob("*.sql")) if carpeta.is_dir() else []
        raise ConsultaNoEncontrada(
            f"No existe la consulta '{nombre}' en {ruta}. "
            + (
                f"Disponibles en ese directorio: {', '.join(disponibles)}."
                if disponibles
                else "Ese directorio no contiene ninguna consulta."
            )
        )

    return ruta.read_text(encoding="utf-8")


def listar(departamento: str | None = None) -> list[str]:
    """Nombres de las consultas del catálogo, en orden estable.

    Lo usan las pruebas que recorren **todo** el catálogo —la de versión final,
    la de dato sensible, la de `ORDER BY`—: si una consulta nueva no apareciera
    aquí, esas pruebas dejarían de cubrirla sin fallar.
    """
    carpeta = RAIZ / departamento if departamento else RAIZ
    if not carpeta.is_dir():
        return []
    return sorted(p.stem for p in carpeta.glob("*.sql"))
