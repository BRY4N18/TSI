import time

import pytest

from apps.accidentes.domain_constants import ESTADO_BORRADOR
from core.repositories.accidentes.accidente_repository import AccidenteRepository
from core.repositories.accidentes.estado_accidente_repository import EstadoAccidenteRepository


@pytest.fixture
def accidente_payload():
    now = int(time.time() * 1000)
    return {
        "latitudinicio": 19.4326,
        "longitudinicio": -99.1332,
        "fechahoraaccidente": now,
        "idseveridad": 2,
        "descripcion": "Choque leve en intersección",
        "idcalle": 1,
    }


@pytest.fixture
def seed_accidente(mock_pinot, mock_kafka):
    """Create an accident with lifecycle state in the in-memory store."""

    def _seed(
        *,
        idaccidente: str = "ACC-SEED-1",
        estado: str = "REPORTADO",
        activo: bool = True,
        **extra,
    ) -> str:
        repo = AccidenteRepository()
        estado_repo = EstadoAccidenteRepository()
        now = int(time.time() * 1000)
        repo.create(
            {
                "idaccidente": idaccidente,
                "latitudinicio": 19.4326,
                "longitudinicio": -99.1332,
                "fechahoraaccidente": now,
                "idseveridad": 2,
                "descripcion": "Accidente semilla",
                "idcalle": 1,
                "idusuario": 2,
                "numvehiculos": 1,
                "activo": activo,
                **extra,
            }
        )
        estado_repo.append_estado(idaccidente=idaccidente, estado=ESTADO_BORRADOR, idusuario=2)
        if estado != ESTADO_BORRADOR:
            estado_repo.append_estado(idaccidente=idaccidente, estado=estado, idusuario=2)
        return idaccidente

    return _seed
