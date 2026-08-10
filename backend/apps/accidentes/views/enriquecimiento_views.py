"""DRF views for CU-O75/CU-O76 enriquecimiento estructurado."""

from __future__ import annotations

from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accidentes.permissions import (
    IsTecnicoCampoOrUnidad,
    IsTecnicoCampoOrUnidadOrAdmin,
)
from apps.accidentes.services.consulta_enriquecimiento_service import (
    ConsultaEnriquecimientoService,
)
from apps.accidentes.services.enriquecimiento_clima_service import (
    EnriquecimientoClimaService,
)
from apps.accidentes.services.enriquecimiento_conductor_service import (
    EnriquecimientoConductorService,
)
from apps.accidentes.services.enriquecimiento_elemento_fisico_service import (
    EnriquecimientoElementoFisicoService,
)
from apps.accidentes.services.enriquecimiento_implicado_service import (
    EnriquecimientoImplicadoService,
)
from core.api.response_envelope import error_response, success_response
from core.auth.permissions import IsAuthenticated401
from core.repositories.evidencia.catalogo_enriquecimiento_repository import (
    CatalogoEnriquecimientoRepository,
)


def _handle_domain(exc: Exception) -> Response | None:
    if isinstance(exc, LookupError):
        return error_response("not_found", str(exc), "404", status_code=404)
    if isinstance(exc, ValueError):
        return error_response("unprocessable_entity", str(exc), "422", status_code=422)
    return None


class EnriquecimientoAccidenteView(APIView):
    permission_classes = [IsAuthenticated401, IsTecnicoCampoOrUnidadOrAdmin]

    def get(self, request: Request, idaccidente: str) -> Response:
        try:
            data = ConsultaEnriquecimientoService().obtener(
                idaccidente, idusuario=request.user.idusuario
            )
        except Exception as exc:
            err = _handle_domain(exc)
            if err:
                return err
            raise
        return success_response(data)


class EnriquecimientoClimaView(APIView):
    permission_classes = [IsAuthenticated401, IsTecnicoCampoOrUnidad]
    parser_classes = [JSONParser]

    def put(self, request: Request, idaccidente: str) -> Response:
        idperiododia = request.data.get("idperiododia")
        idestadoclima = request.data.get("idestadoclima")
        try:
            data = EnriquecimientoClimaService().upsert(
                idaccidente=idaccidente,
                idusuario=request.user.idusuario,
                idperiododia=int(idperiododia) if idperiododia is not None else None,
                idestadoclima=int(idestadoclima) if idestadoclima is not None else None,
            )
        except Exception as exc:
            err = _handle_domain(exc)
            if err:
                return err
            raise
        return success_response(data)


class EnriquecimientoElementosFisicosView(APIView):
    permission_classes = [IsAuthenticated401, IsTecnicoCampoOrUnidadOrAdmin]
    parser_classes = [JSONParser]

    def get(self, request: Request, idaccidente: str) -> Response:
        try:
            items = EnriquecimientoElementoFisicoService().listar(idaccidente)
        except Exception as exc:
            err = _handle_domain(exc)
            if err:
                return err
            raise
        return success_response({"items": items})

    def post(self, request: Request, idaccidente: str) -> Response:
        if not IsTecnicoCampoOrUnidad().has_permission(request, self):
            return error_response("forbidden", "Sin permiso de escritura", "403", status_code=403)
        idelementofisico = request.data.get("idelementofisico")
        if idelementofisico is None:
            return error_response(
                "bad_request", "idelementofisico requerido", "400", status_code=400
            )
        try:
            data = EnriquecimientoElementoFisicoService().agregar(
                idaccidente=idaccidente,
                idelementofisico=int(idelementofisico),
                idusuario=request.user.idusuario,
            )
        except Exception as exc:
            err = _handle_domain(exc)
            if err:
                return err
            raise
        return success_response(data, status_code=status.HTTP_201_CREATED)


class EnriquecimientoElementoFisicoDetailView(APIView):
    permission_classes = [IsAuthenticated401, IsTecnicoCampoOrUnidad]
    parser_classes = [JSONParser]

    def patch(
        self, request: Request, idaccidente: str, idelementosfisicosaccidente: int
    ) -> Response:
        if request.data.get("activo") is not False:
            return error_response(
                "bad_request", "activo debe ser false", "400", status_code=400
            )
        try:
            data = EnriquecimientoElementoFisicoService().desactivar(
                idaccidente=idaccidente,
                idelementosfisicosaccidente=idelementosfisicosaccidente,
                idusuario=request.user.idusuario,
            )
        except Exception as exc:
            err = _handle_domain(exc)
            if err:
                return err
            raise
        return success_response(data)


