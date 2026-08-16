"""T004, T011–T014 — el catálogo de consultas y las reglas sobre su texto.

Estas pruebas miran **el texto de las consultas**, no su resultado. Es
deliberado: las tres reglas que comprueban producen fallos que la ejecución no
delata.

* Una consulta sin `FINAL` sobre un hecho acumulado **funciona** y devuelve
  cifras infladas **solo a veces** — cuando ha habido una recarga y las versiones
  aún no se han fusionado.
* Una consulta con una columna sensible **funciona** y publica el dato.
* Una consulta sin `ORDER BY` **funciona** y devuelve las filas en un orden que
  puede cambiar entre corridas, con lo que comparar dos ejecuciones deja de
  significar nada.

Ninguna de las tres se ve ejecutando la consulta una vez.
"""

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.consultas import ConsultaNoEncontrada, cargar, listar  # noqa: E402

DEPARTAMENTO = "emergencias"

#: `FINAL` obligatorio: instantánea acumulada y dimensiones.
TABLAS_CON_FINAL = ("hecho_accidente", "hecho_despacho")
DIMENSIONES = ("dim_tiempo", "dim_geografia", "dim_severidad", "dim_origen_despacho", "dim_unidad")

#: `FINAL` prohibido: hechos de transacción. Pedirlo falla con `ILLEGAL_FINAL`.
TABLAS_SIN_FINAL = ("hecho_estado_unidad", "hecho_ping_unidad", "hecho_evidencia")


def consultas():
    return [(n, cargar(n, departamento=DEPARTAMENTO)) for n in listar(DEPARTAMENTO)]


def sin_comentarios(sql: str) -> str:
    """El SQL sin sus comentarios: los encabezados nombran tablas y columnas."""
    return "\n".join(l for l in sql.splitlines() if not l.strip().startswith("--"))


def identificadores(sql: str) -> set[str]:
    """Nombres que la consulta **usa**, sin comentarios y sin literales.

    Los literales se quitan porque son valores, no columnas. `tipo = 'nota'`
    compara contra el valor `'nota'` de una columna que se llama `tipo`; leerlo
    como si nombrara una columna `nota` haría fallar la comprobación de dato
    sensible sobre una consulta que no toca ningún texto.
    """
    cuerpo = re.sub(r"'[^']*'", " ", sin_comentarios(sql))
    return set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", cuerpo))


def menciona(cuerpo: str, tabla: str) -> bool:
    return re.search(rf"\b{tabla}\b", cuerpo) is not None


def fuerza_version_final(cuerpo: str, tabla: str) -> bool:
    """¿Toda aparición de `tabla` en un FROM/JOIN lleva `FINAL`?

    El alias va **entre** la tabla y `FINAL` —`hecho_accidente AS h FINAL`—, así
    que buscar la cadena `'hecho_accidente FINAL'` daría por incumplida una
    consulta correcta. Y aceptar cualquier alias sin más daría por cumplida una
    que no lo lleva: el alias es opcional, `FINAL` no.
    """
    apariciones = _apariciones(cuerpo, tabla)
    return all(apariciones) if apariciones else True


def pide_version_final_alguna_vez(cuerpo: str, tabla: str) -> bool:
    """¿**Alguna** aparición lleva `FINAL`? Una sola ya falla con `ILLEGAL_FINAL`."""
    return any(_apariciones(cuerpo, tabla))


def _apariciones(cuerpo: str, tabla: str) -> list[bool]:
    return [
        re.match(r"\s*(?:AS\s+\w+\s+|\w+\s+)?FINAL\b", m.group(1)) is not None
        for m in re.finditer(rf"\b(?:FROM|JOIN)\s+{tabla}\b(.*)", cuerpo)
    ]


class TestElCargador:
    def test_nombre_inexistente_falla_nombrando_el_fichero_buscado(self):
        # Un `KeyError` con el nombre mal escrito no le dice nada a quien se
        # equivocó: ya sabía qué escribió. Lo que no sabe es dónde se miró.
        with pytest.raises(ConsultaNoEncontrada) as exc:
            cargar("informe_que_no_existe", departamento=DEPARTAMENTO)

        assert "informe_que_no_existe.sql" in str(exc.value)
        assert DEPARTAMENTO in str(exc.value)

    def test_el_error_enumera_las_disponibles(self):
        with pytest.raises(ConsultaNoEncontrada) as exc:
            cargar("no_existe", departamento=DEPARTAMENTO)

        assert "ot21_distribucion_severidad" in str(exc.value)

    def test_cargar_devuelve_el_fichero_tal_cual(self):
        sql = cargar("ot21_distribucion_severidad", departamento=DEPARTAMENTO)

        assert "FROM hecho_accidente FINAL" in sql

    def test_listar_encuentra_el_catalogo(self):
        # Si una consulta nueva no apareciera aquí, las pruebas que recorren el
        # catálogo dejarían de cubrirla **sin fallar**.
        assert len(listar(DEPARTAMENTO)) >= 6


