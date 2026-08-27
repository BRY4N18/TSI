"""RF-EVI-009 — conductores y vehículos involucrados."""

from __future__ import annotations

from typing import Any

from core.audit.evidencia_service import AuditEvidenciaService
from core.validacion import campos
from core.repositories.evidencia.accidente_read_repository import AccidenteReadRepository
from core.repositories.evidencia.catalogo_enriquecimiento_repository import (
    CatalogoEnriquecimientoRepository,
)
from core.repositories.evidencia.conductor_accidente_repository import (
    ConductorAccidenteRepository,
)
from core.repositories.evidencia.conductor_repository import ConductorRepository
from core.repositories.evidencia.vehiculo_repository import VehiculoRepository


class EnriquecimientoConductorService:
    def __init__(
        self,
        accidente_repo: AccidenteReadRepository | None = None,
        conductor_repo: ConductorRepository | None = None,
        vehiculo_repo: VehiculoRepository | None = None,
        vinculo_repo: ConductorAccidenteRepository | None = None,
        catalogo_repo: CatalogoEnriquecimientoRepository | None = None,
        audit: AuditEvidenciaService | None = None,
    ):
        self.accidente_repo = accidente_repo or AccidenteReadRepository()
        self.conductor_repo = conductor_repo or ConductorRepository()
        self.vehiculo_repo = vehiculo_repo or VehiculoRepository()
        self.vinculo_repo = vinculo_repo or ConductorAccidenteRepository()
        self.catalogo_repo = catalogo_repo or CatalogoEnriquecimientoRepository()
        self.audit = audit or AuditEvidenciaService()

    def _conductor_payload(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "identificacion": row.get("identificacion"),
            "nombres": row.get("nombres"),
            "apellidos": row.get("apellidos"),
            "genero": row.get("genero"),
            "tipolicencia": row.get("tipolicencia"),
            "estadolicencia": row.get("estadolicencia"),
            "ciudadresidencia": row.get("ciudadresidencia"),
            "aniosexperiencia": row.get("aniosexperiencia"),
        }

    def _vehiculo_payload(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "idvehiculo": row.get("idvehiculo"),
            "tipovehiculo": row.get("tipovehiculo"),
            "modelovehiculo": row.get("modelovehiculo"),
            "categoriausovehiculo": row.get("categoriausovehiculo"),
            "mercanciapeligrosa": row.get("mercanciapeligrosa"),
            "ejes": row.get("ejes"),
        }

    def _enrich_vinculo(self, vinculo: dict[str, Any]) -> dict[str, Any]:
        conductor = self.conductor_repo.find_by_id(int(vinculo["idconductor"])) or {}
        vehiculo = self.vehiculo_repo.find_by_id(int(vinculo["idvehiculo"])) or {}
        return {
            **vinculo,
            "conductor": self._conductor_payload(conductor),
            "vehiculo": self._vehiculo_payload(vehiculo),
        }

    def listar(self, idaccidente: str, *, idusuario: int | None = None) -> list[dict[str, Any]]:
        if not self.accidente_repo.find_by_id(idaccidente):
            raise LookupError("Accidente no encontrado")
        items = [
            self._enrich_vinculo(r)
            for r in self.vinculo_repo.list_activos_by_accidente(idaccidente)
        ]
        if idusuario is not None:
            self.audit.log_consultar_conductores_accidente(
                user_id=idusuario, idaccidente=idaccidente, count=len(items)
            )
        return items

    def registrar(
        self,
        *,
        idaccidente: str,
        idusuario: int,
        conductor: dict[str, Any],
        idestadoconductor: int,
        vehiculo: dict[str, Any],
    ) -> dict[str, Any]:
        if not self.accidente_repo.find_by_id(idaccidente):
            raise LookupError("Accidente no encontrado")
        if not self.accidente_repo.is_caso_activo(idaccidente):
            raise ValueError("El caso no está activo para enriquecer")
        if not self.catalogo_repo.find_estado_conductor(idestadoconductor):
            raise ValueError("idestadoconductor inválido")

        # RN-VAL-CAMPOS — formato, no solo presencia.
        #
        # Antes bastaba con que los tres campos no estuvieran vacíos: la cédula
        # aceptaba letras y símbolos, y los nombres cualquier cosa. Como el
        # conductor se reutiliza por identificación (RN-EVI-019), una cédula mal
        # capturada no ensucia un registro: parte la identidad en dos.
        conductor_valido = self._validar_conductor(conductor)
        identificacion = conductor_valido["identificacion"]

        if not vehiculo.get("tipovehiculo"):
            raise ValueError("vehiculo.tipovehiculo es requerido")
        try:
            campos.entero(vehiculo.get("ejes"), "vehiculo.ejes", minimo=1, maximo=20)
        except campos.CampoInvalido as exc:
            raise ValueError(str(exc)) from exc

        # RN-EVI-022 — tope = Fact_Accidente.numvehiculos
        accidente = self.accidente_repo.find_by_id(idaccidente)
        assert accidente is not None
        numvehiculos = accidente.get("numvehiculos")
        try:
            tope = int(numvehiculos) if numvehiculos is not None else 0
        except (TypeError, ValueError):
            tope = 0
        if tope < 1:
            raise ValueError(
                "El caso no tiene numvehiculos definido; actualice el accidente antes de registrar"
            )
        activos = self.vinculo_repo.list_activos_by_accidente(idaccidente)
        if len(activos) >= tope:
            raise ValueError(
                f"No se pueden registrar más de {tope} conductor(es)/vehículo(s) "
                f"(numvehiculos del caso)"
            )

        # RN-EVI-019 — reutilizar por identificación
        existing = self.conductor_repo.find_by_identificacion(identificacion)
        if existing:
            conductor_row = existing
        else:
            conductor_row = self.conductor_repo.create(conductor_valido)

        idvehiculo = vehiculo.get("idvehiculo")
        if idvehiculo:
            vehiculo_row = self.vehiculo_repo.find_by_id(int(idvehiculo))
            if not vehiculo_row:
                raise ValueError("idvehiculo inválido")
        else:
            vehiculo_row = self.vehiculo_repo.create(
                {
                    "tipovehiculo": vehiculo["tipovehiculo"],
                    "modelovehiculo": vehiculo.get("modelovehiculo"),
                    "categoriausovehiculo": vehiculo.get("categoriausovehiculo"),
                    "mercanciapeligrosa": vehiculo.get("mercanciapeligrosa"),
                    "ejes": vehiculo.get("ejes"),
                }
            )

        vinculo = self.vinculo_repo.create(
            idaccidente=idaccidente,
            idconductor=int(conductor_row["idconductor"]),
            idestadoconductor=idestadoconductor,
            idvehiculo=int(vehiculo_row["idvehiculo"]),
            idusuario=idusuario,
        )
        self.audit.log_registrar_conductor_accidente(
            user_id=idusuario,
            idaccidente=idaccidente,
            idconductoraccidente=vinculo["idconductoraccidente"],
        )
        return self._enrich_vinculo(vinculo)

    #: Catálogos cerrados que hasta ahora viajaban como texto libre. Se validan
    #: aquí para que el modelo analítico no acabe con "M", "Masc." y "masculino"
    #: como tres géneros distintos.
    GENEROS = frozenset({"Masculino", "Femenino", "Otro", "No informa"})
    ESTADOS_LICENCIA = frozenset({"Vigente", "Caducada", "Suspendida", "Sin licencia"})

    def _validar_conductor(self, conductor: dict[str, Any]) -> dict[str, Any]:
        """Normaliza y valida el conductor. Levanta ValueError con el campo culpable."""
        try:
            return {
                "identificacion": campos.cedula(
                    conductor.get("identificacion"), "conductor.identificacion"
                ),
                "nombres": campos.nombre(conductor.get("nombres"), "conductor.nombres"),
                "apellidos": campos.nombre(conductor.get("apellidos"), "conductor.apellidos"),
                "genero": campos.de_catalogo(
                    conductor.get("genero"), "conductor.genero", self.GENEROS, requerido=False
                ),
                "tipolicencia": conductor.get("tipolicencia") or None,
                "estadolicencia": campos.de_catalogo(
                    conductor.get("estadolicencia"),
                    "conductor.estadolicencia",
                    self.ESTADOS_LICENCIA,
                    requerido=False,
                ),
                "ciudadresidencia": campos.nombre(
                    conductor.get("ciudadresidencia"),
                    "conductor.ciudadresidencia",
                    requerido=False,
                ),
                "aniosexperiencia": campos.entero(
                    conductor.get("aniosexperiencia"),
                    "conductor.aniosexperiencia",
                    minimo=0,
                    maximo=80,
                ),
            }
        except campos.CampoInvalido as exc:
            raise ValueError(str(exc)) from exc

    def desactivar(
        self, *, idaccidente: str, idconductoraccidente: int, idusuario: int
    ) -> dict[str, Any]:
        current = self.vinculo_repo.find_by_id(idconductoraccidente)
        if not current or current.get("idaccidente") != idaccidente:
            raise LookupError("Vínculo conductor no encontrado")
        if not self.accidente_repo.is_caso_activo(idaccidente):
            raise ValueError("El caso no está activo para enriquecer")
        record = self.vinculo_repo.soft_delete(
            idconductoraccidente=idconductoraccidente, idusuario=idusuario
        )
        assert record is not None
        self.audit.log_desactivar_conductor_accidente(
            user_id=idusuario,
            idaccidente=idaccidente,
            idconductoraccidente=idconductoraccidente,
        )
        return self._enrich_vinculo(record)
