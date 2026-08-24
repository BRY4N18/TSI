"""PG-RES-002, PG-RES-003 y PG-RES-004 — qué hace el sistema cuando algo cae.

Tres reglas con un hilo común: **una dependencia caída debe producir un error
explícito, nunca un dato incompleto presentado como completo**. Un informe al que
le falta media fuente y no lo dice es peor que un informe que no carga.

La sonda de salud tiene un modo de fallo propio y silencioso: si devuelve `200`
sin comprobar nada, convierte una caída en un silencio. El orquestador ve el
servicio sano, no lo reinicia, no alerta, y las peticiones siguen llegando a un
proceso que no puede atenderlas. Sin sonda, al menos el primer error de un
usuario delata el problema.
"""

from __future__ import annotations

import inspect
from pathlib import Path
from unittest.mock import patch

import pytest
from django.conf import settings
from rest_framework.test import APIClient

from core.seguridad.salud import (
    ACCESORIAS,
    ESENCIALES,
    Comprobacion,
    como_respuesta,
    esta_sano,
)

pytestmark = [pytest.mark.unit, pytest.mark.seguridad]

RUTA_SALUD = "/api/v1/salud"


# --- PG-RES-004: la sonda comprueba de verdad --------------------------------


def test_la_sonda_responde_sin_credencial():
    """La consulta el orquestador antes de que exista sesión alguna."""
    respuesta = APIClient().get(RUTA_SALUD)
    assert respuesta.status_code in (200, 503), respuesta.status_code


def test_la_sonda_ejerce_cada_dependencia_y_no_solo_dice_ok():
    """El aserto que distingue una sonda útil de una decorativa.

    Se comprueba que **consulta**: si Pinot falla, la sonda tiene que enterarse.
    Una que devolviera `{"estado": "ok"}` sin tocar nada pasaría cualquier prueba
    de forma y ninguna de fondo.
    """
    from core.pinot.client import PinotClient

    with patch.object(PinotClient, "query", side_effect=ConnectionError("caído")):
        respuesta = APIClient().get(RUTA_SALUD)

    assert respuesta.status_code == 503, (
        "Con Pinot caído la sonda devolvió "
        f"{respuesta.status_code}: no está comprobando la dependencia, solo que "
        "el proceso vive."
    )
    assert respuesta.json()["dependencias"]["pinot"]["ok"] is False


def test_una_dependencia_accesoria_no_tumba_el_servicio():
    """ClickHouse caído degrada los informes; no impide despachar una unidad.

    Marcar el servicio entero como indisponible por eso provocaría un reinicio
    que no arregla nada y que sí interrumpe la cadena crítica.
    """
    from core.clickhouse.client import ClickHouseClient

    with patch.object(ClickHouseClient, "query", side_effect=ConnectionError("caído")):
        respuesta = APIClient().get(RUTA_SALUD)

    assert respuesta.status_code == 200, (
        "ClickHouse es accesoria: su caída no debe marcar el servicio como "
        "indisponible."
    )
    assert respuesta.json()["dependencias"]["clickhouse"]["ok"] is False


def test_la_sonda_no_revela_detalles_internos():
    """Suele quedar expuesta al orquestador y a veces a la red.

    Un traceback aquí filtraría rutas, nombres de tabla y cadenas de conexión
    (PG-SEC-007).
    """
    from core.pinot.client import PinotClient

    with patch.object(
        PinotClient, "query", side_effect=ConnectionError("http://pinot-broker:8099/query/sql")
    ):
        cuerpo = APIClient().get(RUTA_SALUD).content.decode("utf-8", errors="replace")

    for delator in ("Traceback", "pinot-broker", "8099", "SELECT", "password"):
        assert delator not in cuerpo, f"La sonda revela «{delator}»: {cuerpo[:200]}"


def test_esencial_y_accesorio_no_se_solapan():
    assert not set(ESENCIALES) & set(ACCESORIAS)
    assert ESENCIALES, "Sin dependencias esenciales, la sonda nunca fallaría."


