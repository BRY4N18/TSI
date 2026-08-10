"""RF-PON-011 — contrato de integracion versionado POR SERVICIO (CU-O50).

El versionado NO es global: `Dim_Servicio` contiene varios servicios y cada uno
lleva su propio ciclo. Sin la FK `id_servicio`, los tres colapsarian en una
sola linea temporal (spec.md seccion 15 D1).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from apps.partners.domain_constants import (
    ESTADOS_VERSION,
    SIN_FECHA_RETIRO,
    VERSION_RETIRADA,
    VERSION_SOPORTADA,
    VERSION_VIGENTE,
)
from core.pinot.client import PinotClient
from core.repositories.partners.version_contrato_repository import (
    VersionContratoRepository,
)


class ContratoIntegracionError(Exception):
    def __init__(self, code: str, detail: str):
        self.code = code
        self.detail = detail
        super().__init__(detail)


class ContratoIntegracionService:
    def __init__(
        self,
        versiones: VersionContratoRepository | None = None,
        pinot: PinotClient | None = None,
    ):
        self.versiones = versiones or VersionContratoRepository()
        self.pinot = pinot or PinotClient()

    @staticmethod
    def _now_ms() -> int:
        return int(datetime.now(timezone.utc).timestamp() * 1000)

    def _servicio_existe(self, id_servicio: int) -> bool:
        return bool(
            self.pinot.query(
                "SELECT id_servicio FROM Dim_Servicio WHERE id_servicio = %(id)s LIMIT 1",
                {"id": id_servicio},
            )
        )

    def consultar(self, *, id_servicio: int, version: str | None = None) -> dict[str, Any]:
        """RF-PON-011 — version pedida (o la vigente) mas el listado del servicio."""
        if not self._servicio_existe(id_servicio):
            raise ContratoIntegracionError("not_found", "El servicio no existe")

        todas = self.versiones.list_by_servicio(id_servicio)
        if not todas:
            raise ContratoIntegracionError(
                "not_found", "El servicio no tiene versiones de contrato publicadas"
            )

        if version:
            elegida = self.versiones.find_version(id_servicio, version)
            if not elegida:
                raise ContratoIntegracionError(
                    "not_found", f"La versión {version} no existe para este servicio"
                )
        else:
            elegida = self.versiones.vigente(id_servicio)
            if not elegida:
                raise ContratoIntegracionError(
                    "sin_version_vigente",
                    "El servicio no tiene una versión vigente publicada",
                )

        return {**elegida, "versiones": todas}

    def publicar(
        self,
        *,
        id_servicio: int,
        version: str,
        estado: str = VERSION_VIGENTE,
        spec_url: str | None = None,
        fecha_retiro: int | None = None,
    ) -> dict[str, Any]:
        """Alta o cambio de estado de una version.

        Invariante: como maximo UNA version `vigente` por servicio. Publicar una
        nueva vigente pasa la anterior a `soportada` en la misma operacion.
        """
        if estado not in ESTADOS_VERSION:
            raise ContratoIntegracionError("validation_error", f"estado inválido: {estado}")
        if not self._servicio_existe(id_servicio):
            raise ContratoIntegracionError("not_found", "El servicio no existe")

        # RN-PON-012 — nada pasa a `retirada` sin fecha de retiro publicada.
        if estado == VERSION_RETIRADA and not fecha_retiro:
            raise ContratoIntegracionError(
                "retiro_sin_fecha",
                "Una versión no puede retirarse sin una fecha de retiro publicada previamente",
            )

        # Clave natural (id_servicio, version): si ya existe, se actualiza.
        existente = self.versiones.find_version(id_servicio, version)

        if estado == VERSION_VIGENTE:
            vigente_actual = self.versiones.vigente(id_servicio)
            if vigente_actual and vigente_actual.get("version") != version:
                # La anterior baja a `soportada`, no se retira: los partners que
                # aun no migraron deben poder seguir consultandola (RF-O50.2).
                self.versiones.upsert({**vigente_actual, "estado": VERSION_SOPORTADA})

        return self.versiones.upsert(
            {
                **(existente or {}),
                "id_servicio": id_servicio,
                "version": version,
                "estado": estado,
                "spec_url": spec_url if spec_url is not None else (existente or {}).get("spec_url", ""),
                "fecha_retiro": (
                    fecha_retiro
                    if fecha_retiro is not None
                    else (existente or {}).get("fecha_retiro", SIN_FECHA_RETIRO)
                ),
                "activo": True,
            }
        )
