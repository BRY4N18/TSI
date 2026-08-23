"""Servicio de los informes compuestos de Soporte al Cliente.

El cumplimiento se mide contra el SLA **vigente al crearse el ticket**, y la
cobertura viaja en la misma fila que la cifra BSC. El agente se acota por su
clave; el texto de los tickets no está en el modelo.
"""

from __future__ import annotations

from typing import Any

from apps.informes_tacticos.periodo import Periodo
from core.repositories.informes_tacticos.modelo_repository import ModeloRepository

DEPARTAMENTO = "soporte"

ACOTADO_TODOS = "todos"
ACOTADO_PROPIOS = "propios"

GRANULARIDADES = frozenset({"dia", "semana", "mes"})
GRANULARIDAD_DEFECTO = "mes"
AGRUPAR_COLA = frozenset({"estado", "prioridad", "tipo", "agente"})
EJES_REINCIDENCIA = frozenset({"tipo_incidencia", "tipo"})

INFORMES_CUMPLIMIENTO = frozenset({
    "cumplimiento-sla",
    "cumplimiento-sla-por-plan",
    "evolucion-incumplimiento",
})


class InformeDesconocido(KeyError):
    """El informe pedido no está en el registro publicado."""


CATALOGO: dict[str, str] = {
    "cumplimiento-sla": "ot19_cumplimiento_sla",
    "cumplimiento-sla-por-plan": "ot19_cumplimiento_por_plan",
    "rendimiento-agentes": "ot19_rendimiento_agente",
    "tickets-por-servicio": "ot19_tickets_por_servicio",
    "tablero-cola": "ot20_tablero_cola",
    "evolucion-incumplimiento": "ot20_evolucion_incumplimiento",
    "escalado-automatico": "ot20_tasa_escalado_automatico",
    "carga-entrante-resuelta": "ot20_carga_entrante_vs_resuelta",
    "reincidencia-clientes": "ot20_reincidencia_clientes",
}

PUBLICADOS: frozenset[str] = frozenset(CATALOGO)

MENSAJES = {
    "sla_historico_aplicado": (
        "El cumplimiento se mide contra el SLA vigente cuando se creó cada "
        "ticket, no contra la configuración actual."
    ),
    "cobertura_incompleta": (
        "Hay tickets sin compromiso en el período; el porcentaje sin compromiso "
        "viaja en la misma fila que el cumplimiento."
    ),
    "servicio_no_registrado": (
        "Ningún ticket tiene servicio asignado; el agrupamiento por servicio "
        "no está disponible y se declara el recuento bajo «sin servicio»."
    ),
    "tiempos_excluidos_sin_hito": (
        "Los tiempos sin hito alcanzado se excluyen del promedio; "
        "sin_resolver indica cuántos se omitieron."
    ),
    "periodo_acotado_difiere_del_tablero": (
        "Este tablero acota por período; el tablero operativo actual devuelve "
        "toda la cola, así que las cifras diferirán a propósito."
    ),
    "sin_datos_en_periodo": "No hay tickets en el período pedido.",
    "eje_servicio_sustituido": (
        "El eje servicio no está disponible porque idservicio es nulo en los "
        "tickets; se agrupa por tipo de incidencia."
    ),
}


def _declaracion(codigo: str, **detalle: Any) -> dict[str, Any]:
    item: dict[str, Any] = {"codigo": codigo, "mensaje": MENSAJES[codigo]}
    if detalle:
        item["detalle"] = detalle
    return item


def _nido_motivos(fila: dict[str, Any]) -> dict[str, Any]:
    return {
        "pendiente_clasificar": int(fila.pop("motivo_pendiente_clasificar", 0) or 0),
        "sin_compromiso": int(fila.pop("motivo_sin_compromiso", 0) or 0),
        "sin_configuracion": int(fila.pop("motivo_sin_config", 0) or 0),
    }


class SoporteCompuestosService:
    def __init__(self, repositorio: ModeloRepository | None = None):
        self._repositorio = repositorio or ModeloRepository()

    def informes_publicados(self) -> list[str]:
        return sorted(PUBLICADOS)

    def calcular(
        self,
        informe: str,
        periodo: Periodo | None,
        *,
        idagente: int | None = None,
        extra: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], str]:
        try:
            consulta = CATALOGO[informe]
        except KeyError as exc:
            raise InformeDesconocido(informe) from exc

        extra = dict(extra or {})
        parametros: dict[str, Any] = {
            "idagente": idagente if idagente is not None else -1,
        }
        if periodo is not None:
            parametros["desde"] = periodo.desde
            parametros["hasta"] = periodo.hasta
            parametros["granularidad"] = extra.get("granularidad", periodo.granularidad)
        else:
            parametros["desde"] = "1970-01-01"
            parametros["hasta"] = "2099-12-31"
            parametros["granularidad"] = GRANULARIDAD_DEFECTO

        if informe == "tablero-cola":
            parametros["sin_periodo"] = 0 if extra.get("periodo_pedido") else 1
            parametros["agrupar_por"] = extra.get("agrupar_por", "estado")
        if informe == "reincidencia-clientes":
            parametros["eje"] = extra.get("eje", "tipo_incidencia")
            parametros["minimo"] = extra.get("minimo", 2)

        filas = self._repositorio.ejecutar(
            consulta, departamento=DEPARTAMENTO, parametros=parametros
        )
        resultados = [_normalizar_fila(informe, fila) for fila in filas]
        _poner_nombre_de_agente(resultados)
        declaraciones = _declaraciones_de(informe, resultados, extra, periodo)
        cuerpo: dict[str, Any] = {
            "periodo": _periodo_aplicado(periodo, extra),
            "resultados": resultados,
            "declaraciones": declaraciones,
        }
        if informe == "rendimiento-agentes":
            cuerpo["sin_agente"] = extra.get("sin_agente")
        alcance = ACOTADO_PROPIOS if idagente is not None else ACOTADO_TODOS
        return cuerpo, alcance


