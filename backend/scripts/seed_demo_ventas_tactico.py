"""Siembra los casos que los informes tácticos de Ventas y CRM necesitan para
poder demostrarse (T002, T003 y T004 de su `tasks.md`).

Es **aditivo** a `seed_demo_prospectos.py`, que no se toca: aquel siembra la
cartera de un único gerente, y eso es justo lo que impide verificar el
acotamiento.

Por qué cada caso está aquí
---------------------------

**Un segundo gerente con cartera propia (T002).** Es el más importante y el más
fácil de omitir. **Con una sola cartera poblada, filtrar y no filtrar dan el
mismo resultado**, así que las pruebas de acotamiento pasan aunque el
acotamiento no exista. Dos carteras a la vez es la única forma de que el fallo
tenga dónde manifestarse.

**Un perdido y un convertido a la vez (T003).** Los dos dejan `activo = false`,
y confundirlos presenta los éxitos comerciales como fracasos. `seed_demo_prospectos`
ya siembra uno de cada (offsets 5 y 6) para el gerente original; aquí se repiten
en la cartera del segundo para que la distinción se pueda comprobar también bajo
acotamiento.

**Demos con formato de fecha mixto (T004).** `demo_expiracion` es texto y el
sistema acepta sufijo `Z`, `+00:00` y sin zona. Dos demos con **la misma fecha
y distinto sufijo** deben aparecer o desaparecer juntas; si solo sale una, una
comparación de texto se coló en la consulta. Se siembra además una expirada hoy
más temprano, que el prefiltro por día deja pasar y el refinamiento debe
descartar.

Ejecución:

    docker exec accidentes-django python /app/scripts/seed_demo_ventas_tactico.py

Requiere `seed_demo_usuarios_roles.py` antes (para que exista el rol
`GerenteVentas`).
"""

from __future__ import annotations

import os
import sys
import time
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.environ.get("PYTHONPATH", "/app"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from django.conf import settings  # noqa: E402

from core.pinot.client import PinotClient  # noqa: E402
import bcrypt  # noqa: E402

from core.repositories.cuentas_clientes.kafka_writer import KafkaWriter  # noqa: E402
from scripts._demo_seed_common import (  # noqa: E402
    DEMO_PASSWORD,
    ESTADO_CREDENCIAL_ACTIVO,
)

# Segundo gerente. Correo y ids fijos en rango alto para que re-ejecutar
# actualice las mismas filas en vez de duplicarlas (las tablas son upsert por PK).
GERENTE_2_GMAIL = "pablo.andrade.ventas@demo.tsi.com"
GERENTE_2_USER_ID = 9502
GERENTE_2_CRED_ID = 9502
GERENTE_2_USER_ROLE_ID = 9502

BASE_PROSPECTO_ID = 9100
BASE_ASIGNACION_ID = 9100
BASE_TRANSICION_ID = 9100
BASE_NOTIFICACION_ID = 9100


def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def _now_ms() -> int:
    return int(time.time() * 1000)


def _rol_gerente_ventas(pinot: PinotClient) -> int:
    filas = pinot.query(
        "SELECT idrol FROM Dim_Rol WHERE rol = %(rol)s LIMIT 1", {"rol": "GerenteVentas"}
    )
    if not filas:
        raise SystemExit(
            "No existe el rol 'GerenteVentas'. Ejecuta antes seed_demo_usuarios_roles.py."
        )
    return int(filas[0]["idrol"])


def _sembrar_gerente(writer: KafkaWriter, topics: dict, idrol: int, now: int) -> None:
    writer.publish(
        topics["user"],
        {
            "idusuario": GERENTE_2_USER_ID,
            "nombres": "Pablo",
            "apellidos": "Andrade",
            "gmail": GERENTE_2_GMAIL,
            "identificacion": "0995500221",
            "genero": "M",
            "telefono": "0995500221",
            # `fechanacimiento` es LONG epoch-ms: una cadena hace que Pinot
            # descarte la fila entera sin avisar.
            "fechanacimiento": 662688000000,
            "activo": True,
            "fecha_actualizacion": now,
        },
    )
    writer.publish(
        topics["credential"],
        {
            "idcredencial": GERENTE_2_CRED_ID,
            "idusuario": GERENTE_2_USER_ID,
            "contrasena": _hash(DEMO_PASSWORD),
            "estadocredencial": ESTADO_CREDENCIAL_ACTIVO,
            "fecha_actualizacion": now,
        },
    )
    writer.publish(
        topics["user_role"],
        {
            "idusuariorol": GERENTE_2_USER_ROLE_ID,
            "idusuario": GERENTE_2_USER_ID,
            "idrol": idrol,
            "activo": True,
            "fecha_actualizacion": now,
        },
    )
    print(f"gerente 2 → {GERENTE_2_GMAIL} idusuario={GERENTE_2_USER_ID}")


def _expiraciones(ahora: datetime) -> list[tuple[str, str]]:
    """Casos de `demo_expiracion` que la consulta debe tratar igual o distinguir."""
    en_tres_dias = (ahora + timedelta(days=3)).replace(microsecond=0)
    return [
        # Misma fecha y hora, distinto sufijo: deben salir o no salir JUNTAS.
        ("sufijo Z", en_tres_dias.strftime("%Y-%m-%dT%H:%M:%SZ")),
        ("sufijo +00:00", en_tres_dias.isoformat()),
        # Sin zona horaria: el tercer formato que el parseador tolera.
        ("sin zona", en_tres_dias.strftime("%Y-%m-%dT%H:%M:%S")),
        # Expirada hoy más temprano: el prefiltro por día la deja pasar y el
        # refinamiento en el servicio debe descartarla.
        (
            "expirada hoy",
            ahora.replace(hour=0, minute=1, second=0, microsecond=0).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            ),
        ),
        # Sin fecha: no se considera demo activa.
        ("sin fecha", None),
    ]


