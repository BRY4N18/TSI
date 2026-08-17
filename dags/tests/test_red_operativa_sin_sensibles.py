"""T015 — ninguna consulta de Red Operativa nombra dato sensible (FR-021).

Las exclusiones de este departamento son tres, y la tercera es la que se olvida:

* **Coordenadas** — la ubicación se expresa por nombre.
* **Contacto de proveedor** — teléfono y correo de quien opera la flota.
* **Identidad del validador** — quién aprobó o rechazó una región.

La tercera cuesta más de ver porque parece información de proceso y no de
persona. No lo es: un informe de validaciones desglosado por quien las firma es
un registro de decisiones individuales, y sobre él se juzga a personas por
resultados que dependen de las regiones que les tocaron.

⚠️ Se juzgan **identificadores**, no el texto entero. Buscar el fragmento en todo
el SQL confundiría `validaciones` con `validador`, y la única salida sería
estrechar el patrón — que es justo lo que no debe hacerse: tiene que seguir
cazando cualquier columna de persona que aparezca mañana.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.consultas import cargar, listar  # noqa: E402

DEPARTAMENTO = "red_operativa"
INFORMES = listar(DEPARTAMENTO)

PROHIBIDOS = (
    # Coordenadas.
    "latitud", "longitud", "coord", "geoloc",
    # Contacto de proveedor.
    "telefono", "celular", "correo", "email", "gmail", "contacto",
    # Identidad de persona, incluida la del validador.
    "idusuario", "usuario", "validador", "aprobador", "revisor", "responsable",
    "nombres", "apellidos", "identificacion", "cedula",
    # Texto libre interno.
    "observacion", "comentario", "descripcion_libre",
)

#: Identificadores que contienen un fragmento prohibido y **no son** dato
#: sensible. Se declaran uno a uno, con su razón, en vez de estrechar el patrón.
PERMITIDOS = {
    # `motivo_rechazo` es una **categoría** del rechazo, no el texto de quien lo
    # escribió: es lo que permite agrupar los rechazos por causa, que es el
    # informe. Si algún día trajera texto libre, deja de estar permitido.
    "motivo_rechazo", "motivos_rechazo",
}


def identificadores(informe: str) -> set[str]:
    """Los nombres que la consulta usa, sin comentarios y sin literales.

    Los literales se descartan porque son **valores**: `estado_nuevo = 'Activa'`
    compara contra un valor, no nombra una columna, y leerlo como columna haría
    fallar una consulta que no toca nada sensible.
    """
    texto = "\n".join(
        l for l in cargar(informe, departamento=DEPARTAMENTO).splitlines()
        if not l.strip().startswith("--")
    )
    return set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", re.sub(r"'[^']*'", " ", texto)))


def test_el_catalogo_no_esta_vacio():
    # Sin esto la comprobación de abajo pasaría sin mirar ninguna consulta.
    assert INFORMES


@pytest.mark.parametrize("informe", INFORMES)
def test_ninguna_consulta_nombra_dato_sensible(informe):
    for identificador in identificadores(informe):
        bajo = identificador.lower()
        if bajo in PERMITIDOS:
            continue
        for prohibido in PROHIBIDOS:
            assert prohibido not in bajo, (
                f"'{informe}' nombra '{identificador}', que contiene "
                f"'{prohibido}': es coordenada, contacto de proveedor, identidad "
                f"de persona o texto libre interno"
            )


def test_lo_permitido_es_categoria_y_no_texto_de_persona():
    """Una excepción mal puesta desactivaría el patrón para ese nombre.

    Si alguien añadiera `observaciones` a la lista para acallar un fallo, esto lo
    vería: lo permitido tiene que ser un motivo categorizado, no una nota.
    """
    for permitido in PERMITIDOS:
        assert permitido.startswith("motivo"), (
            f"'{permitido}' no parece una categoría de rechazo"
        )
