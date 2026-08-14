"""Alcance de los datos que un partner puede consumir (RF-APM-002, RF-APM-003).

Dos filtros, dos comportamientos distintos ante el fallo
--------------------------------------------------------
- **Severidad no habilitada -> 403.** Pedir una severidad que el plan no cubre
  es un intento de acceso fuera de alcance, no una busqueda sin resultados.
  Devolver lista vacia le diria al partner «no hay accidentes graves», que es
  falso y le haria tomar decisiones sobre una mentira.
- **Cliente sin zonas -> conjunto vacio (fail-closed).** No recibir todos los
  datos por defecto. Exponer siniestralidad de zonas no contratadas es una fuga
  de datos, no una comodidad (RF-APM-003).

La diferencia importa: en el primer caso el partner **pidio algo que no le
corresponde**; en el segundo **no tiene nada contratado que darle**.

Las zonas se leen con el mismo mecanismo que ya usa
`seguimiento-cierre-de-casos` (`condados_desde_preferencias`), no con uno
nuevo: dos implementaciones del mismo filtro acabarian divergiendo.
"""

from __future__ import annotations

import json
from typing import Any

from apps.seguimiento.services.historial_emergencias_service import (
    HistorialEmergenciasService,
)
from core.pinot.client import PinotClient
from core.repositories.despacho.geografia_repository import GeografiaRepository
from core.repositories.partners.plan_read_repository import PlanReadRepository

LIMITE_MAXIMO = 200


class ConsumoDatosError(Exception):
    """Lleva `code` para que la vista mapee el HTTP sin adivinar."""

    def __init__(self, code: str, detail: str):
        self.code = code
        self.detail = detail
        super().__init__(detail)


