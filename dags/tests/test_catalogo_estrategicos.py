"""T004, T018–T021 — el catálogo anidado de OE6 y las reglas sobre su texto.

Estas pruebas miran **el texto**, no el resultado. Los fallos que vigilan no se
ven ejecutando la consulta una vez: un JOIN con `dim_region` duplica cada caso
sin fallar; un `FINAL` omitido infla cifras solo a veces; un `FINAL` de más
sobre `hecho_evidencia` falla con `ILLEGAL_FINAL`.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.consultas import ConsultaNoEncontrada, cargar, listar  # noqa: E402

DEPARTAMENTO = "estrategicos/oe6"

TABLAS_CON_FINAL = ("hecho_accidente", "hecho_despacho", "dim_severidad", "dim_geografia")
TABLAS_SIN_FINAL = ("hecho_evidencia",)


def consultas():
    return [(n, cargar(n, departamento=DEPARTAMENTO)) for n in listar(DEPARTAMENTO)]


def sin_comentarios(sql: str) -> str:
    return "\n".join(l for l in sql.splitlines() if not l.strip().startswith("--"))


def identificadores(sql: str) -> set[str]:
    cuerpo = re.sub(r"'[^']*'", " ", sin_comentarios(sql))
    return set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", cuerpo))


def _apariciones(cuerpo: str, tabla: str) -> list[bool]:
    return [
        re.match(r"\s*(?:AS\s+\w+\s+|\w+\s+)?FINAL\b", m.group(1)) is not None
        for m in re.finditer(rf"\b(?:FROM|JOIN)\s+{tabla}\b(.*)", cuerpo)
    ]


def fuerza_version_final(cuerpo: str, tabla: str) -> bool:
    apariciones = _apariciones(cuerpo, tabla)
    return all(apariciones) if apariciones else True


def pide_version_final_alguna_vez(cuerpo: str, tabla: str) -> bool:
    return any(_apariciones(cuerpo, tabla))


class TestElCargadorAnidado:
    """T004 — el cargador existente resuelve `estrategicos/oe6`."""

    def test_listar_encuentra_las_doce_consultas(self):
        nombres = listar(DEPARTAMENTO)
        assert len(nombres) == 12, (
            f"el catálogo de OE6 tiene {len(nombres)} ficheros, no 12: {nombres}"
        )

    def test_cargar_devuelve_el_fichero(self):
        sql = cargar("e6_01_tiempo_respuesta_global", departamento=DEPARTAMENTO)
        assert "FROM hecho_accidente FINAL" in sql

    def test_nombre_inexistente_falla_nombrando_la_ruta_buscada(self):
        with pytest.raises(ConsultaNoEncontrada) as exc:
            cargar("informe_que_no_existe", departamento=DEPARTAMENTO)

        mensaje = str(exc.value)
        assert "informe_que_no_existe.sql" in mensaje
        assert "estrategicos" in mensaje.replace("\\", "/")
        assert "oe6" in mensaje


class TestLaReglaDeVersionFinal:
    """T018 — FINAL obligatorio en acumulados; prohibido en evidencia."""

    def test_toda_consulta_sobre_hecho_o_dimension_acumulada_fuerza_final(self):
        for nombre, sql in consultas():
            cuerpo = sin_comentarios(sql)
            for tabla in TABLAS_CON_FINAL:
                if re.search(rf"\b{tabla}\b", cuerpo):
                    assert fuerza_version_final(cuerpo, tabla), (
                        f"'{nombre}' toca {tabla} sin forzar la versión final: "
                        f"devolverá cifras infladas tras una recarga, y solo a veces"
                    )

    def test_ninguna_consulta_pide_final_sobre_hecho_evidencia(self):
        for nombre, sql in consultas():
            cuerpo = sin_comentarios(sql)
            for tabla in TABLAS_SIN_FINAL:
                assert not pide_version_final_alguna_vez(cuerpo, tabla), (
                    f"'{nombre}' pide FINAL sobre {tabla}, que es de transacción: "
                    f"falla con ILLEGAL_FINAL"
                )


class TestProhibicionDelEjeDeRegion:
    """T019 — unir por estado duplica cada caso sin fallar (research D1)."""

    def test_ninguna_consulta_nombra_dim_region_ni_una_columna_de_region(self):
        for nombre, sql in consultas():
            for identificador in identificadores(sql):
                bajo = identificador.lower()
                assert bajo != "dim_region", (
                    f"'{nombre}' nombra dim_region: unir por estado duplica cada "
                    f"caso (4 252 → 8 504) y cada región muestra el total completo"
                )
                assert "region" not in bajo, (
                    f"'{nombre}' nombra '{identificador}', que contiene 'region'. "
                    f"El eje no es construible; se agrupa por condado"
                )


class TestLaFormaDeLasConsultas:
    """T020 — SELECT *, ORDER BY, filtro por fecha."""

    def test_ninguna_consulta_usa_select_estrella(self):
        for nombre, sql in consultas():
            cuerpo = sin_comentarios(sql).upper()
            assert "SELECT *" not in cuerpo, (
                f"'{nombre}' usa SELECT *: una columna nueva aparecería sola "
                f"en el informe sin que nadie lo decidiera"
            )

    def test_toda_consulta_lleva_order_by_explicito(self):
        for nombre, sql in consultas():
            cuerpo = sin_comentarios(sql).upper()
            assert re.search(r"^ORDER BY", cuerpo, re.MULTILINE), (
                f"'{nombre}' no ordena: el orden de las filas sería arbitrario"
            )

    def test_toda_consulta_filtra_por_fecha(self):
        for nombre, sql in consultas():
            cuerpo = sin_comentarios(sql)
            assert "{desde:Date}" in cuerpo, f"'{nombre}' no acepta 'desde'"
            assert "{hasta:Date}" in cuerpo, f"'{nombre}' no acepta 'hasta'"
            assert re.search(r"\bfecha\b", cuerpo), (
                f"'{nombre}' no filtra por fecha: no descarta particiones (Regla 7)"
            )


class TestLaExclusionDeDatoSensible:
    """T021 — exclusión constitucional, también para la autoridad."""

    PROHIBIDAS = (
        "latitud", "longitud", "latitudinicio", "longitudinicio",
        "idusuario", "nombres", "apellidos", "gmail", "identificacion",
        "descripcion", "observaciones", "motivo_suspension", "motivo_rechazo", "nota",
        "client_secret", "ultimos_digitos",
    )
    PERMITIDOS = {
        "notas", "num_notas", "con_notas", "con_nota", "con_foto", "con_ambas",
        "solo_nota", "foto_y_nota", "categoria_nota",
    }

    def test_ninguna_consulta_nombra_una_columna_sensible(self):
        for nombre, sql in consultas():
            for identificador in identificadores(sql):
                bajo = identificador.lower()
                if bajo in self.PERMITIDOS:
                    continue
                for prohibida in self.PROHIBIDAS:
                    assert prohibida not in bajo, (
                        f"'{nombre}' nombra '{identificador}', que contiene "
                        f"'{prohibida}'"
                    )


# ── OE3 ──────────────────────────────────────────────────────────────────────

OE3 = "estrategicos/oe3"

TABLAS_CON_FINAL_OE3 = (
    "hecho_accidente", "hecho_despacho", "dim_unidad",
    "dim_geografia", "dim_condado_vecino",
)
TABLAS_SIN_FINAL_OE3 = ("hecho_estado_unidad", "hecho_ping_unidad")


def consultas_oe3():
    return [(n, cargar(n, departamento=OE3)) for n in listar(OE3)]


class TestElCargadorAnidadoOe3:
    """T004 — el cargador resuelve `estrategicos/oe3`."""

    def test_listar_encuentra_las_siete_consultas(self):
        nombres = listar(OE3)
        assert len(nombres) == 7, (
            f"el catálogo de OE3 tiene {len(nombres)} ficheros, no 7: {nombres}"
        )

    def test_cargar_devuelve_el_fichero(self):
        sql = cargar("e3_02_latencia_asignacion", departamento=OE3)
        assert "FROM hecho_accidente FINAL" in sql

    def test_nombre_inexistente_falla_nombrando_la_ruta_buscada(self):
        with pytest.raises(ConsultaNoEncontrada) as exc:
            cargar("informe_que_no_existe", departamento=OE3)
        mensaje = str(exc.value)
        assert "informe_que_no_existe.sql" in mensaje
        assert "oe3" in mensaje.replace("\\", "/")


class TestLaReglaDeVersionFinalOe3:
    """T018 — FINAL obligatorio en acumulados; prohibido en transacción."""

    def test_toda_consulta_sobre_hecho_o_dimension_acumulada_fuerza_final(self):
        for nombre, sql in consultas_oe3():
            cuerpo = sin_comentarios(sql)
            for tabla in TABLAS_CON_FINAL_OE3:
                if re.search(rf"\b{tabla}\b", cuerpo):
                    assert fuerza_version_final(cuerpo, tabla), (
                        f"'{nombre}' toca {tabla} sin forzar la versión final"
                    )

    def test_ninguna_consulta_pide_final_sobre_hechos_de_transaccion(self):
        for nombre, sql in consultas_oe3():
            cuerpo = sin_comentarios(sql)
            for tabla in TABLAS_SIN_FINAL_OE3:
                assert not pide_version_final_alguna_vez(cuerpo, tabla), (
                    f"'{nombre}' pide FINAL sobre {tabla}: falla con ILLEGAL_FINAL"
                )


class TestProhibicionDelEjeDeRegionOe3:
    """T019 — unir por estado duplica cada caso sin fallar (#38)."""

    def test_ninguna_consulta_nombra_dim_region_ni_una_columna_de_region(self):
        for nombre, sql in consultas_oe3():
            for identificador in identificadores(sql):
                bajo = identificador.lower()
                assert bajo != "dim_region", (
                    f"'{nombre}' nombra dim_region"
                )
                assert "region" not in bajo, (
                    f"'{nombre}' nombra '{identificador}', que contiene 'region'"
                )


class TestLaFormaDeLasConsultasOe3:
    """T020 — SELECT *, ORDER BY, filtro por fecha."""

    def test_ninguna_consulta_usa_select_estrella(self):
        for nombre, sql in consultas_oe3():
            cuerpo = sin_comentarios(sql).upper()
            assert "SELECT *" not in cuerpo, f"'{nombre}' usa SELECT *"

    def test_toda_consulta_lleva_order_by_explicito(self):
        for nombre, sql in consultas_oe3():
            cuerpo = sin_comentarios(sql).upper()
            assert re.search(r"^ORDER BY", cuerpo, re.MULTILINE), (
                f"'{nombre}' no ordena"
            )

    def test_toda_consulta_filtra_por_fecha(self):
        for nombre, sql in consultas_oe3():
            cuerpo = sin_comentarios(sql)
            assert "{desde:Date}" in cuerpo, f"'{nombre}' no acepta 'desde'"
            assert "{hasta:Date}" in cuerpo, f"'{nombre}' no acepta 'hasta'"
            assert re.search(r"\bfecha\b", cuerpo), (
                f"'{nombre}' no filtra por fecha (Regla 7)"
            )


class TestLaExclusionDeDatoSensibleOe3:
    """T020 — exclusión constitucional."""

    PROHIBIDAS = TestLaExclusionDeDatoSensible.PROHIBIDAS
    PERMITIDOS = TestLaExclusionDeDatoSensible.PERMITIDOS

    def test_ninguna_consulta_nombra_una_columna_sensible(self):
        for nombre, sql in consultas_oe3():
            for identificador in identificadores(sql):
                bajo = identificador.lower()
                if bajo in self.PERMITIDOS:
                    continue
                for prohibida in self.PROHIBIDAS:
                    assert prohibida not in bajo, (
                        f"'{nombre}' nombra '{identificador}'"
                    )
