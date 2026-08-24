"""Endpoint de salud (PG-RES-004)."""

from __future__ import annotations

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.seguridad.salud import como_respuesta, comprobar_todo, esta_sano


class SaludView(APIView):
    """`GET /api/v1/salud` — comprueba las dependencias, no solo que el proceso viva.

    **Sin autenticación a propósito.** La sonda la consulta el orquestador antes
    de que exista sesión alguna; exigir credencial la haría inservible para su
    único consumidor. A cambio, la respuesta no revela más que el nombre de la
    dependencia y el tipo de excepción — nunca rutas, tablas ni cadenas de
    conexión (PG-SEC-007).

    Devuelve **503** si falla una dependencia esencial, para que el orquestador
    lo trate como indisponible. Un 200 con `estado: degradado` seria peor que
    nada: el orquestador no reacciona y nadie se entera.
    """

    authentication_classes: list = []
    permission_classes = [AllowAny]

    def get(self, request) -> Response:
        comprobaciones = comprobar_todo()
        sano = esta_sano(comprobaciones)
        return Response(
            como_respuesta(comprobaciones),
            status=status.HTTP_200_OK if sano else status.HTTP_503_SERVICE_UNAVAILABLE,
        )
