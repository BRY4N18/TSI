"""Siembra de dos tenants con recursos propios, para poder probar IDOR (T078).

Por que hace falta. La primera version de la suite de aislamiento reportaba
«82 passed» sin haber ejercitado la tenencia ni una vez: el actor era un
`PartnerIntegracion` y ese rol se deniega por **autorizacion vertical** en casi
todos los endpoints. Ademas, `Dim_Partner`, `Fact_Reclamo`, `Fact_Factura` y
`Dim_Prospecto` estan **vacios** en el store inicial de `conftest.py`, asi que ni
siquiera habia recursos que pedir.

Probar IDOR exige las dos cosas a la vez: **el rol correcto y el tenant
equivocado**. Un solo actor no llega, y sin datos sembrados el 404 es cierto y no
prueba nada.

Los ids del tenant B son deliberadamente altos (`999x`) para que un fallo de
aislamiento sea obvio al leerlo en un aserto.
"""

from __future__ import annotations

from typing import Any

#: Cliente al que pertenece el actor de las pruebas. Ya existe en el store raiz.
TENANT_A = 1
#: Cliente ajeno. Sus recursos son los que nadie de A debe alcanzar.
TENANT_B = 999

#: Usuarios. El 3 y el 4 ya existen en el store raiz y pertenecen al cliente 1.
USUARIO_A = 3
USUARIO_B = 9903

AHORA = "2026-08-23T00:00:00+00:00"
TS = 1_756_000_000_000  # epoch ms, dentro del rango que usan las demas pruebas

# --- Eje de tenencia de los accidentes -------------------------------------
#
# **No es `idcliente`.** Un accidente pertenece a un cliente si ocurrio en un
# condado que ese cliente tiene contratado: `idcalle` -> `idcondado` -> el JSON
# `zonas_geograficas` de `Dim_Preferencias_Cliente` (ver
# `apps/seguimiento/views/cliente_expediente_views.py::_condados_cliente`).
#
# Es un eje de propiedad distinto del de partners o tickets, y por eso la suite
# necesita sembrarlo aparte: un `idcliente` en la fila no serviria de nada.
CONDADO_A = 1   # ya contratado por el cliente 1 en el store raiz ("[1]")
CONDADO_B = 2   # se contrata abajo para el cliente 999
CALLE_A = 1     # -> ciudad 1 -> condado 1, ya en el store raiz
CALLE_B = 9902  # -> CIUDAD_B -> condado 2, se crean abajo
CIUDAD_B = 9902

#: El expediente de cliente exige `requiere_cerrado=True`: un accidente en
#: cualquier otro estado devuelve 404 aunque el condado sea correcto, y la prueba
#: no llegaria a ejercitar la tenencia (T080).
ESTADO_CERRADO = 6

ACCIDENTE_A = "ACC-TENANT-A"
ACCIDENTE_B = "ACC-TENANT-B"


def _fila(**campos: Any) -> dict[str, Any]:
    campos.setdefault("fecha_actualizacion", AHORA)
    campos.setdefault("activo", True)
    return campos


def sembrar(store: dict[str, list[dict]]) -> None:
    """Anade a `PINOT_STORE` los recursos de ambos tenants.

    Se llama despues del reset autouse de `conftest.py`, que deja el store en su
    estado inicial. Solo **anade**: no toca las filas existentes, para no alterar
    las expectativas de las ~4.100 pruebas que ya dependen de ellas.
    """
    _cliente_ajeno(store)
    _usuarios(store)
    _partners(store)
    _soporte(store)
    _suscripciones(store)
    _ventas(store)
    _accidentes(store)
    _despacho(store)
    _red_operativa(store)


def _añadir(store: dict[str, list[dict]], tabla: str, filas: list[dict]) -> None:
    store.setdefault(tabla, []).extend(filas)


def _cliente_ajeno(store) -> None:
    _añadir(store, "Dim_Cliente", [
        _fila(
            idcliente=TENANT_B,
            nombre="Cliente Ajeno",
            razon_social="Cliente Ajeno S.A.",
            tipo="Proveedor",
            nit_identificacion="9999999999",
            logo_url=None,
            admin_local_id=USUARIO_B,
            estado="Aprobado",
        )
    ])


def _preferencias(store) -> None:
    """El cliente ajeno contrata el condado B. Sin esto no «posee» ningun accidente."""
    _añadir(store, "Dim_Preferencias_Cliente", [
        _fila(
            id_preferencia=TENANT_B,
            id_cliente=TENANT_B,
            umbrales_alerta="{}",
            canales_notificacion="email",
            telefono_sms=None,
            zonas_geograficas=f"[{CONDADO_B}]",
            destinatarios_reportes="ajeno@tenantb.com",
            frecuencia_reportes="semanal",
            formato_reportes="PDF",
        )
    ])


