"""Lector del catálogo de consultas desde Django.

Las consultas viven en `dags/lib/consultas/`, junto al modelo que consultan, y no
en este repositorio: es una decisión del plan, para que la definición de un
informe y el esquema que la sostiene no evolucionen por separado. Django las
**lee**; el único escritor del almacén sigue siendo Airflow.

Es el mismo catálogo que carga `dags/lib/consultas/__init__.py`, leído desde el
otro lado del montaje. No es una copia: si lo fuera, las dos divergirían, que es
exactamente el fallo que este módulo sustituye.
"""

from __future__ import annotations

from pathlib import Path

from django.conf import settings


class ConsultaNoEncontrada(FileNotFoundError):
    """El nombre pedido no corresponde a ningún fichero del catálogo."""


def _raiz() -> Path:
    return Path(settings.CONSULTAS_DIR)


def cargar(nombre: str, *, departamento: str | None = None) -> str:
    """Devuelve el SQL del informe, tal como está escrito en su fichero.

    Falla con el **camino que buscó** y las consultas disponibles, no con un
    `KeyError` pelado: cuando el catálogo no está montado, el síntoma es
    idéntico al de un nombre mal escrito, y la ruta es lo único que los
    distingue.
    """
    carpeta = _raiz() / departamento if departamento else _raiz()
    ruta = carpeta / f"{nombre}.sql"

    if not ruta.is_file():
        disponibles = listar(departamento)
        raise ConsultaNoEncontrada(
            f"No existe la consulta '{nombre}' en {ruta}. "
            + (
                f"Disponibles en ese directorio: {', '.join(disponibles)}."
                if disponibles
                else "Ese directorio no contiene ninguna consulta "
                "(¿está montado el catálogo? CONSULTAS_DIR="
                f"{settings.CONSULTAS_DIR})."
            )
        )

    return ruta.read_text(encoding="utf-8")


def listar(departamento: str | None = None) -> list[str]:
    """Nombres de las consultas del catálogo, en orden estable."""
    carpeta = _raiz() / departamento if departamento else _raiz()
    if not carpeta.is_dir():
        return []
    return sorted(p.stem for p in carpeta.glob("*.sql"))
