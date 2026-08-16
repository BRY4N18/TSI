"""Datos sembrados para los informes tácticos de Soporte al Cliente.

**`dos_cuentas_reportadoras` es el fixture del que depende que este módulo esté
probado.** Si el Cliente y el Partner comparten cuenta, la prueba del
acotamiento del Partner pasa sin demostrar nada: no distingue «acotado a lo
suyo» de «no acotado en absoluto».

Los demás casos protegen defectos concretos:

* un ticket **`sin compromiso`** y otro **sin clasificar** — el primero está
  clasificado y no tiene plazo asignable, el segundo aún no llegó a tenerlo, y
  colapsarlos borra el único estado en que un ticket queda sin que ningún
  proceso lo mire;
* un **escalado manual**, uno **automático** y un **aviso de plazo próximo** —
  el aviso no es un escalado y no debe aparecer;
* un usuario con rol **de reporte y de atención a la vez**, que no queda acotado.

`mensaje` se siembra con un texto reconocible marcado como nota interna: si
aparece en una respuesta, la prueba de research D4 debe fallar.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from conftest import PINOT_STORE
from core.jwt_utils import create_access_token

#: Instante fijo: 2026-08-11T12:00:00Z.
AHORA = datetime(2026, 8, 11, 12, 0, 0, tzinfo=timezone.utc)
AHORA_MS = int(AHORA.timestamp() * 1000)
DIA_MS = 86_400_000

CUENTA_CLIENTE = 6401
CUENTA_PARTNER = 6402

USUARIO_CLIENTE = 6501
USUARIO_PARTNER = 6502
USUARIO_MIXTO = 6503  # Cliente **y** Agente de Soporte
AGENTE = 6504
GERENTE_EXITO = 6505
AJENO = 6506  # Operador de Emergencias

SERVICIO_SOPORTE = 6601

TICKET_CLIENTE = 6701
TICKET_CLIENTE_2 = 6702
TICKET_PARTNER = 6703
TICKET_SIN_COMPROMISO = 6704
TICKET_SIN_CLASIFICAR = 6705
TICKET_CON_FACTURA = 6706

#: Texto que jamás puede aparecer en una respuesta del listado de escalados.
NOTA_INTERNA = "NOTA-INTERNA-NO-DEBE-SALIR: el cliente miente sobre la fecha"


@pytest.fixture
def reloj_fijo():
    return lambda: AHORA_MS


@pytest.fixture
def cuentas_soporte(mock_pinot):
    PINOT_STORE["Dim_Usuarios"].extend(
        [
            {"idusuario": USUARIO_CLIENTE, "nombres": "Lucía", "apellidos": "Ferrer",
             "gmail": "lucia.ferrer@cliente.com", "activo": True,
             "fecha_actualizacion": AHORA_MS},
            {"idusuario": USUARIO_PARTNER, "nombres": "Diego", "apellidos": "Navarro",
             "gmail": "diego.navarro@partner.com", "activo": True,
             "fecha_actualizacion": AHORA_MS},
            {"idusuario": USUARIO_MIXTO, "nombres": "Rocío", "apellidos": "Peña",
             "gmail": "rocio.pena@cliente.com", "activo": True,
             "fecha_actualizacion": AHORA_MS},
            {"idusuario": AGENTE, "nombres": "Bruno", "apellidos": "Salas",
             "gmail": "bruno.salas@tsi.com", "activo": True,
             "fecha_actualizacion": AHORA_MS},
        ]
    )
    PINOT_STORE["Dim_Cliente"].extend(
        [
            {"idcliente": CUENTA_CLIENTE, "razon_social": "Transportes Ferrer S.A.",
             "tipo": "Corporativo", "estado": "Activo",
             "admin_local_id": USUARIO_CLIENTE,
             "fecha_creacion": AHORA_MS, "fecha_actualizacion": AHORA_MS},
            # ⚠️ Cuenta **distinta** de la del Cliente. Es lo que hace real la
            # prueba del acotamiento del Partner.
            {"idcliente": CUENTA_PARTNER, "razon_social": "Navarro Integraciones Ltda.",
             "tipo": "Corporativo", "estado": "Activo",
             "admin_local_id": USUARIO_PARTNER,
             "fecha_creacion": AHORA_MS, "fecha_actualizacion": AHORA_MS},
        ]
    )
    PINOT_STORE["Dim_Usuario_Cliente"].extend(
        [
            {"idusuario": USUARIO_CLIENTE, "idcliente": CUENTA_CLIENTE, "activo": True},
            {"idusuario": USUARIO_PARTNER, "idcliente": CUENTA_PARTNER, "activo": True},
            {"idusuario": USUARIO_MIXTO, "idcliente": CUENTA_CLIENTE, "activo": True},
        ]
    )
    PINOT_STORE["Dim_Servicio"].append(
        {"id_servicio": SERVICIO_SOPORTE, "nombre": "Portal de siniestros",
         "tipo": "web", "descripcion": "", "activo": True,
         "fecha_actualizacion": AHORA_MS}
    )


def _ticket(tid, *, idcliente, asunto, estado="Abierto", prioridad="Media",
            tipo_incidencia="Consulta", agente=AGENTE, sla_status="en curso",
            idfactura="", hace_dias=1):
    return {
        "id_reclamo": tid,
        "idcliente": idcliente,
        "idestadosoporte": 1,
        "idservicio": SERVICIO_SOPORTE,
        "idslaconfig": 1,
        "idfactura": idfactura,
        "tipo": "reclamo",
        "activo": True,
        "asunto": asunto,
        "prioridad": prioridad,
        # El cuerpo del reporte. No debe salir en el listado (research D6).
        "descripcion": "DESCRIPCION-LARGA-QUE-NO-APORTA-A-UNA-COLA",
        "id_agente_asignado": agente,
        "tipo_incidencia": tipo_incidencia,
        "sla_status": sla_status,
        "estado": estado,
        "cierreconfirmadocliente": False,
        "sla_primera_respuesta": AHORA_MS + DIA_MS,
        "sla_resolucion": AHORA_MS + 3 * DIA_MS,
        "tiempo_solucion": 0,
        "fechahora": AHORA_MS - hace_dias * DIA_MS,
        "fechahoraconfirmacioncierre": 0,
        "fecha_actualizacion": AHORA_MS,
    }


@pytest.fixture
def dos_cuentas_reportadoras(mock_pinot, cuentas_soporte):
    """Cliente y Partner en cuentas distintas, ambos con tickets."""
    PINOT_STORE["Fact_Reclamo"].extend(
        [
            _ticket(TICKET_CLIENTE, idcliente=CUENTA_CLIENTE,
                    asunto="No carga el expediente", hace_dias=1),
            _ticket(TICKET_CLIENTE_2, idcliente=CUENTA_CLIENTE,
                    asunto="Error al adjuntar fotos", estado="En_progreso",
                    sla_status="en riesgo", hace_dias=2),
            _ticket(TICKET_PARTNER, idcliente=CUENTA_PARTNER,
                    asunto="Timeout en la API de accidentes",
                    tipo_incidencia="Incidente", sla_status="incumplido",
                    hace_dias=3),
            # ⚠️ Clasificado, **sin plazo asignable**: nadie lo vigila.
            _ticket(TICKET_SIN_COMPROMISO, idcliente=CUENTA_CLIENTE,
                    asunto="Consulta sobre cobertura",
                    sla_status="sin compromiso", agente=0, hace_dias=4),
            # ⚠️ Aún **sin clasificar**: no hay contador todavía. Es otra cosa.
            _ticket(TICKET_SIN_CLASIFICAR, idcliente=CUENTA_CLIENTE,
                    asunto="Algo va mal", estado="Pendiente_de_clasificacion",
                    prioridad="", tipo_incidencia="", sla_status=None,
                    agente=0, hace_dias=5),
            _ticket(TICKET_CON_FACTURA, idcliente=CUENTA_PARTNER,
                    asunto="Disputa de la factura de julio",
                    idfactura="f7a1c3e0-0000-4000-8000-000000000001",
                    tipo_incidencia="Disputa", hace_dias=6),
        ]
    )


def _accion(hid, *, id_reclamo, tipo_accion, idusuario, anterior, nuevo,
            hace_dias, mensaje=NOTA_INTERNA, nota_interna=True):
    return {
        "id_historial": hid,
        "id_reclamo": id_reclamo,
        "tipo_accion": tipo_accion,
        # ⛔ Ninguna de estas dos columnas se consulta desde el listado.
        "mensaje": mensaje,
        "es_nota_interna": nota_interna,
        "idusuario": idusuario,
        "estado_anterior": anterior,
        "estado_nuevo": nuevo,
        "fecha_accion": AHORA_MS - hace_dias * DIA_MS,
        "fecha_actualizacion": AHORA_MS,
    }


@pytest.fixture
def escalados_sembrados(mock_pinot, dos_cuentas_reportadoras):
    """Un escalado manual, uno automático y un aviso que **no** es escalado."""
    PINOT_STORE["Fact_Historial_Ticket"].extend(
        [
            # Lo decidió una persona: lleva autor.
            _accion(6801, id_reclamo=TICKET_CLIENTE,
                    tipo_accion="escalado_manual", idusuario=AGENTE,
                    anterior="En_progreso", nuevo="Escalado", hace_dias=1),
            # ⚠️ Lo disparó el sistema: **sin autor**. El supervisor que lo
            # recibe es destinatario, no autor — por eso el campo va vacío.
            _accion(6802, id_reclamo=TICKET_PARTNER,
                    tipo_accion="escalado_automatico_sla", idusuario=0,
                    anterior="En_progreso", nuevo="Escalado", hace_dias=2),
            # ⚠️ Un **aviso** de plazo próximo: el ticket no cambió de agente
            # ni de nivel. No es un escalado y no debe aparecer.
            _accion(6803, id_reclamo=TICKET_CLIENTE_2,
                    tipo_accion="alerta_sla_riesgo", idusuario=0,
                    anterior="En_progreso", nuevo="En_progreso", hace_dias=3),
            # Acción del sistema, pero **cierra**: tampoco deriva nada.
            _accion(6804, id_reclamo=TICKET_CLIENTE_2,
                    tipo_accion="cierre_automatico_por_vencimiento", idusuario=0,
                    anterior="Resuelto", nuevo="Cerrado", hace_dias=4),
            _accion(6805, id_reclamo=TICKET_CLIENTE,
                    tipo_accion="comentario", idusuario=AGENTE,
                    anterior="Abierto", nuevo="Abierto", hace_dias=5),
            # Un escalado antiguo, fuera de un rango corto.
            _accion(6806, id_reclamo=TICKET_CON_FACTURA,
                    tipo_accion="escalado_manual", idusuario=AGENTE,
                    anterior="Abierto", nuevo="Escalado", hace_dias=200),
        ]
    )


@pytest.fixture
def todo_sembrado(dos_cuentas_reportadoras, escalados_sembrados):
    return True


def _headers(user_id: int, roles: list[str]) -> dict:
    token = create_access_token(user_id=user_id, roles=roles, session_id=1)
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


@pytest.fixture
def cliente_informes_headers(mock_pinot, mock_kafka):
    return _headers(USUARIO_CLIENTE, ["Cliente"])


@pytest.fixture
def partner_informes_headers(mock_pinot, mock_kafka):
    """Reporta igual que un Cliente, y **no es Cliente**.

    Si el acotamiento se decidiera por «ser Cliente», este usuario se saldría de
    él y vería los tickets de todas las cuentas.
    """
    return _headers(USUARIO_PARTNER, ["PartnerIntegracion"])


@pytest.fixture
def mixto_informes_headers(mock_pinot, mock_kafka):
    """Cliente **y** Agente: tener un rol de atención saca del acotamiento."""
    return _headers(USUARIO_MIXTO, ["Cliente", "Soporte"])


@pytest.fixture
def agente_informes_headers(mock_pinot, mock_kafka):
    return _headers(AGENTE, ["Soporte"])


@pytest.fixture
def gerente_exito_headers(mock_pinot, mock_kafka):
    """Autoridad del departamento. **No es `SupervisorSoporte`**, que es el
    destinatario operativo de un escalado automático."""
    return _headers(GERENTE_EXITO, ["GerenteExitoCliente"])


@pytest.fixture
def ajeno_informes_headers(mock_pinot, mock_kafka):
    return _headers(AJENO, ["OperadorDespacho"])
