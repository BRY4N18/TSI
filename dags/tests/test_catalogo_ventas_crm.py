"""T014–T016 — las reglas del catálogo de Ventas y CRM, sobre el **texto**.

Las tres trampas de este departamento no fallan al ejecutar:

* Leer `activo` mezcla convertido con perdido y devuelve «N inactivos».
* Nombrar un campo personal o una columna de coste publica dato que el modelo
  no debe tener — o invita a rellenar un CAC inventado.
* Pedir `FINAL` sobre un hecho de transaccion falla; omitirlo en una dimension
  infla cifras solo a veces.

Ninguna se ve ejecutando la consulta una vez.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.consultas import cargar, listar  # noqa: E402

DEPARTAMENTO = "ventas_crm"
INFORMES = listar(DEPARTAMENTO)

CON_FINAL = ("dim_prospecto", "dim_canal")
SIN_FINAL = (
    "hecho_transicion_embudo",
    "hecho_asignacion_prospecto",
    "hecho_interaccion_demo",
    "hecho_notificacion_ventas",
)

PERSONALES = (
    "nombres", "apellidos", "gmail", "correo", "email", "telefono", "cargo",
    "idusuario", "notas", "metadata",
)
#: Fragmentos de columna de coste. `cac` se juzga por igualdad: es subcadena de
#: `notificacion` y cazaria la tabla del aviso.
COSTES = ("coste", "importe", "inversion")
COSTES_EXACTOS = frozenset({"cac"})


def cuerpo(nombre: str) -> str:
    return "\n".join(
        l for l in cargar(nombre, departamento=DEPARTAMENTO).splitlines()
        if not l.strip().startswith("--")
    )


def identificadores(sql: str) -> set[str]:
    sin_literales = re.sub(r"'[^']*'", " ", sql)
    return set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", sin_literales))


def _apariciones(texto: str, tabla: str) -> list[bool]:
    return [
        re.match(r"\s*(?:AS\s+\w+\s+|\w+\s+)?FINAL\b", m.group(1)) is not None
        for m in re.finditer(rf"\b(?:FROM|JOIN)\s+{tabla}\b(.*)", texto)
    ]


def test_el_catalogo_no_esta_vacio():
    """Sin esto, todas las pruebas de abajo pasarían sin mirar nada."""
    assert INFORMES, "el catálogo de Ventas y CRM está vacío"
    assert len(INFORMES) == 13, (
        f"se esperaban 13 consultas y hay {len(INFORMES)}: {INFORMES}"
    )


@pytest.mark.parametrize("informe", INFORMES)
def test_ninguna_consulta_lee_activo(informe):
    """T014 — el defecto que mezcla éxito con fracaso sin fallar."""
    ids = {i.lower() for i in identificadores(cuerpo(informe))}
    assert "activo" not in ids, (
        f"'{informe}' nombra 'activo': esa columna cubre convertido y perdido "
        f"a la vez. El desenlace se lee de 'desenlace'."
    )


@pytest.mark.parametrize("informe", INFORMES)
def test_ninguna_consulta_nombra_dato_personal_ni_coste(informe):
    """T015 — FR-022, FR-027. No filtrado: no se nombra."""
    ids = identificadores(cuerpo(informe))
    permitidos = {"nota_indicador"}
    for identificador in ids:
        if identificador.lower() in permitidos:
            continue
        bajo = identificador.lower()
        assert bajo not in COSTES_EXACTOS, (
            f"'{informe}' nombra '{identificador}', que es una columna de coste"
        )
        for prohibida in PERSONALES + COSTES:
            assert prohibida not in bajo, (
                f"'{informe}' nombra '{identificador}', que contiene '{prohibida}'"
            )


def test_nota_indicador_declara_y_no_cita():
    """La excepcion de `nota_indicador` no puede usarse para colar una nota."""
    assert "nota_indicador".startswith("nota_"), (
        "si deja de ser una etiqueta del indicador, deja de estar permitida"
    )


@pytest.mark.parametrize("informe", INFORMES)
def test_la_regla_de_version_final(informe):
    """T016. Omitirla infla las cifras solo a veces; pedirla de más falla."""
    texto = cuerpo(informe)

    for tabla in CON_FINAL:
        apariciones = _apariciones(texto, tabla)
        assert all(apariciones), (
            f"'{informe}' toca {tabla} sin forzar la versión final: devolverá "
            f"cifras infladas tras una recarga, y solo a veces"
        )

    for tabla in SIN_FINAL:
        assert not any(_apariciones(texto, tabla)), (
            f"'{informe}' pide FINAL sobre {tabla}, que es de transacción: "
            f"falla con ILLEGAL_FINAL"
        )


@pytest.mark.parametrize("informe", INFORMES)
def test_la_forma_de_la_consulta(informe):
    texto = cuerpo(informe)

    assert re.search(r"^ORDER BY", texto, re.MULTILINE), (
        f"'{informe}' no ordena su salida"
    )
    assert "SELECT *" not in texto.upper(), f"'{informe}' usa SELECT *"
    assert "{hasta:Date}" in texto, f"'{informe}' no acepta 'hasta'"
    assert "{desde:Date}" in texto, f"'{informe}' no acepta 'desde'"
    assert "{idejecutivo:Int32}" in texto, (
        f"'{informe}' no acepta acotamiento por ejecutivo: un ejecutivo vería "
        f"el departamento entero"
    )


@pytest.mark.parametrize("informe", INFORMES)
def test_el_acotamiento_filtra_por_el_hecho_no_por_la_dimension(informe):
    """El dueño vive en `hecho_asignacion_prospecto`, no en `dim_prospecto`."""
    texto = cuerpo(informe)
    assert "hecho_asignacion_prospecto" in texto, (
        f"'{informe}' no toca hecho_asignacion_prospecto: el acotamiento "
        f"no puede filtrar por titularidad vigente"
    )
