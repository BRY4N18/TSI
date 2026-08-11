"""RNF-PAC-001 — la revocacion surte efecto en p95 <= 2 s (T050).

Que se mide exactamente
------------------------
No el tiempo de respuesta del endpoint, sino el que va desde que se acepta la
revocacion **hasta que la credencial deja de servir datos**. Son cosas distintas
y la segunda es la que importa: una revocacion que responde en 50 ms pero deja
la credencial sirviendo 15 s no ha revocado nada.

**Sin esperas artificiales.** Si esta medicion necesitara un `sleep` para pasar,
lo que estaria midiendo es la ingesta de Pinot y significaria que la ventana de
exposicion sigue abierta. Que no haga falta es el resultado.

Lo que esta medicion NO prueba
-------------------------------
Corre contra el doble en memoria de `conftest.py`. Mide el coste del camino de
codigo —bcrypt incluido—, **no** la latencia real de Kafka ni la de Pinot. La
prueba de que la ventana esta cerrada en el sistema real es
`database/verifica_acceso_partners.py` (T052), no este archivo.
"""

from __future__ import annotations

import time

import pytest

from apps.partners.services.revocar_credencial_service import RevocarCredencialService
from conftest import PINOT_STORE

pytestmark = [pytest.mark.slow, pytest.mark.api, pytest.mark.django_db]

URL_DATOS = "/api/v1/datos/accidentes"

# Holgado por la misma razon que en #07 y #08: bcrypt con coste 12 domina, y es
# inherente a la autenticacion. Bajarlo NO es la forma de mejorar este numero.
UMBRAL_P95_MS = 2000
MUESTRAS = 10


def _p95(muestras: list[float]) -> float:
    muestras.sort()
    return muestras[max(int(len(muestras) * 0.95) - 1, 0)]


class TestRevocacionEfectivaP95:
    def test_desde_la_revocacion_hasta_que_deja_de_servir(
        self, api_client, credencial_produccion_headers
    ):
        # Arrange — una credencial fresca por muestra. Cada iteracion deja la
        # anterior "activa en la base" para simular la ingesta pendiente, asi que
        # reutilizarlas chocaria de nombre entre si: es un artefacto del bucle,
        # no del producto (donde la revocada si queda inactiva).
        tiempos: list[float] = []

        for i in range(MUESTRAS):
            idcredencial = _sembrar_credencial(880, i)
            cabeceras = _cabeceras_de(idcredencial)

            # Act — se cronometra revocacion + primera peticion rechazada
            inicio = time.perf_counter()
            RevocarCredencialService().revocar(
                idcredencial=idcredencial,
                idpartner_actor=880,
                motivo="medición de RNF-PAC-001",
            )
            # La credencial sigue activa en la base: es el estado real durante
            # la ventana de ingesta. Aun asi debe rechazarse.
            _simular_ingesta_pendiente(idcredencial)
            respuesta = api_client.get(URL_DATOS, **cabeceras)
            transcurrido = (time.perf_counter() - inicio) * 1000

            assert respuesta.status_code == 401, (
                "La credencial revocada siguió sirviendo: la ventana de "
                "exposición está abierta"
            )
            tiempos.append(transcurrido)

        p95 = _p95(tiempos)
        print(
            f"\nRNF-PAC-001 — revocación efectiva:"
            f"\n  p95: {p95:.0f} ms  (umbral {UMBRAL_P95_MS} ms, n={MUESTRAS})"
            f"\n  medido SIN esperas: incluye emitir el reemplazo (bcrypt coste 12)"
            f"\n  mide el camino de código contra el doble, NO la latencia real "
            f"de Kafka/Pinot"
        )

        # Assert
        assert p95 <= UMBRAL_P95_MS


SECRETO = "secreto-de-medicion"


def _sembrar_credencial(idpartner: int, i: int) -> int:
    """Credencial nueva, con nombre único, hasheada de verdad con bcrypt.

    El hash real importa: lo que se mide es el camino completo de
    autenticación, y saltárselo mediría otra cosa.
    """
    from apps.partners.services.secreto_service import SecretoService

    # Zancada de 100: el reemplazo que emite cada revocacion toma `MAX(id)+1`,
    # asi que sembrar consecutivo haria que la siguiente muestra pisara el id de
    # un reemplazo ya emitido.
    idcredencial = 90_000 + i * 100
    PINOT_STORE["Dim_CredencialAPI"].append({
        "idcredencial": idcredencial,
        "idpartner": idpartner,
        "idcliente": idpartner,
        "client_secret_hash": SecretoService().hash(SECRETO),
        "nombre_credencial": f"medicion-{i}",
        "entorno": "Producción",
        "activo": True,
        "fecha_creacion": 1,
        "fecha_expiracion": 253402300799000,
        "fecha_actualizacion": 1,
    })
    return idcredencial


def _cabeceras_de(idcredencial: int) -> dict[str, str]:
    return {
        "HTTP_X_CLIENT_ID": f"tsi-p880-c{idcredencial}",
        "HTTP_X_CLIENT_SECRET": SECRETO,
    }


def _simular_ingesta_pendiente(idcredencial: int) -> None:
    for credencial in PINOT_STORE["Dim_CredencialAPI"]:
        if credencial["idcredencial"] == idcredencial:
            credencial["activo"] = True
