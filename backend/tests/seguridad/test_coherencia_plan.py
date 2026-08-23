"""PG-DOC-001 — el plan de pruebas no puede mentir sobre sí mismo.

Un plan que declara cobertura que no tiene es peor que no tener plan: se cuenta
como control existente al evaluar el riesgo y nadie vuelve a mirarlo. Ya pasó dos
veces en este documento — la tabla de cobertura se desvió del contenido
(decía 10/19/28 con 8/18/31 reales), y una regla apuntaba a un script suelto como
si fuera una prueba automatizada.

La disciplina de mantenerlo a mano no funcionó. Esto lo comprueba.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from django.conf import settings

pytestmark = [pytest.mark.unit, pytest.mark.seguridad]

PLAN = Path(settings.BASE_DIR).parent / "specs" / "Global" / "PlanPruebas" / "spec.md"
TRAZA = PLAN.parent / "traceability.md"

#: Cabecera de regla: `### PG-AREA-NNN — Título` seguida de severidad y estado.
REGLA = re.compile(
    r"^### (PG-[A-Z]+-\d+) — (.+?)\n"
    r"\*\*Severidad:\*\* (\w+) · \*\*Estado:\*\* (✅|⚠️|❌)[^·\n]*· \*\*Prueba:\*\* (.+?)$",
    re.M,
)

SEVERIDADES = {"Bloqueante", "Mayor", "Menor"}


@pytest.fixture(scope="module")
def reglas():
    texto = PLAN.read_text(encoding="utf-8")
    encontradas = REGLA.findall(texto)
    cabeceras = re.findall(r"^### (PG-[A-Z]+-\d+)", texto, re.M)

    faltan = set(cabeceras) - {r[0] for r in encontradas}
    assert not faltan, (
        f"Reglas sin los cuatro campos obligatorios: {sorted(faltan)}. "
        "Cada regla nace con ID, severidad, estado y prueba (PG-DOC-001)."
    )
    return encontradas


def test_toda_regla_declara_severidad_valida(reglas):
    for rid, _tit, sev, _est, _prueba in reglas:
        assert sev in SEVERIDADES, f"{rid} tiene severidad «{sev}»"


def test_ningun_identificador_se_repite(reglas):
    ids = [r[0] for r in reglas]
    duplicados = {i for i in ids if ids.count(i) > 1}
    assert not duplicados, (
        f"Identificadores repetidos: {sorted(duplicados)}. Un ID se referencia "
        "desde commits y trazabilidad; reutilizarlo rompe el rastro."
    )


def test_una_regla_cubierta_apunta_a_una_prueba_que_existe(reglas):
    """El fallo más silencioso posible: ✅ apuntando a un fichero borrado.

    La regla figura como cubierta, el recuento la suma, y no hay nada
    ejecutándose. Se comprueban solo las ✅ porque las ⚠️ pueden apuntar a
    cobertura dispersa descrita en prosa.
    """
    raiz = Path(settings.BASE_DIR)
    huerfanas = []

    for rid, _tit, _sev, estado, prueba in reglas:
        if estado != "✅":
            continue
        for ruta in re.findall(r"`([^`]+\.(?:py|ts|yml|yaml))`", prueba):
            limpia = ruta.split("::")[0].lstrip("/")
            candidatas = [raiz / limpia, raiz.parent / limpia, raiz / limpia.removeprefix("backend/")]
            if not any(c.exists() for c in candidatas):
                huerfanas.append(f"{rid} -> {ruta}")

    assert not huerfanas, (
        "Reglas marcadas ✅ cuya prueba no existe:\n  " + "\n  ".join(huerfanas)
    )


def test_el_recuento_del_plan_coincide_con_sus_reglas(reglas):
    """La tabla de cobertura se editaba a mano y se desvió del contenido.

    Es el mismo fallo que el plan denuncia en el sistema —afirmar cobertura sin
    comprobarla— cometido dentro del propio plan.
    """
    texto = PLAN.read_text(encoding="utf-8")
    fila = re.search(
        r"\| \*\*Total\*\* \| \*\*(\d+)\*\* \| \*\*(\d+)\*\* \| \*\*(\d+)\*\* \| \*\*(\d+)\*\* \|",
        texto,
    )
    assert fila, "El plan no declara una fila de totales."

    total, ok, parcial, pendiente = (int(g) for g in fila.groups())
    estados = [r[3] for r in reglas]

    assert total == len(reglas), f"La tabla dice {total} reglas y hay {len(reglas)}"
    assert ok == estados.count("✅"), f"Tabla ✅={ok}, real={estados.count('✅')}"
    assert parcial == estados.count("⚠️"), f"Tabla ⚠️={parcial}, real={estados.count('⚠️')}"
    assert pendiente == estados.count("❌"), f"Tabla ❌={pendiente}, real={estados.count('❌')}"


def test_la_trazabilidad_cubre_las_mismas_reglas_que_el_plan(reglas):
    """`traceability.md` se genera desde el plan; si divergen, alguien lo editó."""
    traza = TRAZA.read_text(encoding="utf-8")
    en_traza = set(re.findall(r"\| `(PG-[A-Z]+-\d+)`", traza))
    en_plan = {r[0] for r in reglas}

    assert en_plan == en_traza, (
        f"Plan y trazabilidad no coinciden.\n"
        f"  Solo en el plan: {sorted(en_plan - en_traza)}\n"
        f"  Solo en la traza: {sorted(en_traza - en_plan)}\n"
        "Regenerar traceability.md desde el spec; no se edita a mano."
    )


def test_toda_bloqueante_pendiente_dice_que_le_falta(reglas):
    """Una ❌ sin explicación es una intención, no deuda gestionable.

    La diferencia práctica: con el «qué falta» escrito, otra persona puede
    retomarla; sin él, hay que reconstruir el análisis entero.
    """
    texto = PLAN.read_text(encoding="utf-8")
    mudas = []

    for rid, _tit, sev, estado, _prueba in reglas:
        if sev != "Bloqueante" or estado == "✅":
            continue
        inicio = texto.index(f"### {rid} ")
        fin = texto.find("\n### ", inicio + 1)
        cuerpo = texto[inicio : fin if fin != -1 else len(texto)]
        if not re.search(r"Pendiente para|Prueba esperada|Regla:|Acción:", cuerpo):
            mudas.append(rid)

    assert not mudas, (
        f"Bloqueantes abiertas sin decir qué les falta: {mudas}"
    )
