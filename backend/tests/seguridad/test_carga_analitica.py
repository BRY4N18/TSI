"""PG-ANA-003 y PG-ANA-006 — cómo carga el modelo analítico y qué guarda cada base.

**PG-ANA-003.** Una carga a medias es peor que una que no ocurre: una partición
parcialmente cargada es indistinguible de un mes de poca actividad. Nadie
sospecha de un informe con pocos casos si el mes fue tranquilo.

**PG-ANA-006.** El Postgres que acompaña a Airflow es **metastore del
orquestador**, no un almacén de negocio. Si alguna tabla dimensional acabara ahí,
habría una tercera copia de la verdad que ningún cuadre vigila — y las tres
divergirían sin que nada lo detectara.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from django.conf import settings

pytestmark = [pytest.mark.unit, pytest.mark.seguridad]

RAIZ = Path(settings.BASE_DIR).parent
CARGA = RAIZ / "dags" / "lib" / "carga_particion.py"


# --- PG-ANA-003: la carga no deja datos a medias -----------------------------


def test_la_carga_reemplaza_la_particion_entera_y_no_filas_sueltas():
    """`DROP PARTITION` + `INSERT`, nunca `DELETE WHERE`.

    Un borrado por condición deja fuera las filas que la condición no alcanza:
    si el criterio cambia entre cargas, sobreviven filas de la versión anterior
    mezcladas con las nuevas. El resultado es una partición coherente en
    apariencia y falsa en contenido.
    """
    fuente = CARGA.read_text(encoding="utf-8")

    assert "DROP PARTITION" in fuente, (
        "La carga ya no descarta la partición: sin eso, recargar duplica en vez "
        "de reemplazar."
    )
    # Se mira el SQL **que se ejecuta**, no el texto del fichero: el docstring
    # menciona `DELETE WHERE` justamente para explicar por qué no se usa, y
    # buscarlo en crudo marcaba como defecto la explicación de la decisión.
    import re

    ejecutado = re.findall(r'ejecutar\(\s*f?[\'"]([^\'"]+)', fuente)
    assert not [sql for sql in ejecutado if "DELETE" in sql.upper()], (
        f"Se ejecuta un borrado por condición: {ejecutado}. Deja fuera lo que la "
        "condición no alcanza."
    )


def test_un_periodo_que_se_queda_vacio_tambien_se_descarta():
    """El caso que se olvida y corrompe en silencio.

    Si un período que antes tenía filas pasa a no tener ninguna, sin nombrarlo
    explícitamente **nadie descartaría su partición** y las filas viejas
    sobrevivirían a una recarga que debía dejarlo vacío. El informe seguiría
    mostrando datos de una versión anterior de la verdad.
    """
    fuente = CARGA.read_text(encoding="utf-8")
    assert "particiones_vacias" in fuente, (
        "No hay forma de declarar un período que se quedó sin filas."
    )


def test_el_orden_es_descartar_y_luego_insertar():
    """Insertar antes de descartar duplicaría la partición entera."""
    fuente = CARGA.read_text(encoding="utf-8")
    assert fuente.index("DROP PARTITION") < fuente.index("insertar(tabla"), (
        "Se inserta antes de descartar: la partición quedaría duplicada."
    )


def test_la_atomicidad_de_la_carga_esta_documentada_con_su_limite():
    """⚠️ **La carga NO es atómica, y conviene que esté escrito.**

    `DROP PARTITION` seguido de `INSERT` son dos operaciones: si la inserción
    falla, la partición queda **vacía**, no a medias. ClickHouse no ofrece
    transacción entre ambas.

    Vacía es mejor que parcial —un cuadre lo detecta como «faltan N», y
    `PG-ANA-001` lo ve— pero sigue siendo una ventana en la que el informe
    muestra cero para un período que tenía datos.

    Esta prueba no exige atomicidad, que el motor no da: exige que **el límite
    esté documentado donde vive el código**, para que nadie lo descubra en
    producción creyendo que había garantía.
    """
    fuente = CARGA.read_text(encoding="utf-8").lower()
    assert any(
        marca in fuente for marca in ("no es atómic", "no es atomic", "atomicidad")
    ), (
        "carga_particion.py no documenta que DROP+INSERT no es atómico. Quien lo "
        "lea supondrá una garantía que el motor no da."
    )


# --- PG-ANA-006: cada base guarda lo suyo ------------------------------------


def test_el_postgres_de_airflow_no_aparece_en_la_configuracion_de_django():
    """Django no debe tener forma de escribir en el metastore del orquestador.

    Si la tuviera, la tentación de guardar «una tablita» ahí existiría, y esa
    tabla no la vigila ningún cuadre: sería una tercera copia de la verdad
    divergiendo en silencio.
    """
    ajustes = (Path(settings.BASE_DIR) / "config" / "settings.py").read_text(encoding="utf-8")

    for delator in ("airflow-postgres", "tactico-airflow-postgres", "AIRFLOW_DB"):
        assert delator not in ajustes, (
            f"settings.py referencia «{delator}»: Django no debe alcanzar el "
            "metastore de Airflow (PG-ANA-006)."
        )


def test_el_ddl_analitico_no_crea_tablas_en_postgres():
    """Todo el modelo analítico vive en ClickHouse.

    Una tabla dimensional creada en el metastore quedaría fuera del cuadre de
    `PG-ANA-001`, que solo compara Pinot con ClickHouse.
    """
    ddl = (RAIZ / "dags" / "lib" / "ddl.py").read_text(encoding="utf-8")

    for delator in ("postgres", "psycopg", "SERIAL PRIMARY KEY"):
        assert delator.lower() not in ddl.lower(), (
            f"ddl.py menciona «{delator}»: el modelo analítico debe crearse solo "
            "en ClickHouse."
        )


def test_el_compose_no_publica_el_puerto_del_metastore():
    """Un metastore accesible desde fuera invita a usarlo como base de negocio.

    No es una amenaza de seguridad grave —está en la red interna— sino una
    barrera barata contra el atajo que crearía la tercera copia.
    """
    import yaml

    ruta = RAIZ / "docker" / "docker-compose.tactico.yml"
    servicios = yaml.safe_load(ruta.read_text(encoding="utf-8")).get("services", {})

    metastore = servicios.get("tactico-airflow-postgres")
    assert metastore is not None, "El metastore no está declarado."
    assert not metastore.get("ports"), (
        "El Postgres de Airflow publica puertos al host. Es el metastore del "
        "orquestador; exponerlo invita a usarlo como base de negocio "
        "(PG-ANA-006)."
    )
