"""RF-SUSF-003 — solicitud / aprobación cambio de plan."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from core.repositories.cuentas_clientes.cliente_repository import ClienteRepository
from core.repositories.suscripciones.plan_repository import PlanRepository
from core.repositories.suscripciones.solicitud_cambio_plan_repository import (
    SolicitudCambioPlanRepository,
)
from core.repositories.suscripciones.suscripcion_repository import SuscripcionRepository


class CambioPlanError(Exception):
    def __init__(self, code: str, detail: str, http_status: int = 400):
        self.code = code
        self.detail = detail
        self.http_status = http_status
        super().__init__(detail)


class CambioPlanService:
    def __init__(
        self,
        solicitudes: SolicitudCambioPlanRepository | None = None,
        suscripciones: SuscripcionRepository | None = None,
        plans: PlanRepository | None = None,
        clientes: ClienteRepository | None = None,
    ):
        self.solicitudes = solicitudes or SolicitudCambioPlanRepository()
        self.suscripciones = suscripciones or SuscripcionRepository()
        self.plans = plans or PlanRepository()
        self.clientes = clientes or ClienteRepository()

    ORDEN_NIVEL = {"Básico": 1, "Profesional": 2, "Empresarial": 3}

    def _es_upgrade(self, idplan_actual: int, plan_nuevo: dict[str, Any]) -> bool:
        actual = self.plans.find_by_id(idplan_actual)
        nivel_actual = (actual or {}).get("nivel", "Básico")
        nivel_nuevo = plan_nuevo.get("nivel", "Básico")
        return self.ORDEN_NIVEL.get(nivel_nuevo, 0) > self.ORDEN_NIVEL.get(nivel_actual, 0)

    def solicitar(self, *, idcliente: int, idplansolicitado: int, motivo: str = "") -> dict[str, Any]:
        sus = self.suscripciones.find_activa_by_cliente(idcliente)
        if not sus:
            raise CambioPlanError("no_suscripcion", "Sin suscripción activa")
        # SRS §3.3.1: "no se admite cambiar de plan sobre una suscripción suspendida o
        # cancelada". No basta con `find_activa_by_cliente`, que solo mira `activo`:
        # suspender deja `activo = True` y solo cambia `estado`, así que un cliente
        # suspendido por impago podía mejorarse de plan — y al ser mejora, se
        # autoaprobaba y se aplicaba en el acto.
        if sus.get("estado") != "Activa":
            raise CambioPlanError(
                "estado_invalido",
                f"No se puede cambiar de plan con la suscripción {str(sus.get('estado')).lower()}",
                409,
            )
        if self.solicitudes.find_pendiente(idcliente):
            raise CambioPlanError("conflict", "Ya hay solicitud Pendiente", 409)
        plan = self.plans.find_by_id(idplansolicitado)
        if not plan or not plan.get("activo"):
            raise CambioPlanError("plan_inactivo", "Plan destino inválido")
        if plan["idplan"] == sus["idplan"]:
            raise CambioPlanError("mismo_plan", "El plan solicitado es el actual")
        es_upgrade = self._es_upgrade(sus["idplan"], plan)
        sol = self.solicitudes.create(
            {
                "idcliente": idcliente,
                "idplanactual": sus["idplan"],
                "idplansolicitado": idplansolicitado,
                "motivo": motivo,
                "estado": "Pendiente",
            }
        )
        if es_upgrade:
            # Auto-aprobación de upgrade (OpenAPI / CU-O104).
            #
            # Se aprueba sobre el registro que acabamos de construir, NO releyéndolo
            # por id: la escritura va por Kafka y Pinot tarda 5-15 s en exponerla, así
            # que `find_by_id` no la encontraba y el upgrade moría con
            # "Solicitud no pendiente" dejando la solicitud Pendiente para siempre.
            return self._aprobar(sol, idadmin=0)
        return sol

    def aprobar(self, *, idsolicitud: int, idadmin: int) -> dict[str, Any]:
        sol = self.solicitudes.find_by_id(idsolicitud)
        if not sol or sol.get("estado") != "Pendiente":
            raise CambioPlanError("not_found", "Solicitud no pendiente", 404)
        return self._aprobar(sol, idadmin=idadmin)

    # `idplan` arranca en 1, así que 0 no puede confundirse con un plan real.
    # Las filas anteriores a la migración pueden traer el defecto de Pinot para
    # INT (`Integer.MIN_VALUE`), por eso se compara con <= 0 y no con == 0.
    SIN_CAMBIO_PROGRAMADO = 0

    @classmethod
    def plan_programado_id(cls, sus: dict[str, Any]) -> int | None:
        """Plan programado de una suscripción, o None si no hay ninguno."""
        try:
            idplan = int(sus.get("idplan_programado") or 0)
        except (TypeError, ValueError):
            return None
        return idplan if idplan > 0 else None

    def resolver_programado(
        self, sus: dict[str, Any]
    ) -> tuple[dict[str, Any], str | None]:
        """Campos que aplican un cambio programado al recorrer el ciclo.

        Devuelve `({}, None)` si no hay nada programado. El segundo elemento es el
        nombre del plan nuevo, que el llamador debe reflejar en el cliente.
        """
        idplan = self.plan_programado_id(sus)
        if idplan is None:
            return {}, None
        limpiar = {"idplan_programado": self.SIN_CAMBIO_PROGRAMADO}
        if idplan == sus.get("idplan"):
            return limpiar, None  # ya está aplicado; solo se limpia la marca
        plan = self.plans.find_by_id(idplan)
        if not plan:
            # El plan desapareció del catálogo: se descarta el cambio en vez de
            # dejar la marca colgada y reintentarla en cada renovación.
            return limpiar, None
        return {**self.campos_del_plan(plan), **limpiar}, plan.get("nombre")

    @staticmethod
    def campos_del_plan(plan: dict[str, Any]) -> dict[str, Any]:
        """Lo que una suscripción copia de su plan al aplicarlo."""
        return {
            "idplan": plan["idplan"],
            "precio": plan["precio"],
            "periodicidad": plan.get("periodicidad") or "Mensual",
            # nivel/severidades/carga_lote_habilitada se resincronizan solo en un cambio
            # de plan explícito y aprobado — nunca por una edición directa de Dim_Plan
            # (ver decisiones-pendientes.md #6).
            "nivel": plan.get("nivel"),
            "severidades_desbloqueadas": plan.get("severidades_desbloqueadas", "[]"),
            "carga_lote_habilitada": bool(plan.get("carga_lote_habilitada", False)),
        }

    def _aprobar(self, sol: dict[str, Any], *, idadmin: int) -> dict[str, Any]:
        """Resuelve la solicitud. `sol` ya viene validada como Pendiente.

        La **mejora** aplica de inmediato. La **reducción** no: se anota en
        `idplan_programado` y la aplica el job de renovación al recorrer el ciclo
        (decisión #27). Aplicarla en el acto le retiraba al cliente un nivel de
        servicio que ya había pagado hasta el fin del período, y dejaba la factura
        del ciclo al precio del plan bajo — el prorrateo que el SRS prohíbe.
        """
        plan = self.plans.find_by_id(sol["idplansolicitado"])
        if not plan:
            raise CambioPlanError("plan_inactivo", "Plan destino no existe")
        sus = self.suscripciones.find_activa_by_cliente(sol["idcliente"])
        if not sus:
            raise CambioPlanError("no_suscripcion", "Sin suscripción")
        if self._es_upgrade(sus["idplan"], plan):
            self.suscripciones.update(sus["id_suscripcion"], self.campos_del_plan(plan))
            self.clientes.update(sol["idcliente"], {"plan_suscripcion": plan["nombre"]})
        else:
            self.suscripciones.update(
                sus["id_suscripcion"], {"idplan_programado": plan["idplan"]}
            )
        return self.solicitudes.update_from(
            sol,
            {
                "estado": "Aprobada",
                "idadminaprobador": idadmin,
                "fecha_resolucion": int(datetime.now(timezone.utc).timestamp() * 1000),
            },
        )

    def rechazar(self, *, idsolicitud: int, idadmin: int, motivo_rechazo: str) -> dict[str, Any]:
        sol = self.solicitudes.find_by_id(idsolicitud)
        if not sol or sol.get("estado") != "Pendiente":
            raise CambioPlanError("not_found", "Solicitud no pendiente", 404)
        return self.solicitudes.update_from(
            sol,
            {
                "estado": "Rechazada",
                "motivo_rechazo": motivo_rechazo,
                "idadminaprobador": idadmin,
                "fecha_resolucion": int(datetime.now(timezone.utc).timestamp() * 1000),
            },
        )
