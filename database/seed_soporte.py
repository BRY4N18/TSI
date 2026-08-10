"""
Seed demo para Gestión de Tickets de Soporte (gestion-tickets-soporte).

Publica vía Kafka (único canal de escritura → Pinot):
  - Dim_Rol (corrige rol agente a "Soporte" + SupervisorSoporte)
  - Dim_Estado_Soporte, Dim_SLAConfig
  - Dim_Plan (mínimo idplan=1), Dim_Cliente, Dim_Usuario_Cliente, Fact_Suscripcion
  - Fact_Reclamo + Fact_Historial_Ticket (tickets de muestra para la Cola)

Prerrequisitos:
  - Contenedor `kafka` en ejecución
  - Usuarios demo ya sembrados (database/seed_usuarios.py) — Ana=1, Carlos=2, Lucia=3

Uso:
  python database/seed_soporte.py

Login sugerido:
  Agente:  lucia.vera.soporte@demo.tsi.com / Demo1234!
  Admin:   carlos.mendoza.admin@demo.tsi.com / Demo1234!
  Cliente: ana.torres.cliente@demo.tsi.com / Demo1234!
"""
from __future__ import annotations

import json
import subprocess
import time

NOW_MS = int(time.time() * 1000)
HOUR = 3_600_000
DAY = 86_400_000

# IDs alineados a seed_usuarios.py
ID_CLIENTE_USER = 1  # Ana Torres
ID_ADMIN = 2  # Carlos (también SOPORTE_SUPERVISOR_USER_ID default)
ID_AGENTE = 3  # Lucia Vera
ID_CLIENTE = 1
ID_PLAN = 1


def publish(topic: str, records: list[dict]) -> None:
    payload = "\n".join(json.dumps(r, ensure_ascii=False) for r in records)
    proc = subprocess.run(
        [
            "docker",
            "exec",
            "-i",
            "kafka",
            "kafka-console-producer",
            "--bootstrap-server",
            "localhost:9092",
            "--topic",
            topic,
        ],
        input=payload.encode("utf-8"),
        capture_output=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"Error publicando en {topic}: {proc.stderr.decode()}")
    print(f"Publicados {len(records)} registros en {topic}")


