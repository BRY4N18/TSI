"""PG-ANA-001 — el cuadre analítica ↔ operacional.

Dos suites en un fichero, y la separación es lo importante:

- Las **unitarias** comprueban la lógica del cuadre y que el registro de
  correspondencias no envejezca. Corren en cada PR.
- La **de integración** hace el cuadre de verdad, contra Pinot y ClickHouse
  reales. Es la única que puede detectar un informe falso, y por eso está
  marcada aparte: un doble devuelve lo que se le programó, así que cuadraría
  consigo mismo siempre.

Escribir solo las primeras y darlas por suficientes sería repetir el error de
`PG-SEC-005` (`changelog.md` C8): una suite verde que no mide lo que dice.
"""

from __future__ import annotations

import pytest

from core.seguridad.reconciliacion import (
    CORRESPONDENCIAS,
    LIMITE_EXTRACCION,
    Correspondencia,
    discrepancia,
    sql_conteo_analitico,
    sql_conteo_operacional,
)

# --- Lógica del cuadre (rápidas) ---------------------------------------------

unitarias = [pytest.mark.unit, pytest.mark.seguridad]


@pytest.mark.unit
@pytest.mark.seguridad
def test_un_cuadre_exacto_no_reporta_nada():
    """Control negativo: si `discrepancia` devolviera siempre un mensaje, todas
    las pruebas de abajo pasarían sin distinguir cuadrar de no cuadrar."""
    c = CORRESPONDENCIAS[0]
    assert discrepancia(1_000, 1_000, c) is None


@pytest.mark.unit
@pytest.mark.seguridad
@pytest.mark.parametrize("origen,analitica", [(100, 90), (100, 0), (100, 110)])
def test_cualquier_diferencia_se_reporta(origen, analitica):
    """Incluye el caso `analitica > origen`.

    Sobrar filas es tan grave como faltar: significa que la partición no se
    descartó antes de recargar y hay casos duplicados. El informe suma de más y
    nadie lo nota, que es la misma clase de mentira.
    """
    c = CORRESPONDENCIAS[0]
    assert discrepancia(origen, analitica, c) is not None


@pytest.mark.unit
@pytest.mark.seguridad
def test_el_mensaje_dice_de_que_lado_falla():
    """Un «no cuadra» sin dirección obliga a reconstruir el análisis entero."""
    c = CORRESPONDENCIAS[0]

    faltan = discrepancia(100, 90, c)
    sobran = discrepancia(90, 100, c)

    assert "faltan 10" in faltan, faltan
    assert "sobran 10" in sobran, sobran
    assert c.operacional in faltan and c.analitica in faltan


@pytest.mark.unit
@pytest.mark.seguridad
def test_alcanzar_el_tope_de_extraccion_se_avisa_aparte():
    """El modo de fallo más probable, y el que más despista.

    Cuando el origen supera `LIMITE`, la extracción trunca sin avisar y el cuadre
    falla por una razón que **no es un error de código**. Sin este aviso, alguien
    buscaría el fallo en la transformación durante horas.
    """
    c = CORRESPONDENCIAS[0]

    normal = discrepancia(1_000, 900, c)
    en_el_tope = discrepancia(LIMITE_EXTRACCION, LIMITE_EXTRACCION - 100, c)

    assert "tope de extraccion" not in normal
    assert "tope de extraccion" in en_el_tope


@pytest.mark.unit
@pytest.mark.seguridad
def test_la_tolerancia_por_defecto_es_cero():
    """Una tolerancia sin justificar es una discrepancia aceptada por comodidad.

    Si una tabla necesita margen, el motivo va en `nota` — no en el aserto, donde
    nadie lo vuelve a leer.
    """
    for c in CORRESPONDENCIAS:
        if c.tolerancia:
            assert c.nota, (
                f"{c.analitica} admite tolerancia {c.tolerancia} sin explicar por qué."
            )
        else:
            assert c.tolerancia == 0


# --- El registro no envejece --------------------------------------------------


@pytest.mark.unit
@pytest.mark.seguridad
def test_las_correspondencias_estan_bien_formadas():
    for c in CORRESPONDENCIAS:
        assert c.analitica.islower(), f"{c.analitica}: las tablas de ClickHouse van en minúsculas"
        assert c.operacional[0].isupper(), f"{c.operacional}: las de Pinot van capitalizadas"
        assert c.clave_analitica and c.clave_operacional
        assert c.fecha_operacional and c.fecha_analitica


@pytest.mark.unit
@pytest.mark.seguridad
def test_ningun_par_tabla_origen_se_declara_dos_veces():
    """La unicidad es del **par**, no de la tabla analitica.

    `hecho_evidencia` se cuadra en dos mitades —fotos contra `Dim_EvidenciaFoto`,
    notas contra `Dim_NotaAccidente`— porque guarda ambas cosas. Exigir una
    entrada por tabla obligaria a contarla entera contra un solo origen, que es
    justo el error que daba «sobran 49».
    """
    pares = [(c.analitica, c.operacional) for c in CORRESPONDENCIAS]
    duplicados = {p for p in pares if pares.count(p) > 1}
    assert not duplicados, f"Pares repetidos: {sorted(duplicados)}"