def _normalizar_fila(informe: str, fila: dict[str, Any]) -> dict[str, Any]:
    out = dict(fila)
    if informe in INFORMES_CUMPLIMIENTO:
        out["sin_compromiso_por_motivo"] = _nido_motivos(out)
        if out.get("pct_cumplimiento") is not None:
            out["pct_cumplimiento"] = _ausente_si_nan(out["pct_cumplimiento"])
        if out.get("pct_sin_compromiso") is not None:
            out["pct_sin_compromiso"] = _ausente_si_nan(out["pct_sin_compromiso"])
        if out.get("pct_incumplimiento") is not None:
            out["pct_incumplimiento"] = _ausente_si_nan(out["pct_incumplimiento"])
    if informe == "rendimiento-agentes":
        out["media_resolucion_s"] = _ausente_si_nan(out.get("media_resolucion_s"))
    if informe == "escalado-automatico":
        out["pct_escalado_automatico"] = _ausente_si_nan(out.get("pct_escalado_automatico"))
    return out


def _ausente_si_nan(valor: Any) -> Any:
    if valor is None:
        return None
    try:
        if valor != valor:  # NaN
            return None
    except (TypeError, ValueError):
        return None
    return valor


def _periodo_aplicado(periodo: Periodo | None, extra: dict[str, Any]) -> dict[str, Any]:
    if periodo is None or not extra.get("periodo_pedido", True):
        return {"desde": None, "hasta": None, "acotado": False}
    return {"desde": periodo.desde, "hasta": periodo.hasta, "acotado": True}


def _declaraciones_de(
    informe: str,
    resultados: list[dict[str, Any]],
    extra: dict[str, Any],
    periodo: Periodo | None,
) -> list[dict[str, Any]]:
    declaraciones: list[dict[str, Any]] = []
    if not resultados:
        declaraciones.append(_declaracion("sin_datos_en_periodo"))
        return declaraciones

    if informe in INFORMES_CUMPLIMIENTO:
        declaraciones.append(_declaracion("sla_historico_aplicado"))
        if any((fila.get("pct_sin_compromiso") or 0) > 0 for fila in resultados):
            declaraciones.append(_declaracion("cobertura_incompleta"))

    if informe == "tickets-por-servicio":
        solo_sin = resultados and all(
            (fila.get("servicio") or "") == "sin servicio" for fila in resultados
        )
        if solo_sin:
            declaraciones.append(_declaracion("servicio_no_registrado"))

    if informe == "rendimiento-agentes":
        if any((fila.get("sin_resolver") or 0) > 0 for fila in resultados):
            declaraciones.append(_declaracion("tiempos_excluidos_sin_hito"))

    if informe == "tablero-cola" and extra.get("periodo_pedido"):
        declaraciones.append(_declaracion("periodo_acotado_difiere_del_tablero"))

    if informe == "reincidencia-clientes":
        declaraciones.append({
            "codigo": "servicio_no_registrado",
            "mensaje": MENSAJES["eje_servicio_sustituido"],
            "detalle": {"eje_usado": extra.get("eje", "tipo_incidencia")},
        })

    return declaraciones


def _poner_nombre_de_agente(resultados: list[dict[str, Any]]) -> None:
    """Añade `agente` (nombre) junto a `id_agente`, en su sitio.

    ⚠️ **La pantalla mostraba «Agente 2» y «Agente 3».** El informe devolvía solo
    el identificador y la plantilla lo pintaba tal cual, así que el gerente veía
    números donde tiene que decidir sobre personas.

    No es una exclusión deliberada: la identidad del agente **no** está entre los
    datos que este departamento oculta —eso es el asunto, la descripción, los
    mensajes y las notas internas—, y el listado simple de tickets ya resuelve el
    nombre con este mismo repositorio. Faltaba hacerlo aquí.

    `id_agente` se conserva: quien cruce con otra fuente lo necesita, y un nombre
    no identifica una fila.
    """
    ids = [f.get("id_agente") for f in resultados if f.get("id_agente") is not None]
    if not ids:
        return

    from core.repositories.soporte.informes_tickets_repository import (
        InformesTicketsRepository,
    )

    nombres = InformesTicketsRepository().nombres_de_usuario(ids)
    for fila in resultados:
        ident = fila.get("id_agente")
        if ident is None:
            continue
        # ⚠️ Ausente, **no** «Agente 2»: un identificador que no resuelve es una
        # anomalía —el agente ya no existe, o la carga se adelantó—, y disfrazarla
        # de nombre la haría indistinguible de un agente normal.
        fila["agente"] = nombres.get(int(ident))