def _accidentes(store) -> None:
    """Un accidente por condado, para que cada cliente «posea» uno.

    El del tenant B esta en el condado 2, que el cliente 1 **no** tiene
    contratado: si aparece en una respuesta del cliente 1, es una fuga.
    """
    # La cadena completa importa: `resolve_condado_from_idcalle` va
    # calle -> ciudad -> condado. Colgar la calle ajena de la ciudad 1 la habria
    # dejado en el condado del tenant A, y el accidente «ajeno» habria sido
    # legitimamente visible — una prueba que aprueba por estar mal montada.
    _añadir(store, "Dim_Ciudad", [
        _fila(idciudad=CIUDAD_B, idcondado=CONDADO_B, nombre="Ciudad Ajena",
              ciudad="Ciudad Ajena")
    ])
    _añadir(store, "Dim_Calle", [
        _fila(idcalle=CALLE_B, idciudad=CIUDAD_B, nombre="Calle Ajena",
              calle="Calle Ajena")
    ])
    _añadir(store, "Fact_Accidente", [
        _fila(idaccidente=ACCIDENTE_A, latitudinicio=19.4326, longitudinicio=-99.1332,
              fechahoraaccidente=TS, idseveridad=2, descripcion="Accidente propio",
              idcalle=CALLE_A, idusuario=USUARIO_A, numvehiculos=1),
        _fila(idaccidente=ACCIDENTE_B, latitudinicio=20.0, longitudinicio=-100.0,
              fechahoraaccidente=TS, idseveridad=2, descripcion="Accidente ajeno",
              idcalle=CALLE_B, idusuario=USUARIO_B, numvehiculos=1),
    ])
    # CERRADO, no REPORTADO: el expediente de cliente pasa `requiere_cerrado=True`,
    # asi que con cualquier otro estado la ruta responde 404 y la prueba no llega
    # a ejercitar la tenencia — aprobaria sin haber comprobado nada (T080).
    _añadir(store, "Fact_AccidenteTipoEstadoAccidente", [
        _fila(idaccidente=ACCIDENTE_A, idtipoestadoincidente=ESTADO_CERRADO,
              fechahoramodificado=TS, idusuario=USUARIO_A),
        _fila(idaccidente=ACCIDENTE_B, idtipoestadoincidente=ESTADO_CERRADO,
              fechahoramodificado=TS, idusuario=USUARIO_B),
    ])


def _despacho(store) -> None:
    _añadir(store, "Fact_Despacho", [
        _fila(iddespacho=1, idaccidente=ACCIDENTE_A, idunidademergencia=1,
              fechahoradespacho=TS),
        _fila(iddespacho=TENANT_B, idaccidente=ACCIDENTE_B, idunidademergencia=TENANT_B,
              fechahoradespacho=TS),
    ])
    _añadir(store, "Fact_NotificacionDespacho", [
        # `idaccidente` no es opcional: el doble de Pinot filtra por el y una fila
        # sin el campo revienta la consulta del expediente.
        _fila(idnotificaciondespacho=1, iddespacho=1, idunidademergencia=1,
              idaccidente=ACCIDENTE_A, idunidaddemergencia=1),
        _fila(idnotificaciondespacho=TENANT_B, iddespacho=TENANT_B,
              idunidademergencia=TENANT_B, idaccidente=ACCIDENTE_B,
              idunidaddemergencia=TENANT_B),
    ])


def _red_operativa(store) -> None:
    _añadir(store, "Dim_RegionOperativa", [
        _fila(idregionoperativa=TENANT_B, idestado=99, estadoregion="Producción",
              nombreregion="Region Ajena")
    ])
    _añadir(store, "Dim_UnidadEmergencia", [
        _fila(idunidademergencia=TENANT_B, idusuario=USUARIO_B,
              unidademergencia="Unidad Ajena", idtipounidad=1, idcondado=CONDADO_B,
              latitud=20.0, longitud=-100.0)
    ])


def _usuarios(store) -> None:
    _añadir(store, "Dim_Usuarios", [
        _fila(
            idusuario=USUARIO_B,
            nombres="Ajeno",
            apellidos="Tenant B",
            gmail="ajeno@tenantb.com",
            identificacion="9999999999",
            genero="M",
            telefono="3000000000",
            fechanacimiento="1990-01-01",
        )
    ])
    _añadir(store, "Dim_Usuario_Cliente", [
        _fila(idusuario=USUARIO_B, idcliente=TENANT_B)
    ])
    _preferencias(store)


def _partners(store) -> None:
    """Un partner por tenant. Sin esto, ni siquiera el actor legitimo entra."""
    _añadir(store, "Dim_Partner", [
        _fila(idpartner=1, idcliente=TENANT_A, nombrepartner="Partner Propio",
              planapi="Basico", limitellamadasminuto=100),
        _fila(idpartner=TENANT_B, idcliente=TENANT_B, nombrepartner="Partner Ajeno",
              planapi="Basico", limitellamadasminuto=100),
    ])
    _añadir(store, "Dim_CredencialAPI", [
        _fila(idcredencial=1, idpartner=1, entorno="Sandbox", client_id="1.1"),
        _fila(idcredencial=TENANT_B, idpartner=TENANT_B, entorno="Sandbox",
              client_id=f"{TENANT_B}.{TENANT_B}"),
    ])


def _soporte(store) -> None:
    _añadir(store, "Fact_Reclamo", [
        _fila(id_reclamo=1, idcliente=TENANT_A, idusuario=USUARIO_A,
              asunto="Ticket propio", id_estado=1),
        _fila(id_reclamo=TENANT_B, idcliente=TENANT_B, idusuario=USUARIO_B,
              asunto="Ticket ajeno", id_estado=1),
    ])


def _suscripciones(store) -> None:
    _añadir(store, "Fact_Factura", [
        _fila(id_factura="F-0001", idcliente=TENANT_A, total=100.0, estado="Pagada"),
        _fila(id_factura="F-9999", idcliente=TENANT_B, total=100.0, estado="Pagada"),
    ])


def _ventas(store) -> None:
    _añadir(store, "Dim_Prospecto", [
        _fila(idprospecto=1, idcliente=TENANT_A, nombre="Prospecto propio"),
        _fila(idprospecto=TENANT_B, idcliente=TENANT_B, nombre="Prospecto ajeno"),
    ])