def main() -> None:
    # --- Roles canónicos (JWT / guards Angular esperan estos strings) ---
    roles = [
        {
            "idrol": 1,
            "rol": "Cliente",
            "descripcion": "Cliente que contrata el servicio",
            "activo": True,
            "fecha_actualizacion": NOW_MS,
        },
        {
            "idrol": 2,
            "rol": "Administrador",
            "descripcion": "Administrador general del sistema",
            "activo": True,
            "fecha_actualizacion": NOW_MS,
        },
        {
            "idrol": 3,
            "rol": "Soporte",
            "descripcion": "Atención de tickets y reclamos (Cola de soporte)",
            "activo": True,
            "fecha_actualizacion": NOW_MS,
        },
        {
            "idrol": 5,
            "rol": "DesarrolladorAPIs",
            "descripcion": "Nivel de escalado técnico",
            "activo": True,
            "fecha_actualizacion": NOW_MS,
        },
        {
            "idrol": 6,
            "rol": "DirectorTecnologico",
            "descripcion": "Nivel de escalado ejecutivo",
            "activo": True,
            "fecha_actualizacion": NOW_MS,
        },
        {
            "idrol": 10,
            "rol": "SupervisorSoporte",
            "descripcion": "Receptor de escalado automático SLA (RN-TIC-005)",
            "activo": True,
            "fecha_actualizacion": NOW_MS,
        },
    ]
    publish("Dim_Rol_topic", roles)

    # Lucia (3) → Soporte; Carlos (2) → SupervisorSoporte además de Admin (usuario_rol id 20)
    publish(
        "Dim_Usuario_Rol_topic",
        [
            {
                "idusuariorol": 3,
                "idusuario": ID_AGENTE,
                "idrol": 3,
                "activo": True,
                "fecha_actualizacion": NOW_MS,
            },
            {
                "idusuariorol": 20,
                "idusuario": ID_ADMIN,
                "idrol": 10,
                "activo": True,
                "fecha_actualizacion": NOW_MS,
            },
        ],
    )

    estados = [
        {"id_estado_soporte": 1, "nombre": "Abierto", "descripcion": "Ticket registrado", "activo": True},
        {
            "id_estado_soporte": 2,
            "nombre": "Pendiente_de_clasificacion",
            "descripcion": "Sin clasificar",
            "activo": True,
        },
        {"id_estado_soporte": 3, "nombre": "En_progreso", "descripcion": "En atención", "activo": True},
        {"id_estado_soporte": 4, "nombre": "Escalado", "descripcion": "Escalado", "activo": True},
        {"id_estado_soporte": 5, "nombre": "Resuelto", "descripcion": "Resuelto", "activo": True},
        {"id_estado_soporte": 6, "nombre": "Cerrado", "descripcion": "Cerrado", "activo": True},
        {"id_estado_soporte": 7, "nombre": "Reabierto", "descripcion": "Reabierto", "activo": True},
    ]
    publish("Dim_Estado_Soporte_topic", estados)

    publish(
        "Dim_Plan_topic",
        [
            {
                "idplan": ID_PLAN,
                "nombre": "Básico",
                "nivel": "Básico",
                "limites": json.dumps(
                    {"unidades_max": 5, "usuarios_max": 3, "api_calls_mes": 1000},
                    ensure_ascii=False,
                ),
                "activo": True,
                "precio": 49.0,
                "fecha_actualizacion": NOW_MS,
            }
        ],
    )

    sla_configs = [
        {
            "idslaconfig": 1,
            "idplan": ID_PLAN,
            "tipoincidencia": "tecnica",
            "prioridad": "alta",
            "activo": True,
            "tiemporespuestamax": 3600,
            "tiemporesolucionmax": 86400,
            "fechavigenciadesde": NOW_MS - DAY,
            "fechavigenciahasta": None,
            "fecha_actualizacion": NOW_MS,
        },
        {
            "idslaconfig": 2,
            "idplan": ID_PLAN,
            "tipoincidencia": "emergencia_activa",
            "prioridad": "crítico",
            "activo": True,
            "tiemporespuestamax": 60,
            "tiemporesolucionmax": 3600,
            "fechavigenciadesde": NOW_MS - DAY,
            "fechavigenciahasta": None,
            "fecha_actualizacion": NOW_MS,
        },
        {
            "idslaconfig": 3,
            "idplan": ID_PLAN,
            "tipoincidencia": "acceso",
            "prioridad": "media",
            "activo": True,
            "tiemporespuestamax": 7200,
            "tiemporesolucionmax": 172800,
            "fechavigenciadesde": NOW_MS - DAY,
            "fechavigenciahasta": None,
            "fecha_actualizacion": NOW_MS,
        },
        {
            "idslaconfig": 4,
            "idplan": ID_PLAN,
            "tipoincidencia": "consulta_funcional",
            "prioridad": "baja",
            "activo": True,
            "tiemporespuestamax": 14400,
            "tiemporesolucionmax": 259200,
            "fechavigenciadesde": NOW_MS - DAY,
            "fechavigenciahasta": None,
            "fecha_actualizacion": NOW_MS,
        },
        {
            "idslaconfig": 5,
            "idplan": ID_PLAN,
            "tipoincidencia": "Facturación",
            "prioridad": "baja",
            "activo": True,
            "tiemporespuestamax": 14400,
            "tiemporesolucionmax": 259200,
            "fechavigenciadesde": NOW_MS - DAY,
            "fechavigenciahasta": None,
            "fecha_actualizacion": NOW_MS,
        },
    ]
    publish("Dim_SLAConfig_topic", sla_configs)

    publish(
        "Dim_Cliente_topic",
        [
            {
                "idcliente": ID_CLIENTE,
                "nombre": "Empresa Demo Torres",
                "razon_social": "Empresa Demo Torres S.A.S.",
                "tipo": "Corporativo",
                "nit_identificacion": "900123456-1",
                "logo_url": None,
                "admin_local_id": ID_CLIENTE_USER,
                "estado": "Activo",
                "fecha_actualizacion": NOW_MS,
            }
        ],
    )
    publish(
        "Dim_Usuario_Cliente_topic",
        [
            {
                # Clave primaria de la tabla (upsert de Pinot). Sin ella el
                # registro entra con el centinela de nulo de INT y queda como
                # una fila huerfana aparte del vinculo real.
                "idusuariocliente": ID_CLIENTE_USER,
                "idusuario": ID_CLIENTE_USER,
                "idcliente": ID_CLIENTE,
                "activo": True,
                "fecha_actualizacion": NOW_MS,
            }
        ],
    )
    publish(
        "Fact_Suscripcion_topic",
        [
            {
                "id_suscripcion": 1,
                "idcliente": ID_CLIENTE,
                "idplan": ID_PLAN,
                "estado": "Activa",
                "activo": True,
                "renovacionautomatica": True,
                "motivocancelacion": None,
                "fechacancelacion": None,
                "precio": 49.0,
                "fecha_inicio": NOW_MS - 30 * DAY,
                "fecha_fin": NOW_MS + 335 * DAY,
                "fecha_actualizacion": NOW_MS,
            }
        ],
    )

    # Tickets de muestra (estados variados para ejercitar la Cola)
    tickets = [
        {
            "id_reclamo": 1,
            "idcliente": ID_CLIENTE,
            "asunto": "La API no responde — error 500",
            "descripcion": "Desde hace 1 hora las llamadas a partners-api devuelven error 500 constante.",
            "tipo": "tecnico",
            "tipo_incidencia": "tecnica",
            "prioridad": "alta",
            "estado": "Abierto",
            "idestadosoporte": 1,
            "idslaconfig": 1,
            "sla_status": "en curso",
            "sla_primera_respuesta": NOW_MS + HOUR,
            "sla_resolucion": NOW_MS + DAY,
            "id_agente_asignado": None,
            "cierreconfirmadocliente": False,
            "activo": True,
            "fechahora": NOW_MS - 30 * 60_000,
            "fecha_actualizacion": NOW_MS,
        },
        {
            "id_reclamo": 2,
            "idcliente": ID_CLIENTE,
            "asunto": "No puedo hacer login",
            "descripcion": "Mi usuario aparece bloqueado y no puedo acceso al portal.",
            "tipo": "acceso",
            "tipo_incidencia": "acceso",
            "prioridad": "media",
            "estado": "En_progreso",
            "idestadosoporte": 3,
            "idslaconfig": 3,
            "sla_status": "en curso",
            "sla_primera_respuesta": NOW_MS + 2 * HOUR,
            "sla_resolucion": NOW_MS + 2 * DAY,
            "id_agente_asignado": ID_AGENTE,
            "cierreconfirmadocliente": False,
            "activo": True,
            "fechahora": NOW_MS - 2 * HOUR,
            "fecha_actualizacion": NOW_MS,
        },
        {
            "id_reclamo": 3,
            "idcliente": ID_CLIENTE,
            "asunto": "Consulta: cómo funciona el dashboard",
            "descripcion": "Tengo una duda sobre cómo filtrar métricas en el dashboard de soporte.",
            "tipo": "consulta",
            "tipo_incidencia": "consulta_funcional",
            "prioridad": "baja",
            "estado": "Abierto",
            "idestadosoporte": 1,
            "idslaconfig": 4,
            "sla_status": "en curso",
            "sla_primera_respuesta": NOW_MS + 4 * HOUR,
            "sla_resolucion": NOW_MS + 3 * DAY,
            "id_agente_asignado": None,
            "cierreconfirmadocliente": False,
            "activo": True,
            "fechahora": NOW_MS - HOUR,
            "fecha_actualizacion": NOW_MS,
        },
        {
            "id_reclamo": 4,
            "idcliente": ID_CLIENTE,
            "asunto": "Ticket de prueba Facturación #9",
            "descripcion": "Consulta sobre cargo duplicado en la última factura.",
            "tipo": "Facturación",
            "tipo_incidencia": "Facturación",
            "prioridad": "baja",
            "estado": "Resuelto",
            "idestadosoporte": 5,
            "idslaconfig": 5,
            "sla_status": "cumplido",
            "sla_primera_respuesta": NOW_MS - DAY,
            "sla_resolucion": NOW_MS - HOUR,
            "id_agente_asignado": ID_AGENTE,
            "cierreconfirmadocliente": False,
            "activo": True,
            "fechahora": NOW_MS - 2 * DAY,
            "fecha_actualizacion": NOW_MS,
        },
        {
            "id_reclamo": 5,
            "idcliente": ID_CLIENTE,
            "asunto": "Reporte genérico sin keywords",
            "descripcion": "Problema reportado sin detalle suficiente para clasificar.",
            "tipo": "otro",
            "tipo_incidencia": None,
            "prioridad": None,
            "estado": "Pendiente_de_clasificacion",
            "idestadosoporte": 2,
            "idslaconfig": None,
            "sla_status": None,
            "sla_primera_respuesta": None,
            "sla_resolucion": None,
            "id_agente_asignado": None,
            "cierreconfirmadocliente": False,
            "activo": True,
            "fechahora": NOW_MS - 45 * 60_000,
            "fecha_actualizacion": NOW_MS,
        },
        {
            "id_reclamo": 6,
            "idcliente": ID_CLIENTE,
            "asunto": "API caído — escalado por SLA",
            "descripcion": "El endpoint de despacho no responde desde ayer (api caído).",
            "tipo": "tecnico",
            "tipo_incidencia": "tecnica",
            "prioridad": "alta",
            "estado": "Escalado",
            "idestadosoporte": 4,
            "idslaconfig": 1,
            "sla_status": "incumplido",
            "sla_primera_respuesta": NOW_MS - DAY,
            "sla_resolucion": NOW_MS - HOUR,
            "id_agente_asignado": ID_ADMIN,
            "cierreconfirmadocliente": False,
            "activo": True,
            "fechahora": NOW_MS - 2 * DAY,
            "fecha_actualizacion": NOW_MS,
        },
        {
            "id_reclamo": 7,
            "idcliente": ID_CLIENTE,
            "asunto": "Ticket de prueba #7 cerrado",
            "descripcion": "Incidencia de facturación ya cerrada por el cliente.",
            "tipo": "Facturación",
            "tipo_incidencia": "Facturación",
            "prioridad": "baja",
            "estado": "Cerrado",
            "idestadosoporte": 6,
            "idslaconfig": 5,
            "sla_status": "cumplido",
            "sla_primera_respuesta": NOW_MS - 5 * DAY,
            "sla_resolucion": NOW_MS - 4 * DAY,
            "id_agente_asignado": ID_AGENTE,
            "cierreconfirmadocliente": True,
            "fechahoraconfirmacioncierre": NOW_MS - 3 * DAY,
            "activo": True,
            "fechahora": NOW_MS - 6 * DAY,
            "fecha_actualizacion": NOW_MS,
        },
    ]
    publish("Fact_Reclamo_topic", tickets)

    historial = [
        {
            "id_historial": 1,
            "id_reclamo": 1,
            "idusuario": ID_CLIENTE_USER,
            "tipo_accion": "creacion",
            "mensaje": "Ticket creado por el cliente",
            "es_nota_interna": False,
            "estado_anterior": None,
            "estado_nuevo": "Abierto",
            "fecha_accion": NOW_MS - 30 * 60_000,
            "fecha_actualizacion": NOW_MS,
        },
        {
            "id_historial": 2,
            "id_reclamo": 2,
            "idusuario": ID_CLIENTE_USER,
            "tipo_accion": "creacion",
            "mensaje": "Ticket de acceso creado",
            "es_nota_interna": False,
            "estado_anterior": None,
            "estado_nuevo": "Abierto",
            "fecha_accion": NOW_MS - 2 * HOUR,
            "fecha_actualizacion": NOW_MS,
        },
        {
            "id_historial": 3,
            "id_reclamo": 2,
            "idusuario": ID_AGENTE,
            "tipo_accion": "asignacion_agente",
            "mensaje": "Agente tomó el ticket",
            "es_nota_interna": False,
            "estado_anterior": "Abierto",
            "estado_nuevo": "En_progreso",
            "fecha_accion": NOW_MS - HOUR,
            "fecha_actualizacion": NOW_MS,
        },
        {
            "id_historial": 4,
            "id_reclamo": 2,
            "idusuario": ID_AGENTE,
            "tipo_accion": "comentario",
            "mensaje": "Revisando bloqueo de cuenta en auth",
            "es_nota_interna": True,
            "estado_anterior": "En_progreso",
            "estado_nuevo": "En_progreso",
            "fecha_accion": NOW_MS - 50 * 60_000,
            "fecha_actualizacion": NOW_MS,
        },
        {
            "id_historial": 5,
            "id_reclamo": 2,
            "idusuario": ID_AGENTE,
            "tipo_accion": "comentario",
            "mensaje": "Estamos validando tu usuario; te avisamos en breve.",
            "es_nota_interna": False,
            "estado_anterior": "En_progreso",
            "estado_nuevo": "En_progreso",
            "fecha_accion": NOW_MS - 40 * 60_000,
            "fecha_actualizacion": NOW_MS,
        },
        {
            "id_historial": 6,
            "id_reclamo": 4,
            "idusuario": ID_AGENTE,
            "tipo_accion": "resolucion",
            "mensaje": "Se anuló el cargo duplicado.",
            "es_nota_interna": False,
            "estado_anterior": "En_progreso",
            "estado_nuevo": "Resuelto",
            "fecha_accion": NOW_MS - HOUR,
            "fecha_actualizacion": NOW_MS,
        },
        {
            "id_historial": 7,
            "id_reclamo": 7,
            "idusuario": ID_CLIENTE_USER,
            "tipo_accion": "cierre_confirmado",
            "mensaje": "Cliente confirmó el cierre",
            "es_nota_interna": False,
            "estado_anterior": "Resuelto",
            "estado_nuevo": "Cerrado",
            "fecha_accion": NOW_MS - 3 * DAY,
            "fecha_actualizacion": NOW_MS,
        },
    ]
    publish("Fact_Historial_Ticket_topic", historial)

    print("\nEsperando ingest Pinot (~8s)...")
    time.sleep(8)

    print(
        "\n=== Seed soporte listo ===\n"
        "Cola: http://localhost:4200/soporte-cliente/cola\n\n"
        "Credenciales (password Demo1234!):\n"
        "  lucia.vera.soporte@demo.tsi.com     = rol Soporte (agente)\n"
        "  carlos.mendoza.admin@demo.tsi.com   = Administrador / supervisor SLA\n"
        "  ana.torres.cliente@demo.tsi.com     = Cliente (crear tickets)\n\n"
        "Tickets sembrados: #1 Abierto, #2 En_progreso, #3 Abierto baja, #4 Resuelto,\n"
        "                   #5 Pendiente_de_clasificacion, #6 Escalado, #7 Cerrado\n"
    )


if __name__ == "__main__":
    main()
