"""Seed demo Dim_Prospecto (+ Fact_Asignacion / Fact_Pipeline) for Ventas CRM UI.

Assigns prospects to demo GerenteVentas (lucia.ramos.ventas@demo.tsi.com).
Run after seed_demo_usuarios_roles.py so the gerente exists.

  docker exec accidentes-django python /app/scripts/seed_demo_prospectos.py
"""

from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.environ.get("PYTHONPATH", "/app"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from django.conf import settings  # noqa: E402

from core.pinot.client import PinotClient  # noqa: E402
from core.repositories.cuentas_clientes.kafka_writer import KafkaWriter  # noqa: E402

GERENTE_VENTAS_GMAIL = "lucia.ramos.ventas@demo.tsi.com"
GERENTE_VENTAS_FALLBACK_ID = 12

# Fixed demo IDs (high range) so re-runs upsert the same rows in Pinot realtime.
BASE_PROSPECTO_ID = 9001
BASE_ASIGNACION_ID = 9001
BASE_TRANSICION_ID = 9001

ETAPAS_ORDEN = ["Nuevo", "Contactado", "Calificado", "Propuesta", "Negociación"]


def _now_ms() -> int:
    return int(time.time() * 1000)


def _resolve_gerente_id(pinot: PinotClient) -> int:
    rows = pinot.query(
        "SELECT idusuario FROM Dim_Usuarios WHERE gmail = %(gmail)s LIMIT 1",
        {"gmail": GERENTE_VENTAS_GMAIL},
    )
    if rows:
        return int(rows[0]["idusuario"])
    print(
        f"WARN gerente no encontrado ({GERENTE_VENTAS_GMAIL}); "
        f"usando idusuario={GERENTE_VENTAS_FALLBACK_ID}"
    )
    return GERENTE_VENTAS_FALLBACK_ID


def _pipeline_chain(etapa: str) -> list[tuple[str | None, str]]:
    """Adjacent forward transitions up to `etapa` (or terminal)."""
    if etapa == "Perdido":
        # Lose early for variety
        return [(None, "Nuevo"), ("Nuevo", "Contactado"), ("Contactado", "Perdido")]
    if etapa == "Ganado":
        chain: list[tuple[str | None, str]] = [(None, "Nuevo")]
        for i in range(1, len(ETAPAS_ORDEN)):
            chain.append((ETAPAS_ORDEN[i - 1], ETAPAS_ORDEN[i]))
        chain.append(("Negociación", "Ganado"))
        return chain
    if etapa not in ETAPAS_ORDEN:
        return [(None, "Nuevo")]
    idx = ETAPAS_ORDEN.index(etapa)
    chain = [(None, "Nuevo")]
    for i in range(1, idx + 1):
        chain.append((ETAPAS_ORDEN[i - 1], ETAPAS_ORDEN[i]))
    return chain


def main() -> None:
    pinot = PinotClient()
    writer = KafkaWriter()
    topics = settings.KAFKA_TOPICS
    now = _now_ms()
    gerente_id = _resolve_gerente_id(pinot)

    demos: list[dict] = [
        {
            "offset": 0,
            "nombres": "Andrés",
            "apellidos": "Vega",
            "gmail": "andres.vega@municipio-norte.demo",
            "empresa": "Municipio Norte",
            "tipo_organizacion": "Público",
            "cargo": "Director de Movilidad",
            "telefono": "0991001001",
            "como_nos_conocio": "Referido institucional",
            "etapa_actual": "Nuevo",
            "activo": True,
            "motivo_inactividad": None,
            "valor_estimado": 12000.0,
        },
        {
            "offset": 1,
            "nombres": "María",
            "apellidos": "Salazar",
            "gmail": "maria.salazar@segurosdelta.demo",
            "empresa": "Seguros Delta",
            "tipo_organizacion": "Privado",
            "cargo": "Jefa de siniestros",
            "telefono": "0991001002",
            "como_nos_conocio": "Web / catálogo planes",
            "etapa_actual": "Contactado",
            "activo": True,
            "motivo_inactividad": None,
            "valor_estimado": 8500.0,
        },
        {
            "offset": 2,
            "nombres": "Carlos",
            "apellidos": "Mena",
            "gmail": "carlos.mena@flotaexpress.demo",
            "empresa": "Flota Express Cia. Ltda.",
            "tipo_organizacion": "Privado",
            "cargo": "Gerente de operaciones",
            "telefono": "0991001003",
            "como_nos_conocio": "Demo interactiva",
            "etapa_actual": "Calificado",
            "activo": True,
            "motivo_inactividad": None,
            "valor_estimado": 22000.0,
        },
        {
            "offset": 3,
            "nombres": "Elena",
            "apellidos": "Paredes",
            "gmail": "elena.paredes@smartcity-loja.demo",
            "empresa": "Smart City Loja",
            "tipo_organizacion": "Público",
            "cargo": "Coordinadora TIC",
            "telefono": "0991001004",
            "como_nos_conocio": "Evento municipal",
            "etapa_actual": "Propuesta",
            "activo": True,
            "motivo_inactividad": None,
            "valor_estimado": 45000.0,
        },
        {
            "offset": 4,
            "nombres": "Diego",
            "apellidos": "Ríos",
            "gmail": "diego.rios@aseguradoraandina.demo",
            "empresa": "Aseguradora Andina",
            "tipo_organizacion": "Privado",
            "cargo": "VP Comercial",
            "telefono": "0991001005",
            "como_nos_conocio": "LinkedIn",
            "etapa_actual": "Negociación",
            "activo": True,
            "motivo_inactividad": None,
            "valor_estimado": 68000.0,
        },
        {
            "offset": 5,
            "nombres": "Patricia",
            "apellidos": "Luna",
            "gmail": "patricia.luna@transurban.demo",
            "empresa": "TransUrban S.A.",
            "tipo_organizacion": "Privado",
            "cargo": "Analista de compras",
            "telefono": "0991001006",
            "como_nos_conocio": "Cold call",
            "etapa_actual": "Perdido",
            "activo": False,
            "motivo_inactividad": "perdido",
            "valor_estimado": 5000.0,
        },
        {
            "offset": 6,
            "nombres": "Jorge",
            "apellidos": "Cifuentes",
            "gmail": "jorge.cifuentes@gad-centro.demo",
            "empresa": "GAD Provincial Centro",
            "tipo_organizacion": "Público",
            "cargo": "Director de emergencias",
            "telefono": "0991001007",
            "como_nos_conocio": "Referido TSI",
            "etapa_actual": "Ganado",
            "activo": False,
            "motivo_inactividad": "convertido",
            "valor_estimado": 99000.0,
        },
        {
            "offset": 7,
            "nombres": "Sofía",
            "apellidos": "Navarrete",
            "gmail": "sofia.navarrete@rescuefleet.demo",
            "empresa": "Rescue Fleet Ecuador",
            "tipo_organizacion": "Privado",
            "cargo": "Fundadora",
            "telefono": "0991001008",
            "como_nos_conocio": "Feria logística",
            "etapa_actual": "Contactado",
            "activo": True,
            "motivo_inactividad": None,
            "valor_estimado": 15000.0,
        },
    ]

    asig_id = BASE_ASIGNACION_ID
    trans_id = BASE_TRANSICION_ID

    for demo in demos:
        pid = BASE_PROSPECTO_ID + int(demo["offset"])
        ts = now + int(demo["offset"])
        payload = {
            "idprospecto": pid,
            "nombres": demo["nombres"],
            "apellidos": demo["apellidos"],
            "gmail": demo["gmail"],
            "empresa": demo["empresa"],
            "tipo_organizacion": demo["tipo_organizacion"],
            "cargo": demo["cargo"],
            "telefono": demo["telefono"],
            "como_nos_conocio": demo["como_nos_conocio"],
            "etapa_actual": demo["etapa_actual"],
            "idusuario": gerente_id,
            "demo_expiracion": None,
            "activo": demo["activo"],
            "motivo_inactividad": demo["motivo_inactividad"],
            "valor_estimado": demo["valor_estimado"],
            "fecha_registro": ts,
            "fecha_actualizacion": ts + 10,
        }
        writer.publish(topics["prospecto"], payload)
        print(
            f"prospecto id={pid} etapa={demo['etapa_actual']} "
            f"activo={demo['activo']} → {demo['empresa']}"
        )

        writer.publish(
            topics["asignacion"],
            {
                "idasignacion": asig_id,
                "idprospecto": pid,
                "idusuariogerenteanterior": None,
                "idusuariogerenteactual": gerente_id,
                "tipoasignacion": "automatica",
                "motivo": None,
                "fechahoraasignacion": ts + 1,
                "fecha_actualizacion": ts + 1,
            },
        )
        print(f"  asignacion id={asig_id} → gerente={gerente_id}")
        asig_id += 1

        for etapa_ant, etapa_nueva in _pipeline_chain(str(demo["etapa_actual"])):
            if etapa_ant is None:
                # Initial state is denormalized on Dim_Prospecto; optional no-op skip
                continue
            motivo = "presupuesto insuficiente" if etapa_nueva == "Perdido" else None
            writer.publish(
                topics["pipeline"],
                {
                    "id_transicion": trans_id,
                    "id_prospecto": pid,
                    "etapa_anterior": etapa_ant,
                    "etapa_nueva": etapa_nueva,
                    "notas": f"Demo seed → {etapa_nueva}",
                    "motivo_perdida": motivo,
                    "gerente_id": gerente_id,
                    "fecha_transicion": ts + 20 + trans_id,
                    "fecha_actualizacion": ts + 20 + trans_id,
                },
            )
            print(f"  pipeline id={trans_id} {etapa_ant} → {etapa_nueva}")
            trans_id += 1

    print()
    print(f"OK — {len(demos)} prospectos para idusuario={gerente_id} ({GERENTE_VENTAS_GMAIL})")
    print("Espera ~5–15s Pinot realtime y refresca /ventas-crm/prospectos y /pipeline.")


if __name__ == "__main__":
    main()