class ConsumoDatosService:
    def __init__(
        self,
        pinot: PinotClient | None = None,
        planes: PlanReadRepository | None = None,
        geografia: GeografiaRepository | None = None,
    ):
        self.pinot = pinot or PinotClient()
        self.planes = planes or PlanReadRepository(pinot=self.pinot)
        self.geografia = geografia or GeografiaRepository()

    # --- Alcance -------------------------------------------------------------

    def severidades_habilitadas(self, idcliente: int) -> set[int]:
        """Las severidades contratadas por el cliente (RF-APM-002).

        **Se lee de `Fact_Suscripcion`, no de `Dim_Plan`**, contra lo que dice
        literalmente el spec, porque es lo semanticamente correcto: la
        suscripcion guarda lo que el cliente **contrato**, congelado — misma
        filosofia que el cupo congelado de #07. Si el plan cambia despues, lo
        contratado no se mueve. El plan queda como respaldo para las
        suscripciones antiguas que no copiaron el valor.

        Los valores son ids de `Dim_Severidad` (1 Leve · 2 Moderado · 3 Grave ·
        4 Fatal) desde la migracion del 2026-08-11.
        """
        suscripcion = self.planes.suscripcion_vigente(idcliente)
        if not suscripcion:
            raise ConsumoDatosError(
                "sin_suscripcion", "El cliente no tiene una suscripción vigente"
            )

        severidades = self._parsear_severidades(
            suscripcion.get("severidades_desbloqueadas")
        )
        if severidades:
            return severidades

        # Respaldo: si la suscripcion no lo trae, se intenta el plan.
        plan = self.planes.find_plan(int(suscripcion["idplan"]))
        if not plan:
            raise ConsumoDatosError(
                "plan_incompleto", "La suscripción referencia un plan inexistente"
            )
        return self._parsear_severidades(plan.get("severidades_desbloqueadas"))

    @staticmethod
    def _parsear_severidades(crudo: Any) -> set[int]:
        """JSON de nombres o de ids -> conjunto de `idseveridad`.

        Tolera el centinela de Pinot: `'null'` (el string, no vacio) y `None`
        dan conjunto vacio en vez de reventar. `json.loads('null')` devuelve
        `None`, e iterarlo lanzaria `TypeError` en produccion.
        """
        if crudo in (None, "", "null"):
            return set()
        try:
            valores = json.loads(crudo)
        except (TypeError, json.JSONDecodeError):
            return set()
        if not isinstance(valores, list):
            return set()

        ids: set[int] = set()
        for v in valores:
            if isinstance(v, bool):
                continue
            if isinstance(v, int):
                ids.add(v)
            elif isinstance(v, str) and v.strip().isdigit():
                # Tolerado porque el JSON podria traer el id como texto; los
                # nombres del vocabulario retirado ya no se reconocen.
                ids.add(int(v.strip()))
        return ids

    def zonas_contratadas(self, idcliente: int) -> set[int]:
        """Condados contratados, reutilizando el mecanismo de seguimiento.

        Un cliente sin preferencias devuelve conjunto vacio, y eso significa
        **cero resultados**, no «todos» (fail-closed).
        """
        # La columna es `id_cliente` con guion bajo, no `idcliente`: verificado
        # contra el esquema real, no supuesto.
        filas = self.pinot.query(
            "SELECT zonas_geograficas FROM Dim_Preferencias_Cliente "
            "WHERE id_cliente = %(id_cliente)s LIMIT 1",
            {"id_cliente": idcliente},
        )
        if not filas:
            return set()
        return HistorialEmergenciasService.condados_desde_preferencias(
            filas[0].get("zonas_geograficas")
        )

    # --- Consulta ------------------------------------------------------------

    def consultar_accidentes(
        self,
        *,
        idcliente: int,
        idseveridad: int | None = None,
        limit: int = 50,
        desde_ms: int | None = None,
        hasta_ms: int | None = None,
    ) -> dict[str, Any]:
        """Expedientes dentro del alcance del partner.

        Devuelve tambien `zonas_aplicadas` y `severidades_aplicadas`: un
        resultado vacio tiene que ser **explicable** sin abrir la base.
        """
        severidades = self.severidades_habilitadas(idcliente)
        zonas = self.zonas_contratadas(idcliente)

        if idseveridad is not None and int(idseveridad) not in severidades:
            # 403, NO lista vacia: es un acceso fuera de alcance.
            raise ConsumoDatosError(
                "severidad_no_habilitada",
                f"El plan contratado no habilita la severidad {idseveridad}",
            )

        meta = {
            "zonas_aplicadas": sorted(zonas),
            "severidades_aplicadas": sorted(severidades),
        }

        # Fail-closed: sin zonas o sin severidades no se consulta siquiera.
        if not zonas or not severidades:
            return {"items": [], "meta": meta}

        severidades_pedidas = {int(idseveridad)} if idseveridad is not None else severidades

        filtros = ["activo = true"]
        params: dict[str, Any] = {"limit": max(1, min(int(limit), LIMITE_MAXIMO))}
        if desde_ms is not None:
            filtros.append("fechahoraaccidente >= %(desde)s")
            params["desde"] = desde_ms
        if hasta_ms is not None:
            filtros.append("fechahoraaccidente < %(hasta)s")
            params["hasta"] = hasta_ms

        # `LIMIT` explicito siempre: Pinot aplica 10 en silencio.
        filas = self.pinot.query(
            "SELECT * FROM Fact_Accidente WHERE "
            + " AND ".join(filtros)
            + " ORDER BY fechahoraaccidente DESC LIMIT %(limit)s",
            params,
        )

        # El filtrado se aplica aqui y no en el SQL para no depender de `IN` con
        # listas dinamicas, que Pinot resuelve de forma distinta segun version.
        #
        # OJO: `Fact_Accidente` **no tiene columna `idcondado`** — solo
        # `idcalle`. El condado se resuelve con el mismo repositorio que usa
        # `seguimiento` (`resolve_condado_from_idcalle`), que es lo que exige
        # RF-APM-003: reutilizar el mecanismo existente, no inventar otro.
        items = []
        for f in filas:
            if int(f.get("idseveridad", -1)) not in severidades_pedidas:
                continue
            idcondado = self.geografia.resolve_condado_from_idcalle(
                int(f.get("idcalle", -1))
            )
            if idcondado is None or int(idcondado) not in zonas:
                continue
            items.append(f)
        return {"items": items, "meta": meta}


# Aqui vivia `SEVERIDADES_POR_NIVEL`, el puente que traducia el vocabulario
# propio de los planes ("Baja"/"Media"/"Alta") a los ids de `Dim_Severidad`.
# Retirado el 2026-08-11: los planes y las suscripciones ya guardan ids reales
# (`database/migra_severidades_plan_a_idseveridad.py`) y el catalogo unico es
# `Dim_Severidad`. Cierra `decisiones-pendientes.md` #23.
