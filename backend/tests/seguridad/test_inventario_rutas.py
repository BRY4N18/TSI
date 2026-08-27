"""El inventario de rutas es la base de las suites de aislamiento y de roles.

Si el inventario miente, todo lo que se apoya en él miente con confianza: una
suite que recorre 30 rutas creyendo recorrer 234 reporta «todo cubierto» y deja
200 endpoints sin probar. Por eso el inventario se prueba a sí mismo antes de que
nadie lo use.
"""

from __future__ import annotations

import pytest

from core.seguridad.inventario_rutas import (
    PREFIJO_API,
    inventariar,
    rutas_con_identificador,
)

pytestmark = [pytest.mark.unit, pytest.mark.seguridad]

#: Medidas el 2026-08-23 ejecutando el resolver contra el sistema real.
#:
#: No son un umbral de calidad: son un detector de cambios. Si dejan de cuadrar
#: es que se añadieron o retiraron endpoints, y toca revisar si los nuevos tienen
#: cobertura de aislamiento — **no** relajar el número para que la prueba pase.
#: 235 desde el 2026-08-23: se anadio `GET /api/v1/salud` (PG-RES-004). Esta
#: prueba lo detecto sola, que es exactamente para lo que existe.
#:
#: 236 desde el 2026-08-26: se anadio
#: `GET /api/v1/unidades-emergencia/<id>/historial-despachos` (RN-DES-012,
#: hallazgo #13 de la revision del 24/08/2026). Lleva identificador, asi que
#: sube tambien el segundo contador. Cobertura de aislamiento verificada: la
#: suite `test_aislamiento_tenant` se parametriza sobre `rutas_con_identificador()`
#: y la recorre con los tres actores, en GET, en escritura y en la comprobacion
#: de indistinguibilidad.
RUTAS_API_REFERENCIA = 236
RUTAS_CON_ID_REFERENCIA = 93


def test_el_inventario_no_esta_vacio():
    """Un recorrido roto devuelve cero rutas y todas las suites pasarían vacías."""
    assert len(inventariar()) > 0


def test_el_numero_de_rutas_coincide_con_la_referencia():
    total = len(inventariar())
    assert total == RUTAS_API_REFERENCIA, (
        f"El inventario ve {total} rutas y la referencia son {RUTAS_API_REFERENCIA}. "
        "Si se añadieron endpoints, comprobar que tienen cobertura de aislamiento "
        "y actualizar la referencia; si desaparecieron, comprobar que fue a propósito."
    )


def test_el_numero_de_rutas_con_identificador_coincide():
    total = len(rutas_con_identificador())
    assert total == RUTAS_CON_ID_REFERENCIA, (
        f"Hay {total} rutas con identificador y la referencia son "
        f"{RUTAS_CON_ID_REFERENCIA}. Cada ruta nueva con id es superficie de IDOR "
        "(PG-SEC-001): comprobar que la suite de aislamiento la cubre."
    )


def test_todas_las_rutas_pertenecen_a_la_api_versionada():
    for ruta in inventariar():
        assert ruta.patron.startswith(PREFIJO_API), ruta


def test_el_recorrido_atraviesa_los_include_anidados():
    """`config/urls.py` monta once módulos con `include()`.

    Un recorrido plano vería once entradas y ninguna ruta real. Que aparezcan
    rutas de módulos distintos demuestra que la recursión funciona.
    """
    modulos = {r.patron.split("/")[2] for r in inventariar() if r.patron.count("/") > 2}
    assert len(modulos) >= 5, f"Solo se alcanzaron los módulos {modulos}"


def test_las_rutas_con_identificador_declaran_sus_parametros():
    for ruta in rutas_con_identificador():
        assert ruta.parametros_id, ruta
        for nombre in ruta.parametros_id:
            assert "id" in nombre.lower(), (ruta, nombre)


def test_las_rutas_exponen_los_metodos_que_implementan():
    """Sin esto la suite de aislamiento no sabría qué verbos probar."""
    con_metodos = [r for r in inventariar() if r.metodos]
    assert len(con_metodos) > len(inventariar()) // 2, (
        "Menos de la mitad de las vistas declaran métodos: probablemente la "
        "detección no funciona con este estilo de vista."
    )


def test_el_inventario_expone_las_clases_de_permiso():
    """US2 cruza roles contra estas clases; sin ellas la matriz es inútil."""
    con_permisos = [r for r in inventariar() if r.permission_classes]
    assert con_permisos, "Ninguna ruta expone permission_classes"
