"""PG-RES-006 — ninguna migración sin vuelta atrás.

**Por qué importa más aquí que en un sistema con transacciones.** Estas tablas
son upsert por clave primaria y las migraciones **republican la fila entera**
—hay que hacerlo: publicar solo la columna que cambia dejaría el resto en su
valor por defecto—. Eso significa que una migración equivocada no corrompe un
campo: entierra el estado anterior de la fila completa, y Pinot no guarda la
versión previa. Sin un respaldo tomado *antes*, no hay a dónde volver.

**Lo que se encontró (2026-08-23).** De las 9 migraciones, 7 respaldaban y 2 no
(`migra_fecha_inicio_contrato`, `migra_severidades_plan_a_idseveridad`). El
patrón correcto estaba escrito a mano en cada una, así que las dos que se
saltaron el paso no rompieron nada visible — simplemente no tenían red. Se
extrajo a `database/_reversion.py` y se añadió a las dos.

Esta suite se construye sobre el listado real de `database/migra_*.py`: una
migración nueva entra sola en el recorrido, que es lo que evita que la próxima
nazca desprotegida.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
from django.conf import settings

pytestmark = [pytest.mark.unit, pytest.mark.seguridad]

BD = Path(settings.BASE_DIR).parent / "database"

#: Migraciones que **no** necesitan respaldo, con el motivo. Una entrada aquí es
#: una afirmación revisable, no una excepción para que la prueba calle: si el
#: motivo deja de ser cierto, la exención se nota al leerla.
SIN_RESPALDO_JUSTIFICADO: dict[str, str] = {
    "migra_dim_severidad.py": (
        "La tabla está VACÍA — es el motivo declarado de hacer el cambio ahora. "
        "No hay filas que respaldar, y recrear la tabla es la reversión. "
        "⚠️ Si algún día Dim_Severidad tuviera datos, esta exención deja de "
        "valer y hay que quitarla de aquí."
    ),
    "migra_partners_esquema.py": (
        "No toca Pinot: solo reescribe `esquemas.json` y `tablas.json`, que "
        "están versionados. El respaldo es git, y la reversión es un "
        "`git checkout` de esos dos ficheros — está escrito en su docstring."
    ),
}


def _migraciones() -> list[Path]:
    return sorted(BD.glob("migra_*.py"))


def _fuente(ruta: Path) -> str:
    return ruta.read_text(encoding="utf-8", errors="replace")


#: Formas de escribir que tiene una migración. La lista empezó con `publish(` y
#: dejaba escapar `migra_plan_programado.py`, que escribe con un POST al
#: controller de Pinot: la prueba lo saltaba **en silencio** dándolo por
#: solo-lectura. Un salto silencioso es exactamente el fallo que esta suite
#: persigue, así que la lista se amplió al detectarlo.
MARCAS_DE_ESCRITURA = (
    "publish(",
    "kafka-console-producer",
    "ingestFromFile",
    'pedir("POST"',
    'pedir("PUT"',
    'pedir("DELETE"',
    "/segments/",
    "/schemas/",
    # Reescribir `esquemas.json` / `tablas.json` también es escribir: no cambia
    # datos, pero cambia la forma con la que se leerán a partir de entonces.
    "write_text(",
)


def _escribe(fuente: str) -> bool:
    return any(marca in fuente for marca in MARCAS_DE_ESCRITURA)


def test_ninguna_migracion_se_salta_el_recorrido_entera():
    """Un `skip` de más deja una migración sin revisar y en verde.

    Ocurrió: `migra_plan_programado.py` escribe con un POST al controller de
    Pinot y la lista de marcas solo miraba `publish(`, así que se saltaba dándose
    por solo-lectura. Este aserto fija el número: si mañana otra migración deja
    de reconocerse como escritora, falla en vez de callar.
    """
    lectoras = [r.name for r in _migraciones() if not _escribe(_fuente(r))]
    assert not lectoras, (
        "Migraciones que ninguna marca reconoce como escritoras:\n  "
        + "\n  ".join(lectoras)
        + "\n\n  O de verdad no escriben —y conviene decirlo en el docstring— o "
        "escriben de una forma que `MARCAS_DE_ESCRITURA` no contempla, y se "
        "están saltando las tres comprobaciones sin que nadie lo vea."
    )


def test_hay_migraciones_que_revisar():
    """Control negativo: sin esto, la suite pasaría recorriendo una lista vacía.

    Es el modo de fallo de toda prueba construida sobre un glob — si el patrón
    deja de casar, todo queda en verde y nadie se entera.
    """
    assert len(_migraciones()) >= 9, (
        f"Solo {len(_migraciones())} migraciones encontradas en {BD}. El sistema "
        "tiene 9: probablemente falló el patrón de búsqueda."
    )


@pytest.mark.parametrize("ruta", _migraciones(), ids=lambda r: r.name)
def test_toda_migracion_respalda_antes_de_escribir(ruta: Path):
    """Escribir sin copia previa es una decisión irreversible tomada sin querer."""
    fuente = _fuente(ruta)

    if not _escribe(fuente):
        pytest.skip("No escribe: no hay nada que revertir.")

    if ruta.name in SIN_RESPALDO_JUSTIFICADO:
        pytest.skip(SIN_RESPALDO_JUSTIFICADO[ruta.name])

    assert "respaldar(" in fuente or "RESPALDOS" in fuente, (
        f"{ruta.name} escribe sin respaldar antes.\n\n"
        "  Las tablas son upsert por clave y se republica la fila entera: sin "
        "copia previa, el estado anterior queda enterrado y Pinot no guarda "
        "versiones. Usa `database/_reversion.py::respaldar`."
    )


@pytest.mark.parametrize("ruta", _migraciones(), ids=lambda r: r.name)
def test_toda_migracion_se_puede_ensayar_en_seco(ruta: Path):
    """Una migración que solo corre «de verdad» se ensaya en producción.

    Que es donde no se ensaya nada: se ejecuta y se ve qué pasa.
    """
    fuente = _fuente(ruta)
    if not _escribe(fuente):
        pytest.skip("No escribe: el ensayo en seco no aplica.")

    assert "dry_run" in fuente or "dry-run" in fuente, (
        f"{ruta.name} no ofrece `--dry-run`: la única forma de saber qué hace "
        "es dejar que lo haga."
    )


@pytest.mark.parametrize("ruta", _migraciones(), ids=lambda r: r.name)
def test_toda_migracion_explica_su_reversion(ruta: Path):
    """El docstring debe decir cómo se vuelve atrás.

    Quien ejecute la migración a las tres de la mañana con algo saliendo mal no
    va a leer el código para deducirlo.
    """
    fuente = _fuente(ruta)
    doc = (ast.get_docstring(ast.parse(fuente)) or "").lower()
    cuerpo = fuente.lower()

    pistas = ("revertir", "reversión", "reversion", "respaldo", "deshacer", "idempotente")
    assert any(p in doc for p in pistas) or any(p in cuerpo for p in pistas), (
        f"{ruta.name} no dice en ninguna parte cómo se vuelve atrás ni afirma "
        "ser idempotente."
    )


def test_el_respaldo_se_relee_antes_de_darlo_por_bueno():
    """Escribir el fichero no prueba que se haya escrito entero.

    Un disco lleno o una codificación rota producen un respaldo truncado que
    parece correcto hasta el día que hace falta. La comprobación cuesta un
    segundo y convierte «creo que hay copia» en «hay copia».
    """
    fuente = (BD / "_reversion.py").read_text(encoding="utf-8")

    assert "json.loads(destino.read_text" in fuente, (
        "`respaldar()` ya no relee el fichero: un respaldo truncado pasaría por "
        "bueno."
    )
    assert "RespaldoInvalidoError" in fuente, (
        "Un respaldo inválido debe abortar la migración, no avisar y seguir: "
        "abortar solo sale gratis mientras los datos siguen intactos."
    )


def test_las_excepciones_al_respaldo_estan_justificadas_una_a_una():
    """Si alguien exime una migración, tiene que escribir por qué.

    Es la misma disciplina que la allowlist de gitleaks (`PG-CFG-005`): una
    excepción sin motivo escrito es indistinguible de un descuido seis meses
    después.
    """
    vacias = [n for n, motivo in SIN_RESPALDO_JUSTIFICADO.items() if len(motivo.strip()) < 20]
    assert not vacias, (
        "Migraciones eximidas sin un motivo escrito de verdad: " + ", ".join(vacias)
    )
