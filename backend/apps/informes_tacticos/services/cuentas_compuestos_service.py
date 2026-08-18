"""Servicio de los informes compuestos de Cuentas y Clientes.

El Administrador cubre los nueve. El Director Tecnológico, **solo OT18**.
"""

from __future__ import annotations

from typing import Any

from apps.informes_tacticos.periodo import Periodo
from core.repositories.informes_tacticos.modelo_repository import ModeloRepository

DEPARTAMENTO = "cuentas"

MATERIA_CICLO = "ciclo"
MATERIA_INCORPORACION = "incorporacion"
MATERIA_ACCESO = "acceso"

NOTA_COBERTURA = (
    "Solo el 9,5 % de los usuarios tiene organización declarada; "
    "la ocupación real puede ser mayor."
)
NOTA_CATALOGO = (
    "Etapas tomadas del catálogo declarado; incluye las que ningún cliente ha completado."
)
NOTA_SOLAPE = (
    "Una sesión que cruza la medianoche cuenta en ambas franjas; "
    "la suma de franjas supera el total de sesiones."
)


class InformeDesconocido(KeyError):
    """El informe pedido no está en el registro publicado."""


CATALOGO: dict[str, str] = {
    "churn-por-cohorte": "ot17_churn_por_cohorte",
    "antiguedad-media": "ot17_antiguedad_media",
    "usuarios-vs-tope": "ot17_usuarios_vs_tope",
    "cuentas-en-riesgo": "ot17_cuentas_en_riesgo",
    "tiempo-onboarding": "ot04_tiempo_onboarding",
    "embudo-abandono": "ot04_embudo_abandono",
    "tasa-aprobacion": "ot04_tasa_aprobacion",
    "concurrencia-sesiones": "ot18_concurrencia_sesiones",
    "roles-incompatibles": "ot18_roles_incompatibles",
}

MATERIAS: dict[str, str] = {
    "churn-por-cohorte": MATERIA_CICLO,
    "antiguedad-media": MATERIA_CICLO,
    "usuarios-vs-tope": MATERIA_CICLO,
    "cuentas-en-riesgo": MATERIA_CICLO,
    "tiempo-onboarding": MATERIA_INCORPORACION,
    "embudo-abandono": MATERIA_INCORPORACION,
    "tasa-aprobacion": MATERIA_INCORPORACION,
    "concurrencia-sesiones": MATERIA_ACCESO,
    "roles-incompatibles": MATERIA_ACCESO,
}

INFORMES_COBERTURA = frozenset({"usuarios-vs-tope", "cuentas-en-riesgo"})
INFORMES_CATALOGO = frozenset({"embudo-abandono"})
INFORMES_SOLAPE = frozenset({"concurrencia-sesiones"})

PUBLICADOS: frozenset[str] = frozenset(CATALOGO)


class CuentasCompuestosService:
    def __init__(self, repositorio: ModeloRepository | None = None):
        self._repositorio = repositorio or ModeloRepository()

    def informes_publicados(self) -> list[str]:
        return sorted(PUBLICADOS)

    def materia_de(self, informe: str) -> str | None:
        return MATERIAS.get(informe)

    def calcular(
        self,
        informe: str,
        periodo: Periodo,
        *,
        extra: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], dict[str, str]]:
        try:
            consulta = CATALOGO[informe]
        except KeyError as exc:
            raise InformeDesconocido(informe) from exc

        extra = dict(extra or {})
        parametros: dict[str, Any] = {
            "desde": periodo.desde,
            "hasta": periodo.hasta,
            "mes_cohorte": extra.get("mes_cohorte") or "",
            "dias_inactividad": extra.get("dias_inactividad", 90),
            "pares": extra.get("pares_incompatibles") or "",
        }
        filas = self._repositorio.ejecutar(
            consulta, departamento=DEPARTAMENTO, parametros=parametros
        )
        notas: dict[str, str] = {}
        if informe in INFORMES_COBERTURA:
            notas["nota_cobertura"] = NOTA_COBERTURA
        if informe in INFORMES_CATALOGO:
            notas["nota_catalogo"] = NOTA_CATALOGO
        if informe in INFORMES_SOLAPE and any(f.get("cruza_medianoche") for f in filas):
            notas["nota_solape"] = NOTA_SOLAPE
        resultados = [_limpiar(informe, fila) for fila in filas]
        cuerpo = {
            "periodo": {"desde": periodo.desde, "hasta": periodo.hasta},
            "resultados": resultados,
        }
        return cuerpo, notas


def _limpiar(informe: str, fila: dict[str, Any]) -> dict[str, Any]:
    out = dict(fila)
    if informe == "concurrencia-sesiones":
        out.pop("cruza_medianoche", None)
    return out
