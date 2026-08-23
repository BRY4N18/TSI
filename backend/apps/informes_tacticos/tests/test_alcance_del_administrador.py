"""Qué ve el `Administrador` frente a la autoridad de cada departamento.

⚠️ **Esta prueba fija un hecho medido, no un deseo.**

Las clases de permiso decían que el `Administrador` entraba «con su
acotamiento». Medido el 2026-08-19 resultó falso en Emergencias, Red Operativa,
Partners, Cuentas y Suscripciones: esos endpoints **no acotan a nadie**, y el
director y el `Administrador` reciben exactamente las mismas filas.

Describir un control que no existe es peor que no describir ninguno —quien lo lee
deja de buscarlo—, así que se corrigió el texto. Esto lo sujeta: si algún día se
añade un acotamiento de verdad, esta prueba falla y obliga a actualizar la
documentación en el mismo cambio, en vez de dejarla mintiendo otra vez.
"""

from __future__ import annotations

import inspect

import pytest

from apps.informes_tacticos import permissions as perms


#: Clases cuyo docstring **no puede** volver a prometer acotamiento para el
#: `Administrador` mientras su endpoint no lo aplique.
SIN_ACOTAMIENTO_REAL = [
    perms.EmergenciasCompuestosPermission,
    perms.RedOperativaCompuestosPermission,
    perms.SuscripcionesCompuestosPermission,
]


@pytest.mark.parametrize("clase", SIN_ACOTAMIENTO_REAL, ids=lambda c: c.__name__)
def test_el_docstring_no_promete_un_acotamiento_que_no_existe(clase):
    doc = inspect.getdoc(clase) or ""

    assert "con su acotamiento" not in doc, (
        f"{clase.__name__} vuelve a prometer que el Administrador entra acotado. "
        f"Ese endpoint no acota a nadie: el director y el Administrador reciben "
        f"las mismas filas."
    )
    assert "NO entra acotado" in doc, (
        f"{clase.__name__} perdió el aviso de que aquí no hay acotamiento. Sin "
        f"él, quien lea la clase supondrá que el Administrador está limitado."
    )


def test_ventas_si_acota_al_administrador_y_lo_dice():
    """El contraste: donde el acotamiento **sí** existe, el texto lo afirma.

    En Ventas y CRM el `Administrador` entra con `acotado_a = propios`, medido.
    Que aquí la promesa se mantenga es lo que hace significativo quitarla en las
    otras tres.
    """
    doc = inspect.getdoc(perms.VentasCrmCompuestosPermission) or ""

    assert "acotado igual que el ejecutivo" in doc


def _admin():
    admin = type("U", (), {"is_authenticated": True, "roles": [perms.ROLE_ADMIN]})()
    return type("R", (), {"user": admin})()


def test_el_administrador_ya_no_entra_a_los_informes_de_gestion():
    """Decisión del 2026-08-19: el `Administrador` **opera**, no lee gestión.

    Antes abría los 84 informes compuestos mientras cada director abría entre 3 y
    17, y eso anulaba los dos repartos de autoridad que este módulo mantiene: veía
    crecimiento **y** validación, finanzas **y** catálogo.
    """
    peticion = _admin()

    for materia in ("crecimiento", "validacion"):
        vista = type("V", (), {"kwargs": {"informe": _informe_de(materia)}})()
        assert not perms.RedOperativaCompuestosPermission().has_permission(peticion, vista)

    sin_materia = type("V", (), {"kwargs": {"informe": "x"}})()
    assert not perms.EmergenciasCompuestosPermission().has_permission(peticion, sin_materia)
    assert not perms.PartnersCompuestosPermission().has_permission(peticion, sin_materia)
    assert not perms.VentasCrmCompuestosPermission().has_permission(peticion, sin_materia)
    assert not perms.SoporteCompuestosPermission().has_permission(peticion, sin_materia)


def test_el_reparto_por_materia_ahora_se_sostiene_frente_a_todos():
    """⚠️ Lo que el reparto existe para impedir, ya no lo salta nadie.

    `RedOperativaCompuestosPermission` avisa de que lo natural es «admitir a las
    dos autoridades y quedarse tranquilo». El reparto se respetaba entre
    directores y el `Administrador` lo saltaba entero.
    """
    expansion = type("U", (), {"is_authenticated": True, "roles": ["DirectorExpansion"]})()
    peticion = type("R", (), {"user": expansion})()

    propia = type("V", (), {"kwargs": {"informe": _informe_de("crecimiento")}})()
    ajena = type("V", (), {"kwargs": {"informe": _informe_de("validacion")}})()

    assert perms.RedOperativaCompuestosPermission().has_permission(peticion, propia)
    assert not perms.RedOperativaCompuestosPermission().has_permission(peticion, ajena)


def test_cuentas_ya_no_es_una_excepcion():
    """⚠️ **La excepción se cerró creando el cargo que faltaba.**

    El `Administrador` seguía entrando aquí porque Cuentas y Clientes no tenía
    autoridad táctica propia: quitárselo habría dejado siete de sus nueve
    informes sin que nadie pudiera abrirlos. El 2026-08-19 se creó el
    **Director de Cuentas**, y con él la excepción desapareció.

    El orden importaba: retirar al `Administrador` **antes** de crear el cargo
    habría dejado los informes inalcanzables.
    """
    vista = type("V", (), {"kwargs": {"informe": "churn-por-cohorte"}})()
    assert not perms.CuentasCompuestosPermission().has_permission(_admin(), vista)


def test_cuentas_reparte_su_autoridad_por_materia():
    """Cada autoridad a su materia, como Red Operativa y Suscripciones."""
    def peticion(rol):
        usuario = type("U", (), {"is_authenticated": True, "roles": [rol]})()
        return type("R", (), {"user": usuario})()

    def vista(informe):
        return type("V", (), {"kwargs": {"informe": informe}})()

    permiso = perms.CuentasCompuestosPermission()

    # El ciclo de vida y la incorporación son del Director de Cuentas...
    assert permiso.has_permission(peticion("DirectorCuentas"), vista("churn-por-cohorte"))
    assert permiso.has_permission(peticion("DirectorCuentas"), vista("tiempo-onboarding"))
    # ...y los accesos técnicos no.
    assert not permiso.has_permission(
        peticion("DirectorCuentas"), vista("concurrencia-sesiones")
    )

    # Y en el otro sentido: el Tecnológico solo gobierna los accesos.
    assert permiso.has_permission(
        peticion("DirectorTecnologico"), vista("concurrencia-sesiones")
    )
    assert not permiso.has_permission(
        peticion("DirectorTecnologico"), vista("churn-por-cohorte")
    )


def _informe_de(materia: str) -> str:
    from apps.informes_tacticos.services.red_operativa_compuestos_service import (
        MATERIAS,
    )

    return next(informe for informe, m in MATERIAS.items() if m == materia)
