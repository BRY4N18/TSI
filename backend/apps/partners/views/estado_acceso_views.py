"""Consulta del estado de acceso (CU-O55, RF-PAC-009).

Dos lecturas, dos preguntas distintas
--------------------------------------
* `GET /partners/{id}/estado-acceso` — «¿por que se me corto el acceso?». La
  hace el partner sobre lo suyo, o un gestor sobre cualquiera.
* `GET /partners/cola-acceso` — «¿a quien le toca?». Solo Administrador.

El suspendido SI puede consultar
---------------------------------
Es lectura, no cambia nada, y es justo donde entiende por que se le corto y que
debe pagar (RN-PAC-016). Bloquearlo convertiria la suspension en un callejon sin
salida: el partner no sabria ni cuanto debe.

Nada de esto esta persistido
-----------------------------
«En mora» no es una columna y no debe crearse: seria una segunda verdad frente a
`Dim_Partner.activo` (RN-PAC-012). Se deriva en cada consulta de las facturas
vencidas y de los avisos ya registrados en la bitacora.
"""

from __future__ import annotations

from typing import Any

from rest_framework import status
from rest_framework.views import APIView

from apps.partners.domain_constants import (
    CAMBIO_AVISO_PREVIO_SUSPENSION,
    SIN_SUSPENSION,
)
from apps.partners.permissions import (
    EsAdministrador,
    EsPartnerOGestor,
    PartnerInexistenteError,
    PropiedadPartnerError,
    resolver_partner_visible,
    verificar_propiedad,
)
from apps.partners.services.evaluacion_mora_service import EvaluacionMoraService
from core.api.response_envelope import error_response, success_response
from core.repositories.partners.credencial_repository import CredencialRepository
from core.repositories.partners.historial_acceso_repository import (
    HistorialAccesoRepository,
)
from core.repositories.partners.partner_repository import PartnerRepository


def _avisos_enviados(historial: list[dict[str, Any]]) -> list[str]:
    """Las etiquetas (`T-10`, `T-5`) ya notificadas, de la mas antigua a la mas nueva."""
    etiquetas = [
        str(ev.get("motivo", ""))
        for ev in reversed(historial)
        if ev.get("tipo_cambio") == CAMBIO_AVISO_PREVIO_SUSPENSION
    ]
    vistas: list[str] = []
    for etiqueta in etiquetas:
        if etiqueta and etiqueta not in vistas:
            vistas.append(etiqueta)
    return vistas


class EstadoAccesoView(APIView):
    """GET /api/v1/partners/{idpartner}/estado-acceso"""

    permission_classes = [EsPartnerOGestor]

    def get(self, request, idpartner: int):
        partner = PartnerRepository().find_by_id(int(idpartner))
        try:
            # Un id inexistente y uno ajeno son indistinguibles salvo para un
            # gestor: separarlos deja un oraculo de enumeracion (PG-SEC-001).
            partner = resolver_partner_visible(request, partner)
        except PartnerInexistenteError as exc:
            return error_response(
                "not_found", str(exc), "not_found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        except PropiedadPartnerError as exc:
            return error_response(
                "forbidden", str(exc), "propiedad_partner",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        historial = HistorialAccesoRepository().list_by_partner(int(idpartner), limit=100)
        mora = EvaluacionMoraService().estado_de_mora(partner)

        return success_response({
            "idpartner": int(idpartner),
            "activo": bool(partner.get("activo", False)),
            # Centinelas, no NULL: el frontend distingue "" de "sin dato".
            "fecha_suspension": partner.get("fecha_suspension", SIN_SUSPENSION),
            "motivo_suspension": partner.get("motivo_suspension", SIN_SUSPENSION),
            "en_mora": bool(mora["en_mora"]),
            "dias_mora": int(mora["dias_mora"]),
            "avisos_enviados": _avisos_enviados(historial),
            "credenciales": [
                {
                    "idcredencial": int(c["idcredencial"]),
                    "nombre_credencial": c.get("nombre_credencial"),
                    "entorno": c.get("entorno"),
                    "activo": bool(c.get("activo", False)),
                    "fecha_creacion": c.get("fecha_creacion"),
                }
                for c in CredencialRepository().list_by_partner(int(idpartner))
            ],
            "historial": historial,
        })


class ColaAccesoView(APIView):
    """GET /api/v1/partners/cola-acceso — la cola de trabajo del Administrador.

    Sin esta lectura, el Administrador tendria que consultar partner por partner
    para saber a quien reactivar; y la reactivacion solo puede hacerla el
    (RN-PAC-009), asi que no tendria por donde empezar.
    """

    permission_classes = [EsAdministrador]

    def get(self, request):
        filtro = str(request.query_params.get("estado") or "").strip().lower()
        mora_service = EvaluacionMoraService()
        historial_repo = HistorialAccesoRepository()

        items: list[dict[str, Any]] = []
        suspendidos = 0
        en_mora = 0

        cursor = None
        while True:
            pagina, cursor = PartnerRepository().list(limit=200, cursor=cursor)
            for partner in pagina:
                idpartner = int(partner["idpartner"])
                activo = bool(partner.get("activo", False))
                estado_mora = (
                    mora_service.estado_de_mora(partner)
                    if activo
                    else {"en_mora": False, "dias_mora": 0}
                )
                avisos = _avisos_enviados(
                    historial_repo.list_by_partner(idpartner, limit=100)
                )

                # Entra en la cola si esta suspendido, o si esta en mora Y ya se
                # le aviso: un moroso sin aviso aun no requiere decision humana.
                es_suspendido = not activo
                es_avisado = bool(estado_mora["en_mora"]) and bool(avisos)
                if not (es_suspendido or es_avisado):
                    continue
                if filtro == "suspendidos" and not es_suspendido:
                    continue
                if filtro == "en_mora" and not es_avisado:
                    continue

                suspendidos += 1 if es_suspendido else 0
                en_mora += 1 if es_avisado else 0
                items.append({
                    "idpartner": idpartner,
                    "nombrepartner": partner.get("nombrepartner", ""),
                    "activo": activo,
                    "motivo_suspension": partner.get("motivo_suspension", SIN_SUSPENSION),
                    "fecha_suspension": partner.get("fecha_suspension", SIN_SUSPENSION),
                    "dias_mora": int(estado_mora["dias_mora"]),
                    "ultimo_aviso": avisos[-1] if avisos else "",
                })
            if not cursor:
                break

        # Los de mas dias de mora primero: es el orden en que urge decidir.
        items.sort(key=lambda i: (not i["activo"], i["dias_mora"]), reverse=True)
        return success_response(
            items, meta={"suspendidos": suspendidos, "en_mora": en_mora}
        )