class EnriquecimientoConductoresView(APIView):
    permission_classes = [IsAuthenticated401, IsTecnicoCampoOrUnidadOrAdmin]
    parser_classes = [JSONParser]

    def get(self, request: Request, idaccidente: str) -> Response:
        try:
            items = EnriquecimientoConductorService().listar(
                idaccidente, idusuario=request.user.idusuario
            )
        except Exception as exc:
            err = _handle_domain(exc)
            if err:
                return err
            raise
        return success_response({"items": items})

    def post(self, request: Request, idaccidente: str) -> Response:
        if not IsTecnicoCampoOrUnidad().has_permission(request, self):
            return error_response("forbidden", "Sin permiso de escritura", "403", status_code=403)
        conductor = request.data.get("conductor")
        vehiculo = request.data.get("vehiculo")
        idestadoconductor = request.data.get("idestadoconductor")
        if not isinstance(conductor, dict) or not isinstance(vehiculo, dict):
            return error_response(
                "bad_request",
                "conductor y vehiculo son requeridos",
                "400",
                status_code=400,
            )
        if idestadoconductor is None:
            return error_response(
                "bad_request", "idestadoconductor requerido", "400", status_code=400
            )
        try:
            data = EnriquecimientoConductorService().registrar(
                idaccidente=idaccidente,
                idusuario=request.user.idusuario,
                conductor=conductor,
                idestadoconductor=int(idestadoconductor),
                vehiculo=vehiculo,
            )
        except Exception as exc:
            err = _handle_domain(exc)
            if err:
                return err
            raise
        return success_response(data, status_code=status.HTTP_201_CREATED)


class EnriquecimientoConductorDetailView(APIView):
    permission_classes = [IsAuthenticated401, IsTecnicoCampoOrUnidad]
    parser_classes = [JSONParser]

    def patch(
        self, request: Request, idaccidente: str, idconductoraccidente: int
    ) -> Response:
        if request.data.get("activo") is not False:
            return error_response(
                "bad_request", "activo debe ser false", "400", status_code=400
            )
        try:
            data = EnriquecimientoConductorService().desactivar(
                idaccidente=idaccidente,
                idconductoraccidente=idconductoraccidente,
                idusuario=request.user.idusuario,
            )
        except Exception as exc:
            err = _handle_domain(exc)
            if err:
                return err
            raise
        return success_response(data)


class EnriquecimientoImplicadosView(APIView):
    permission_classes = [IsAuthenticated401, IsTecnicoCampoOrUnidadOrAdmin]
    parser_classes = [JSONParser]

    def get(self, request: Request, idaccidente: str) -> Response:
        try:
            items = EnriquecimientoImplicadoService().listar(
                idaccidente, idusuario=request.user.idusuario
            )
        except Exception as exc:
            err = _handle_domain(exc)
            if err:
                return err
            raise
        return success_response({"items": items})

    def post(self, request: Request, idaccidente: str) -> Response:
        if not IsTecnicoCampoOrUnidad().has_permission(request, self):
            return error_response("forbidden", "Sin permiso de escritura", "403", status_code=403)
        required = ("tipoimplicado", "estadoimplicado")
        missing = [f for f in required if not request.data.get(f)]
        if missing:
            return error_response(
                "bad_request",
                f"Campos requeridos: {', '.join(missing)}",
                "400",
                status_code=400,
            )
        try:
            data = EnriquecimientoImplicadoService().registrar(
                idaccidente=idaccidente,
                idusuario=request.user.idusuario,
                tipoimplicado=str(request.data["tipoimplicado"]),
                estadoimplicado=str(request.data["estadoimplicado"]),
                genero=request.data.get("genero"),
                edad=request.data.get("edad"),
            )
        except Exception as exc:
            err = _handle_domain(exc)
            if err:
                return err
            raise
        return success_response(data, status_code=status.HTTP_201_CREATED)


class EnriquecimientoImplicadoDetailView(APIView):
    permission_classes = [IsAuthenticated401, IsTecnicoCampoOrUnidad]
    parser_classes = [JSONParser]

    def patch(self, request: Request, idaccidente: str, idimplicado: int) -> Response:
        if request.data.get("activo") is not False:
            return error_response(
                "bad_request", "activo debe ser false", "400", status_code=400
            )
        try:
            data = EnriquecimientoImplicadoService().desactivar(
                idaccidente=idaccidente,
                idimplicado=idimplicado,
                idusuario=request.user.idusuario,
            )
        except Exception as exc:
            err = _handle_domain(exc)
            if err:
                return err
            raise
        return success_response(data)


class CatalogoPeriodosDiasView(APIView):
    permission_classes = [IsAuthenticated401, IsTecnicoCampoOrUnidadOrAdmin]

    def get(self, request: Request) -> Response:
        items = CatalogoEnriquecimientoRepository().list_periodos_dias()
        return success_response({"items": items})


class CatalogoEstadosClimasView(APIView):
    permission_classes = [IsAuthenticated401, IsTecnicoCampoOrUnidadOrAdmin]

    def get(self, request: Request) -> Response:
        items = CatalogoEnriquecimientoRepository().list_estados_climas()
        return success_response({"items": items})


class CatalogoElementosFisicosView(APIView):
    permission_classes = [IsAuthenticated401, IsTecnicoCampoOrUnidadOrAdmin]

    def get(self, request: Request) -> Response:
        items = CatalogoEnriquecimientoRepository().list_elementos_fisicos()
        return success_response({"items": items})


class CatalogoEstadosConductorView(APIView):
    permission_classes = [IsAuthenticated401, IsTecnicoCampoOrUnidadOrAdmin]

    def get(self, request: Request) -> Response:
        items = CatalogoEnriquecimientoRepository().list_estados_conductor()
        return success_response({"items": items})
