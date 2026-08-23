"""PG-SEC-005/007 — ningún error revela datos de una víctima.

TSI enlaza ubicación, identidad de personas implicadas en accidentes y datos
potencialmente de salud. El Principio V de la constitución los declara sensibles
y exige control de acceso **y registro de auditoría**; el Principio IX recuerda
de quién son esos datos.

Lo que aquí se comprueba no es que el sistema falle poco, sino **qué cuenta
cuando falla**. Un `500` es un incidente técnico; un `500` con el traceback, la
consulta SQL y las coordenadas de una víctima es una filtración.

Dos superficies distintas, y conviene no confundirlas:

- **La respuesta** la ve quien hizo la petición, incluido un atacante que provoca
  el error a propósito.
- **El log** lo ve quien administre el servidor y, muy a menudo, cualquier
  servicio de agregación al que se reenvíe. Es la superficie que se olvida.

Contrato: `contracts/respuestas-seguridad.md` §C7.
"""

from __future__ import annotations

import logging
import re

import pytest
from rest_framework.test import APIClient

from apps.partners.domain_constants import ROL_ADMINISTRADOR
from core.jwt_utils import create_access_token

pytestmark = [pytest.mark.api, pytest.mark.seguridad]

USUARIO = 3
SESION = 1

#: Rastros que **nunca** deben aparecer en una respuesta de error. No son
#: ejemplos: son lo que el sistema realmente escribiría al filtrarse.
RASTROS_INTERNOS = (
    "Traceback",
    "File \"",
    "site-packages",
    "SELECT ",
    "FROM Dim_",
    "FROM Fact_",
    "pinot",
    "clickhouse",
    "settings.py",
)

#: Datos personales presentes en el almacén de pruebas. Si aparecen en un log o
#: en una respuesta, la fuga es real y no hipotética.
DATOS_PERSONALES = {
    "identificacion": "1234567890",
    "gmail": "admin@tsi.com",
}


def _cliente(roles=None) -> APIClient:
    api = APIClient()
    api.credentials(
        HTTP_AUTHORIZATION=(
            f"Bearer {create_access_token(user_id=USUARIO, roles=roles or [ROL_ADMINISTRADOR], session_id=SESION)}"
        )
    )
    return api


# --- La respuesta no cuenta de más -------------------------------------------


@pytest.mark.parametrize(
    "url",
    [
        "/api/v1/usuarios/999999",
        "/api/v1/accidentes/NO-EXISTE",
        "/api/v1/soporte/tickets/999999",
        "/api/v1/partners/999999",
    ],
)
def test_un_error_no_revela_las_tripas_del_sistema(url):
    """Un `404` o un `403` no deben describir cómo está construido el sistema.

    Cada nombre de tabla o fragmento de consulta que se escapa en un mensaje le
    ahorra trabajo de reconocimiento a quien esté probando la API.
    """
    cuerpo = _cliente().get(url).content.decode("utf-8", errors="replace")

    filtrados = [r for r in RASTROS_INTERNOS if r.lower() in cuerpo.lower()]
    assert not filtrados, f"{url} revela {filtrados} en la respuesta: {cuerpo[:200]}"


@pytest.mark.parametrize("payload", [
    {"campo_inexistente": "x"},
    {"idusuario": "no-es-un-numero"},
    {"fechanacimiento": "2026-02-30"},
])
def test_una_entrada_invalida_no_provoca_un_500(payload):
    """Un `500` ante entrada malformada es una fuga en potencia.

    No por el código en sí, sino porque el camino del `500` es el único que no
    pasa por el manejador central — y por tanto el único sin garantías sobre lo
    que enseña.
    """
    respuesta = _cliente().post("/api/v1/usuarios", payload, format="json")

    assert respuesta.status_code < 500, (
        f"{payload} produjo {respuesta.status_code}. Una entrada inválida debe "
        "rechazarse con 4xx por el manejador central, no reventar."
    )


def test_un_error_de_validacion_no_devuelve_el_valor_recibido_en_crudo():
    """Devolver la entrada tal cual es cómo se reflejan cargas de otros ataques."""
    sonda = "<script>alert(1)</script>"
    respuesta = _cliente().post("/api/v1/usuarios", {"gmail": sonda}, format="json")
    cuerpo = respuesta.content.decode("utf-8", errors="replace")

    assert "<script>" not in cuerpo, (
        "La respuesta refleja la entrada sin escapar. Aunque una API JSON no "
        "ejecute nada, el cliente que la pinte sí puede."
    )


# --- El log no cuenta de más --------------------------------------------------


def test_el_log_no_escribe_datos_personales_en_claro(caplog):
    """La superficie que se olvida.

    Los logs se reenvían a servicios de agregación, se comparten al depurar y se
    conservan más tiempo que cualquier respuesta HTTP. Un dato personal escrito
    en claro aquí sobrevive mucho más que uno filtrado en una petición.
    """
    with caplog.at_level(logging.DEBUG):
        _cliente().get(f"/api/v1/usuarios/{USUARIO}")

    texto = "\n".join(r.getMessage() for r in caplog.records)
    filtrados = {
        campo: valor for campo, valor in DATOS_PERSONALES.items() if valor in texto
    }
    assert not filtrados, (
        f"El log escribe datos personales en claro: {filtrados}. "
        "Deben enmascararse (PG-SEC-007, constitución Principio V)."
    )


def test_el_log_no_escribe_credenciales(caplog):
    """Un token en el log es una credencial válida en un fichero de texto."""
    with caplog.at_level(logging.DEBUG):
        _cliente().get("/api/v1/usuarios")

    texto = "\n".join(r.getMessage() for r in caplog.records)
    assert "Bearer " not in texto, "El log contiene una cabecera Authorization."
    assert not re.search(r"eyJ[A-Za-z0-9_-]{10,}", texto), (
        "El log contiene lo que parece un JWT en claro."
    )


def test_el_log_no_escribe_coordenadas_de_victimas(caplog):
    """La ubicación de un accidente identifica a quien estuvo en él."""
    from tests.seguridad import datos_dos_tenants as datos

    with caplog.at_level(logging.DEBUG):
        _cliente().get(f"/api/v1/accidentes/{datos.ACCIDENTE_A}")

    texto = "\n".join(r.getMessage() for r in caplog.records)
    for coordenada in ("19.4326", "-99.1332"):
        assert coordenada not in texto, (
            f"El log escribe la coordenada {coordenada} de un accidente en claro."
        )