@pytest.mark.unit
@pytest.mark.seguridad
def test_el_sql_generado_acota_por_la_ventana_pedida():
    """Sin el filtro de fecha, el cuadre compararía totales históricos.

    Coincidirían casi siempre y la prueba pasaría sin mirar el período que
    importa — otra suite verde que no mide nada.
    """
    c = CORRESPONDENCIAS[0]

    operacional = sql_conteo_operacional(c, 1_700_000_000_000, 1_700_086_400_000)
    analitico = sql_conteo_analitico(c, "2026-01-01", "2026-01-31")

    assert "1700000000000" in operacional and "1700086400000" in operacional
    assert "2026-01-01" in analitico and "2026-01-31" in analitico
    assert f"COUNT(DISTINCT {c.clave_operacional})" in operacional
    assert f"COUNT(DISTINCT {c.clave_analitica})" in analitico


@pytest.mark.unit
@pytest.mark.seguridad
def test_se_cuenta_por_clave_distinta_y_no_por_filas():
    """`COUNT(*)` daría falsos negativos en cualquier tabla que agregue, y falsos
    positivos si el origen tiene duplicados por upsert."""
    c = CORRESPONDENCIAS[0]
    for sql in (
        sql_conteo_operacional(c, 0, 1),
        sql_conteo_analitico(c, "2026-01-01", "2026-01-02"),
    ):
        assert "COUNT(*)" not in sql, sql


@pytest.mark.unit
@pytest.mark.seguridad
def test_toda_tabla_de_hechos_del_modelo_esta_declarada_o_justificada():
    """Antienvejecimiento: una tabla nueva sin cuadre queda **señalada**.

    Sin esto, `hecho_*` se añaden con el tiempo y ninguna cuadra — el registro
    seguiría en verde midiendo tres tablas de veinte, que es exactamente la falsa
    sensación de cobertura que este plan existe para evitar.
    """
    from pathlib import Path

    from django.conf import settings

    ddl = Path(settings.BASE_DIR).parent / "dags" / "lib" / "ddl.py"
    if not ddl.exists():  # pragma: no cover - depende del checkout
        pytest.skip("dags/lib/ddl.py no disponible")

    import re

    declaradas = {c.analitica for c in CORRESPONDENCIAS}
    en_el_modelo = set(
        re.findall(r"CREATE TABLE IF NOT EXISTS (hecho_\w+)", ddl.read_text(encoding="utf-8"))
    )

    sin_cuadre = sorted(en_el_modelo - declaradas)
    assert not sin_cuadre, (
        f"{len(sin_cuadre)} tablas de hechos sin correspondencia declarada:\n  "
        + "\n  ".join(sin_cuadre)
        + "\n\nCada una es un informe que puede mentir sin que nada lo detecte. "
        "Añadirlas a CORRESPONDENCIAS en core/seguridad/reconciliacion.py."
    )


@pytest.mark.unit
@pytest.mark.seguridad
def test_las_columnas_declaradas_existen_en_los_esquemas_reales():
    """La prueba que impide que un nombre inventado pase por correspondencia.

    Los nombres se cruzaron a mano entre `ddl.py` y `esquemas.json`, y un solo
    error tipográfico produciría un fallo de cuadre que parecería un dato mal
    cargado. Distinguir «la tabla no cuadra» de «escribí mal la columna» cuesta
    horas si nadie lo comprueba aquí.
    """
    import json
    import re
    from pathlib import Path

    from django.conf import settings

    raiz = Path(settings.BASE_DIR).parent
    esquemas, ddl = raiz / "database" / "esquemas.json", raiz / "dags" / "lib" / "ddl.py"
    if not (esquemas.exists() and ddl.exists()):  # pragma: no cover
        pytest.skip("esquemas.json o ddl.py no disponibles")

    crudo = json.loads(esquemas.read_text(encoding="utf-8"))
    lista = crudo if isinstance(crudo, list) else list(crudo.values())
    operacional = {}
    for tabla in lista:
        if not isinstance(tabla, dict):
            continue
        nombre = tabla.get("schemaName") or tabla.get("tableName")
        if nombre:
            operacional[nombre] = {
                col["name"]
                for clave in ("dimensionFieldSpecs", "metricFieldSpecs", "dateTimeFieldSpecs")
                for col in tabla.get(clave, [])
            }

    texto = ddl.read_text(encoding="utf-8")
    analitico = {
        m.group(1): set(re.findall(r"^\s+(\w+)\s+\w", m.group(2), re.M))
        for m in re.finditer(
            r"CREATE TABLE IF NOT EXISTS (hecho_\w+)\s*\((.*?)\)\s*ENGINE", texto, re.S
        )
    }

    errores = []
    for c in CORRESPONDENCIAS:
        cols_op = operacional.get(c.operacional)
        cols_an = analitico.get(c.analitica)
        if cols_op is None:
            errores.append(f"{c.analitica}: la tabla origen {c.operacional} no está en esquemas.json")
            continue
        if cols_an is None:
            errores.append(f"{c.analitica}: no se declara en ddl.py")
            continue
        if c.clave_operacional not in cols_op:
            errores.append(f"{c.operacional}.{c.clave_operacional} no existe")
        if c.fecha_operacional not in cols_op:
            errores.append(f"{c.operacional}.{c.fecha_operacional} no existe")
        if c.clave_analitica not in cols_an:
            errores.append(f"{c.analitica}.{c.clave_analitica} no existe")
        if c.fecha_analitica not in cols_an:
            errores.append(f"{c.analitica}.{c.fecha_analitica} no existe")
        for op_med, an_med in c.medidas:
            if op_med not in cols_op:
                errores.append(f"{c.operacional}.{op_med} (medida) no existe")
            if an_med not in cols_an:
                errores.append(f"{c.analitica}.{an_med} (medida) no existe")

    assert not errores, "Correspondencias que apuntan a columnas inexistentes:\n  " + "\n  ".join(errores)