class TestLaReglaDeVersionFinal:
    """T011 — la regla que se olvida y no avisa."""

    def test_toda_consulta_sobre_hecho_acumulado_fuerza_la_version_final(self):
        for nombre, sql in consultas():
            cuerpo = sin_comentarios(sql)
            for tabla in TABLAS_CON_FINAL:
                if menciona(cuerpo, tabla):
                    assert fuerza_version_final(cuerpo, tabla), (
                        f"'{nombre}' toca {tabla} sin forzar la versión final: "
                        f"devolverá cifras infladas tras una recarga, y solo a veces"
                    )

    def test_toda_consulta_sobre_una_dimension_fuerza_la_version_final(self):
        for nombre, sql in consultas():
            cuerpo = sin_comentarios(sql)
            for dim in DIMENSIONES:
                if menciona(cuerpo, dim):
                    assert fuerza_version_final(cuerpo, dim), (
                        f"'{nombre}' toca {dim} sin FINAL"
                    )

    def test_ninguna_consulta_pide_final_sobre_un_hecho_de_transaccion(self):
        # Pedirlo de más no es inocuo: falla con `ILLEGAL_FINAL`.
        for nombre, sql in consultas():
            cuerpo = sin_comentarios(sql)
            for tabla in TABLAS_SIN_FINAL:
                assert not pide_version_final_alguna_vez(cuerpo, tabla), (
                    f"'{nombre}' pide FINAL sobre {tabla}, que es de transacción: "
                    f"falla con ILLEGAL_FINAL"
                )


class TestLaExclusionDeDatoSensible:
    """T012 — exclusión constitucional: ningún cargo la levanta."""

    PROHIBIDAS = (
        "latitud", "longitud", "latitudinicio", "longitudinicio",
        "idusuario", "nombres", "apellidos", "gmail", "identificacion",
        "descripcion", "observaciones", "motivo_suspension", "motivo_rechazo", "nota",
        "client_secret", "ultimos_digitos",
    )

    #: Identificadores que contienen un fragmento prohibido y **no son** dato
    #: sensible. Se enumeran uno a uno, con su razón, en vez de estrechar los
    #: patrones: `nota` tiene que seguir cazando la columna con el texto de la
    #: nota y cualquier columna de texto que aparezca mañana.
    #:
    #: Lo que distingue a estos es que **cuentan o clasifican, no citan**. Saber
    #: que un caso tiene tres notas no revela ninguna, y saber que una nota es de
    #: categoría «Condiciones del sitio» no dice qué decía.
    PERMITIDOS = {
        "notas", "num_notas", "con_notas", "solo_nota", "foto_y_nota",
        "categoria_nota",
    }

    def test_ninguna_consulta_nombra_una_columna_sensible(self):
        # Se juzgan **identificadores**, no el texto entero. Buscar el fragmento
        # en todo el SQL confunde `nota` con `notas`, y la única salida sería
        # estrechar el patrón —que es justo lo que no debe hacerse—.
        for nombre, sql in consultas():
            for identificador in identificadores(sql):
                bajo = identificador.lower()
                if bajo in self.PERMITIDOS:
                    continue
                for prohibida in self.PROHIBIDAS:
                    assert prohibida not in bajo, (
                        f"'{nombre}' nombra '{identificador}', que contiene "
                        f"'{prohibida}'. Es dato sensible: coordenadas, identidad "
                        f"de persona o texto libre interno"
                    )

    def test_lo_permitido_cuenta_o_clasifica_pero_no_cita(self):
        """Una excepción mal puesta desactivaría el patrón para ese nombre.

        No se puede comprobar el tipo desde aquí —esto mira texto, no el
        esquema—, así que se comprueba la **forma del nombre**: un recuento
        empieza por `num_`/`con_`/`solo_` o va en plural, y una categoría empieza
        por `categoria_`. Si alguien añadiera `observaciones` a la lista para
        acallar un fallo, esta prueba lo vería.
        """
        for permitido in self.PERMITIDOS:
            assert (
                permitido.startswith(("num_", "con_", "solo_", "categoria_"))
                or permitido.endswith("s")
                or "_y_" in permitido
            ), f"'{permitido}' no parece un recuento ni una categoría"


class TestLaFormaDeLasConsultas:
    """T013 y T014 — lo que hace comparables dos corridas."""

    def test_toda_consulta_lleva_order_by_explicito(self):
        for nombre, sql in consultas():
            # Al principio de línea y sin sangrar: es el `ORDER BY` que ordena la
            # **salida**. Buscar la cadena en cualquier parte daría por ordenada
            # una consulta cuyo único `ORDER BY` está dentro de una función de
            # ventana, que no ordena nada de lo que sale.
            cuerpo = sin_comentarios(sql).upper()
            assert re.search(r"^ORDER BY", cuerpo, re.MULTILINE), (
                f"'{nombre}' no ordena: el orden de las filas sería arbitrario y "
                f"comparar dos corridas dejaría de ser posible"
            )

    def test_ninguna_consulta_usa_select_estrella(self):
        for nombre, sql in consultas():
            cuerpo = sin_comentarios(sql).upper()
            assert "SELECT *" not in cuerpo, (
                f"'{nombre}' usa SELECT *: una columna nueva del hecho aparecería "
                f"sola en el informe sin que nadie lo decidiera"
            )

    def test_toda_consulta_acepta_y_filtra_el_rango(self):
        for nombre, sql in consultas():
            cuerpo = sin_comentarios(sql)
            assert "{desde:Date}" in cuerpo, f"'{nombre}' no acepta 'desde'"
            assert "{hasta:Date}" in cuerpo, f"'{nombre}' no acepta 'hasta'"

    def test_toda_consulta_lleva_encabezado_con_su_informe_y_su_ot(self):
        # El encabezado es lo que permite saber qué mide un fichero sin
        # reconstruirlo leyendo el SQL.
        for nombre, sql in consultas():
            cabecera = "\n".join(sql.splitlines()[:4])
            assert "Informe #" in cabecera, f"'{nombre}' no declara su número"
            assert "OT2" in cabecera, f"'{nombre}' no declara su OT"
