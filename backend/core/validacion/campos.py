"""Reglas de formato de campos de captura — capa de garantía.

Espejo de `frontend/src/app/shared/validacion/campos.validacion.ts`. El frontend
evita el viaje; **esto** es lo que impide el dato malo, porque el endpoint se
puede llamar sin pasar por el formulario.

Motivación (revisión 24/08/2026, hallazgo #9): varios campos aceptaban espacios
en blanco, letras donde iban dígitos y símbolos arbitrarios. El caso citado fue
la cédula del enriquecimiento del sitio, que admitía letras.

Cada función devuelve el valor **normalizado** o levanta `CampoInvalido`, que el
llamador traduce a su propio error de dominio. Normalizar aquí evita que cada
servicio recorte espacios a su manera.
"""

from __future__ import annotations

import re
from typing import Any

#: Cédula ecuatoriana: exactamente 10 dígitos.
PATRON_CEDULA = re.compile(r"^\d{10}$")

#: Nombres/apellidos: letras con acentos, espacios, apóstrofo y guion.
PATRON_NOMBRE = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ][A-Za-zÁÉÍÓÚÜÑáéíóúüñ '\-]{1,49}$")

#: Placa: 6 a 8 alfanuméricos, con guion intermedio opcional.
PATRON_PLACA = re.compile(r"^[A-Za-z0-9]{3}-?[A-Za-z0-9]{3,4}$")

PATRON_TELEFONO = re.compile(r"^\+?\d{7,15}$")

PATRON_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class CampoInvalido(ValueError):
    """Un campo no cumple su formato. Trae el nombre del campo culpable."""

    def __init__(self, campo: str, detalle: str):
        self.campo = campo
        self.detalle = detalle
        super().__init__(f"{campo}: {detalle}")


def texto_requerido(valor: Any, campo: str, *, maximo: int = 255) -> str:
    limpio = str(valor or "").strip()
    if not limpio:
        raise CampoInvalido(campo, "es obligatorio y no puede ser solo espacios")
    if len(limpio) > maximo:
        raise CampoInvalido(campo, f"no puede superar {maximo} caracteres")
    return limpio


def cedula(valor: Any, campo: str = "identificacion", *, requerido: bool = True) -> str | None:
    limpio = str(valor or "").strip()
    if not limpio:
        if requerido:
            raise CampoInvalido(campo, "es obligatorio")
        return None
    if not PATRON_CEDULA.match(limpio):
        raise CampoInvalido(campo, "debe tener exactamente 10 dígitos, sin letras ni símbolos")
    return limpio


def nombre(valor: Any, campo: str, *, requerido: bool = True) -> str | None:
    limpio = str(valor or "").strip()
    if not limpio:
        if requerido:
            raise CampoInvalido(campo, "es obligatorio")
        return None
    if not PATRON_NOMBRE.match(limpio):
        raise CampoInvalido(
            campo, "solo admite letras, espacios, apóstrofo y guion (2 a 50 caracteres)"
        )
    return limpio


def placa(valor: Any, campo: str = "placa", *, requerido: bool = True) -> str | None:
    limpio = str(valor or "").strip().upper()
    if not limpio:
        if requerido:
            raise CampoInvalido(campo, "es obligatorio")
        return None
    if not PATRON_PLACA.match(limpio):
        raise CampoInvalido(campo, "debe tener entre 6 y 8 alfanuméricos (ej. ABC-1234)")
    return limpio


def email(valor: Any, campo: str = "gmail", *, requerido: bool = True) -> str | None:
    limpio = str(valor or "").strip().lower()
    if not limpio:
        if requerido:
            raise CampoInvalido(campo, "es obligatorio")
        return None
    if not PATRON_EMAIL.match(limpio):
        raise CampoInvalido(campo, "no tiene un formato de correo válido")
    return limpio


def telefono(valor: Any, campo: str = "telefono", *, requerido: bool = False) -> str | None:
    limpio = str(valor or "").strip()
    if not limpio:
        if requerido:
            raise CampoInvalido(campo, "es obligatorio")
        return None
    if not PATRON_TELEFONO.match(limpio):
        raise CampoInvalido(campo, "debe tener entre 7 y 15 dígitos")
    return limpio


def entero(
    valor: Any,
    campo: str,
    *,
    minimo: int = 0,
    maximo: int | None = None,
    requerido: bool = False,
) -> int | None:
    if valor in (None, ""):
        if requerido:
            raise CampoInvalido(campo, "es obligatorio")
        return None
    try:
        parsed = int(valor)
    except (TypeError, ValueError):
        raise CampoInvalido(campo, "debe ser un número entero") from None
    if parsed < minimo:
        raise CampoInvalido(campo, f"no puede ser menor que {minimo}")
    if maximo is not None and parsed > maximo:
        raise CampoInvalido(campo, f"no puede ser mayor que {maximo}")
    return parsed


def de_catalogo(
    valor: Any, campo: str, admitidos: set[str] | frozenset[str], *, requerido: bool = True
) -> str | None:
    """Valor libre que en realidad pertenece a un catálogo cerrado."""
    limpio = str(valor or "").strip()
    if not limpio:
        if requerido:
            raise CampoInvalido(campo, "es obligatorio")
        return None
    if limpio not in admitidos:
        raise CampoInvalido(campo, f"debe ser uno de: {', '.join(sorted(admitidos))}")
    return limpio