def test_el_estado_refleja_solo_lo_esencial():
    """Lógica pura, sin red: el criterio de «sano» es lo que aquí se prueba."""
    todo_ok = [Comprobacion(n, True) for n in ESENCIALES + ACCESORIAS]
    accesoria_mal = [
        Comprobacion(n, n not in ACCESORIAS) for n in ESENCIALES + ACCESORIAS
    ]
    esencial_mal = [
        Comprobacion(n, n not in ESENCIALES) for n in ESENCIALES + ACCESORIAS
    ]

    assert esta_sano(todo_ok)
    assert esta_sano(accesoria_mal), "Una accesoria caída no debe tumbar el servicio."
    assert not esta_sano(esencial_mal)
    assert como_respuesta(esencial_mal)["estado"] == "degradado"


# --- PG-RES-002: degradación ante caída --------------------------------------


@pytest.mark.parametrize(
    "modulo,clase",
    [
        ("core.pinot.client", "PinotClient"),
        ("core.clickhouse.client", "ClickHouseClient"),
    ],
)
def test_todo_cliente_externo_declara_un_timeout(modulo, clase):
    """Sin timeout, una dependencia lenta **cuelga el hilo indefinidamente**.

    Es peor que un fallo: el servicio no responde, la sonda tampoco, y el
    orquestador no puede distinguirlo de un proceso ocupado. Un error explícito
    se maneja; un cuelgue no.
    """
    fuente = inspect.getsource(__import__(modulo, fromlist=[clase]))
    assert "timeout=" in fuente, f"{modulo}.{clase} no declara timeout."


def test_osrm_declara_un_timeout_mas_corto_que_el_resto():
    """OSRM está en la cadena crítica: el ruteo no puede esperar diez segundos.

    Un despacho que tarda diez segundos en calcular ruta ya llegó tarde. Vale
    más una ruta aproximada a tiempo que la óptima cuando ya no sirve.
    """
    fuente = (Path(settings.BASE_DIR) / "core" / "osrm" / "client.py").read_text(encoding="utf-8")
    import re

    timeouts = [int(t) for t in re.findall(r"timeout=(\d+)", fuente)]
    assert timeouts, "OSRM no declara timeout."
    assert max(timeouts) <= 5, (
        f"OSRM espera hasta {max(timeouts)}s. Está en la cadena crítica: un "
        "despacho que tarda tanto en calcular ruta ya llegó tarde."
    )


# --- PG-RES-003: arranque en orden -------------------------------------------


def test_el_compose_declara_el_orden_de_arranque():
    """`infrastructure.md` §2 fija zookeeper → kafka → pinot-*.

    Sin `depends_on`, Pinot arranca antes que Kafka, no encuentra el bróker y
    **se queda sin consumir en silencio** — el fallo exacto que persigue
    `PG-OPE-001`, provocado por el orden de arranque.
    """
    import yaml

    ruta = Path(settings.BASE_DIR).parent / "docker" / "docker-compose.infraestructura.yml"
    # Se parsea el YAML en vez de trocear texto: la primera version cortaba el
    # bloque en la siguiente linea indentada y daba por ausente un `depends_on`
    # que si estaba. Un falso positivo aqui manda a "arreglar" un compose
    # correcto.
    servicios = yaml.safe_load(ruta.read_text(encoding="utf-8")).get("services", {})

    for servicio in ("kafka", "pinot-controller", "pinot-broker", "pinot-server"):
        assert servicio in servicios, f"{servicio} no está declarado"
        assert servicios[servicio].get("depends_on"), (
            f"{servicio} no declara `depends_on`: puede arrancar antes que su "
            "dependencia y quedarse sin consumir sin dar error."
        )


def test_los_servicios_declaran_healthcheck():
    """`depends_on` sin `condition: service_healthy` solo espera al arranque.

    Un contenedor «iniciado» no es un contenedor «listo»: Kafka tarda segundos
    en aceptar conexiones después de que Docker lo dé por arrancado.
    """
    compose = (
        Path(settings.BASE_DIR).parent / "docker" / "docker-compose.infraestructura.yml"
    ).read_text(encoding="utf-8")

    assert "healthcheck" in compose, "Ningún servicio declara healthcheck."
    assert "service_healthy" in compose, (
        "Hay `depends_on` sin `condition: service_healthy`: se espera al arranque "
        "del contenedor, no a que la dependencia acepte conexiones."
    )