def main() -> None:
    pinot = PinotClient()
    writer = KafkaWriter()
    topics = settings.KAFKA_TOPICS
    now = _now_ms()
    ahora = datetime.now(timezone.utc)

    _sembrar_gerente(writer, topics, _rol_gerente_ventas(pinot), now)

    # Cartera propia del segundo gerente: un activo, un perdido y un convertido,
    # más las cinco demos de formato mixto.
    casos = [
        ("Constructora Pacífico", "Activo en curso", "Negociación", True, None, None),
        ("Logística Andes", "Oportunidad perdida", "Perdido", False, "perdido", None),
        ("Municipio del Este", "Ya es cliente", "Ganado", False, "convertido", None),
    ]
    for etiqueta, expiracion in _expiraciones(ahora):
        casos.append((f"Demo {etiqueta}", etiqueta, "Contactado", True, None, expiracion))

    asig_id = BASE_ASIGNACION_ID
    trans_id = BASE_TRANSICION_ID

    for offset, (empresa, cargo, etapa, activo, motivo, expiracion) in enumerate(casos):
        pid = BASE_PROSPECTO_ID + offset
        ts = now + offset
        writer.publish(
            topics["prospecto"],
            {
                "idprospecto": pid,
                "nombres": "Contacto",
                "apellidos": f"Demo {offset}",
                "gmail": f"contacto{offset}@{empresa.split()[0].lower()}.demo",
                "empresa": empresa,
                "tipo_organizacion": "Público" if "Municipio" in empresa else "Privado",
                "cargo": cargo,
                "telefono": f"09955002{offset:02d}",
                "como_nos_conocio": "Siembra táctica",
                "etapa_actual": etapa,
                "idusuario": GERENTE_2_USER_ID,
                "demo_expiracion": expiracion,
                "activo": activo,
                "motivo_inactividad": motivo,
                "valor_estimado": 10000.0 + offset * 500,
                "fecha_registro": ts,
                "fecha_actualizacion": ts + 10,
            },
        )
        print(f"prospecto id={pid} {empresa} etapa={etapa} expiracion={expiracion}")

        writer.publish(
            topics["asignacion"],
            {
                "idasignacion": asig_id,
                "idprospecto": pid,
                # La primera asignación no tiene responsable anterior: se
                # publica ausente, y el informe debe mostrarlo así.
                "idusuariogerenteanterior": None,
                "idusuariogerenteactual": GERENTE_2_USER_ID,
                "tipoasignacion": "automatica",
                "motivo": None,
                "fechahoraasignacion": ts + 1,
                "fecha_actualizacion": ts + 1,
            },
        )
        asig_id += 1

        if motivo == "perdido":
            # `motivo_perdida` vive en la transición del embudo, no en el
            # prospecto: sin esta fila el listado no puede explicar la pérdida.
            writer.publish(
                topics["pipeline"],
                {
                    "id_transicion": trans_id,
                    "id_prospecto": pid,
                    "etapa_anterior": "Contactado",
                    "etapa_nueva": "Perdido",
                    "notas": "Siembra táctica",
                    "motivo_perdida": "eligió a un competidor",
                    "gerente_id": GERENTE_2_USER_ID,
                    "fecha_transicion": ts + 20,
                    "fecha_actualizacion": ts + 20,
                },
            )
            trans_id += 1

    # Una reasignación real (con responsable anterior) para contrastarla con las
    # primeras asignaciones de arriba.
    writer.publish(
        topics["asignacion"],
        {
            "idasignacion": asig_id,
            "idprospecto": BASE_PROSPECTO_ID,
            "idusuariogerenteanterior": GERENTE_2_USER_ID,
            "idusuariogerenteactual": GERENTE_2_USER_ID,
            "tipoasignacion": "manual",
            "motivo": "reparto de cartera",
            "fechahoraasignacion": now + 100,
            "fecha_actualizacion": now + 100,
        },
    )

    # Notificación dirigida al segundo gerente, para acotar por destinatario.
    writer.publish(
        topics["notificacion_ventas"],
        {
            "idnotificacion": BASE_NOTIFICACION_ID,
            "id_prospecto": BASE_PROSPECTO_ID,
            "idinteraccion": None,
            "idusuariogerentenotificado": GERENTE_2_USER_ID,
            "regladisparada": "visita repetida a precios",
            "canal": "correo",
            "estado_envio": None,
            "fechahoranotificacion": now + 200,
            "fecha_actualizacion": now + 200,
        },
    )

    print()
    print(f"OK — {len(casos)} prospectos para idusuario={GERENTE_2_USER_ID} ({GERENTE_2_GMAIL})")
    print(f"Contraseña: {DEMO_PASSWORD}")
    print("Espera ~5-15 s la ingesta de Pinot antes de consultar los informes.")


if __name__ == "__main__":
    main()
