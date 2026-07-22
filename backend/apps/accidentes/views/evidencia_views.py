"""DRF views for evidencia endpoints."""

from __future__ import annotations

import json

from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accidentes.permissions import (
    IsTecnicoCampoOrUnidad,
    IsTecnicoCampoOrUnidadOrAdmin,
)
from apps.accidentes.services.consulta_evidencia_service import ConsultaEvidenciaService
from apps.accidentes.services.evidencia_foto_service import EvidenciaFotoService
from apps.accidentes.services.nota_campo_service import NotaCampoService
from apps.accidentes.services.sincronizar_evidencia_service import (
    SincronizarEvidenciaService,
)
from core.api.response_envelope import error_response, success_response
from core.auth.permissions import IsAuthenticated401
from core.storage.blob_storage_service import BlobTooLargeError


class EvidenciaListView(APIView):
    permission_classes = [IsAuthenticated401, IsTecnicoCampoOrUnidadOrAdmin]

    def get(self, request: Request, idaccidente: str) -> Response:
        limit = min(int(request.query_params.get("limit", 20)), 100)
        cursor = request.query_params.get("cursor")
        tipo = request.query_params.get("tipo")
        items, next_cursor = ConsultaEvidenciaService().listar(
            idaccidente,
            tipo=tipo,
            limit=limit,
            cursor=cursor,
        )
        return success_response(
            {"items": items},
            meta={"pagination": {"next_cursor": next_cursor, "limit": limit}},
        )


class SubirEvidenciaFotoView(APIView):
    permission_classes = [IsAuthenticated401, IsTecnicoCampoOrUnidad]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request: Request, idaccidente: str) -> Response:
        archivo = request.FILES.get("archivo")
        if not archivo:
            return error_response("bad_request", "archivo requerido", "400", status_code=400)

        fechahora = request.data.get("fechahora")
        fechahora_int = int(fechahora) if fechahora else None

        try:
            data = EvidenciaFotoService().subir(
                idaccidente=idaccidente,
                idusuario=request.user.idusuario,
                archivo=archivo.read(),
                content_type=archivo.content_type or "image/jpeg",
                fechahora=fechahora_int,
            )
        except LookupError:
            return error_response("not_found", "Accidente no encontrado", "404", status_code=404)
        except BlobTooLargeError:
            return error_response(
                "payload_too_large",
                "Archivo excede 10 MB",
                "413",
                status_code=413,
            )
        except ValueError as exc:
            return error_response("unprocessable_entity", str(exc), "422", status_code=422)

        return success_response(data, status_code=status.HTTP_201_CREATED)


class RegistrarNotaCampoView(APIView):
    permission_classes = [IsAuthenticated401, IsTecnicoCampoOrUnidad]
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def post(self, request: Request, idaccidente: str) -> Response:
        nota = request.data.get("nota")
        tipo = request.data.get("tipo")
        if not nota or not tipo:
            return error_response(
                "bad_request", "nota y tipo son requeridos", "400", status_code=400
            )

        fechahora = request.data.get("fechahora")
        fechahora_int = int(fechahora) if fechahora else None

        try:
            data = NotaCampoService().registrar(
                idaccidente=idaccidente,
                idusuario=request.user.idusuario,
                nota=str(nota),
                tipo=str(tipo),
                fechahora=fechahora_int,
            )
        except LookupError:
            return error_response("not_found", "Accidente no encontrado", "404", status_code=404)
        except ValueError as exc:
            return error_response("unprocessable_entity", str(exc), "422", status_code=422)

        return success_response(data, status_code=status.HTTP_201_CREATED)


class SincronizarEvidenciaView(APIView):
    permission_classes = [IsAuthenticated401, IsTecnicoCampoOrUnidad]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request: Request, idaccidente: str) -> Response:
        notas_json = request.data.get("notas")
        fotos_metadata_json = request.data.get("fotos_metadata")
        fotos_files = request.FILES.getlist("fotos")

        archivos: list[tuple[bytes, str]] = []
        for f in fotos_files:
            archivos.append((f.read(), f.content_type or "image/jpeg"))

        try:
            data = SincronizarEvidenciaService().sincronizar(
                idaccidente=idaccidente,
                idusuario=request.user.idusuario,
                notas_json=notas_json,
                fotos_metadata_json=fotos_metadata_json,
                fotos_archivos=archivos,
            )
        except json.JSONDecodeError:
            return error_response("bad_request", "JSON inválido en notas o fotos_metadata", "400", status_code=400)
        except LookupError:
            return error_response("not_found", "Accidente no encontrado", "404", status_code=404)

        return success_response(data)
