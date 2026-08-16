"""Datos sembrados para los informes tácticos de Red Operativa.

**`dos_flotas` es el fixture del que depende que este módulo esté probado.** Con
una sola flota poblada, filtrar por proveedor y no filtrar devuelven lo mismo, y
toda prueba de acotamiento pasa aunque el acotamiento no exista.

Los otros casos sembrados protegen defectos concretos:

* una unidad **dada de alta pero `Fuera de servicio`** — es la que demuestra que
  `activo` significa «existe», no «puede acudir». Su estado operativo vive en el
  histórico, que este módulo **no lee** a propósito (research D2);
* una unidad **sin condado**, que debe aparecer con la ubicación ausente en vez
  de omitirse (FR-023);
* una baja **forzada con su caso afectado** y una **normal**, que son un
  incidente operativo y una salida ordenada, no dos filas del mismo tipo;
* una región **`En_Alerta`** y otra **`Despublicada`**: la primera **sigue
  operando** con cobertura degradada, y agruparlas ocultaría la ventana en la
  que OT13 puede actuar;
* **dos rechazos** sobre la misma región, porque el segundo no sustituye al
  primero.

`latitud`, `longitud` y `contactoproveedor` se siembran con valores reconocibles:
si aparecen en una respuesta, la prueba de research D6 debe fallar.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from conftest import PINOT_STORE
from core.jwt_utils import create_access_token
from core.repositories.red_operativa.informes_baja_repository import (
    TIPO_BAJA_FORZADA,
    TIPO_BAJA_NORMAL,
)
from core.repositories.red_operativa.informes_region_repository import (
    ESTADO_DESPUBLICADA,
    ESTADO_EN_ALERTA,
    ESTADO_EN_VALIDACION,
    ESTADO_PRODUCCION,
)

#: Instante fijo: 2026-08-11T12:00:00Z.
AHORA = datetime(2026, 8, 11, 12, 0, 0, tzinfo=timezone.utc)
AHORA_MS = int(AHORA.timestamp() * 1000)
DIA_MS = 86_400_000

PROVEEDOR_A = 5501
PROVEEDOR_B = 5502
ADMIN_A = 5601  # administrador local del proveedor A
ADMIN_B = 5602
EMPLEADO_A = 5603  # vinculado a A pero NO su administrador local

CONDADO = 5701
ESTADO_GEO = 5801
REGION_PROD = 5901
REGION_ALERTA = 5902
REGION_DESPUBLICADA = 5903
REGION_VALIDACION = 5904

#: Valores que jamás pueden aparecer en una respuesta.
POSICION_PROHIBIDA = -99.12345
CONTACTO_PROHIBIDO = "NO-DEBE-SALIR-0999888777"


@pytest.fixture
def reloj_fijo():
    return lambda: AHORA_MS


@pytest.fixture
def geografia_y_proveedores(mock_pinot):
    PINOT_STORE["Dim_Estado"].append(
        {"idestado": ESTADO_GEO, "estado": "Provincia Norte", "idpais": 1,
         "activo": True, "fecha_actualizacion": AHORA_MS}
    )
    PINOT_STORE["Dim_Condado"].append(
        {"idcondado": CONDADO, "condado": "Canton Central", "idestado": ESTADO_GEO,
         "activo": True, "fecha_actualizacion": AHORA_MS}
    )
    PINOT_STORE["Dim_Usuarios"].extend(
        [
            {"idusuario": ADMIN_A, "nombres": "Rosa", "apellidos": "Delgado",
             "gmail": "rosa.delgado@tsi.com", "activo": True, "fecha_actualizacion": AHORA_MS},
            {"idusuario": ADMIN_B, "nombres": "Hugo", "apellidos": "Ponce",
             "gmail": "hugo.ponce@tsi.com", "activo": True, "fecha_actualizacion": AHORA_MS},
            {"idusuario": EMPLEADO_A, "nombres": "Empleado", "apellidos": "Vinculado",
             "gmail": "empleado@tsi.com", "activo": True, "fecha_actualizacion": AHORA_MS},
        ]
    )
    PINOT_STORE["Dim_Cliente"].extend(
        [
            {"idcliente": PROVEEDOR_A, "razon_social": "Gruas Delgado S.A.",
             "tipo": "Proveedor", "estado": "Activo", "admin_local_id": ADMIN_A,
             "fecha_creacion": AHORA_MS, "fecha_actualizacion": AHORA_MS},
            {"idcliente": PROVEEDOR_B, "razon_social": "Rescate Ponce Ltda.",
             "tipo": "Proveedor", "estado": "Activo", "admin_local_id": ADMIN_B,
             "fecha_creacion": AHORA_MS, "fecha_actualizacion": AHORA_MS},
        ]
    )
    # El empleado pertenece a A por vínculo, pero no es su administrador local:
    # es el caso que distingue los dos criterios de pertenencia.
    PINOT_STORE["Dim_Usuario_Cliente"].append(
        {"idusuario": EMPLEADO_A, "idcliente": PROVEEDOR_A, "activo": True,
         "fecha_actualizacion": AHORA_MS}
    )


def _unidad(uid, *, placa, idcliente, activo=True, idcondado=CONDADO, tipo="Grua"):
    return {
        "idunidademergencia": uid,
        "idusuario": ADMIN_A,
        "idcliente": idcliente,
        "tipopropiedad": "Propia",
        "placa": placa,
        "capacidad": "2",
        "idcondado": idcondado,
        "zonacobertura": "Centro",
        # Dato personal: no puede salir.
        "contactoproveedor": CONTACTO_PROHIBIDO,
        "unidademergencia": f"Unidad {placa}",
        "tipounidademergencia": tipo,
        "activo": activo,
        # Última posición conocida: dato sensible, no puede salir.
        "latitud": POSICION_PROHIBIDA,
        "longitud": POSICION_PROHIBIDA,
        "fecha_creacion": AHORA_MS,
        "fecha_actualizacion": AHORA_MS,
    }


@pytest.fixture
def dos_flotas(mock_pinot, geografia_y_proveedores):
    """Dos proveedores con flota a la vez — el fixture que hace reales las pruebas.

    Tamaños distintos a propósito (A tiene 3, B tiene 1), para que un conteo
    pueda distinguir «acotado» de «sin acotar».

    La unidad `FUERA-01` está **dada de alta** (`activo = true`) y su estado
    operativo es `Fuera de servicio` — pero eso vive en el histórico, que este
    módulo no lee. Es exactamente el caso que demuestra que alta ≠ disponible.
    """
    PINOT_STORE["Dim_UnidadEmergencia"].extend(
        [
            _unidad(5001, placa="GRUA-01", idcliente=PROVEEDOR_A),
            # De alta, pero fuera de servicio en el histórico.
            _unidad(5002, placa="FUERA-01", idcliente=PROVEEDOR_A),
            # Dada de baja: existe pero ya no forma parte de la flota activa.
            _unidad(5003, placa="BAJA-01", idcliente=PROVEEDOR_A, activo=False),
            _unidad(5004, placa="AJENA-01", idcliente=PROVEEDOR_B, tipo="Ambulancia"),
        ]
    )
    # Su estado operativo vive **solo** aquí, y este módulo no lo lee.
    PINOT_STORE["Fact_HistorialEstadoUnidad"].append(
        {
            "idhistorialestadounidad": 5901,
            "idunidademergencia": 5002,
            "idestadounidademergencia": 4,  # Fuera de servicio
            "fechahora": AHORA_MS - DIA_MS,
            "fecha_actualizacion": AHORA_MS - DIA_MS,
        }
    )


@pytest.fixture
def unidad_sin_condado(mock_pinot, geografia_y_proveedores):
    """Sin condado no puede ser candidata en un despacho: hay que verla (FR-023)."""
    PINOT_STORE["Dim_UnidadEmergencia"].append(
        _unidad(5010, placa="SINCOND-01", idcliente=PROVEEDOR_A, idcondado=None)
    )


@pytest.fixture
def bajas_sembradas(mock_pinot, dos_flotas):
    """Una baja **forzada con su caso** y una **normal**, más una de otro proveedor."""
    PINOT_STORE["Fact_BajaUnidad"].extend(
        [
            {
                "idbajaunidad": 5101, "idunidademergencia": 5003,
                "idusuario": ADMIN_A, "idaccidente": None,
                "motivo": "fin de vida util", "tipobaja": TIPO_BAJA_NORMAL,
                "fechahora": AHORA_MS - 10 * DIA_MS,
                "fecha_actualizacion": AHORA_MS - 10 * DIA_MS,
            },
            {
                # La unidad atendía un caso: hubo que reasignar.
                "idbajaunidad": 5102, "idunidademergencia": 5001,
                "idusuario": ADMIN_A, "idaccidente": "ACC-2026-000123",
                "motivo": "averia en ruta", "tipobaja": TIPO_BAJA_FORZADA,
                "fechahora": AHORA_MS - 3 * DIA_MS,
                "fecha_actualizacion": AHORA_MS - 3 * DIA_MS,
            },
            {
                "idbajaunidad": 5103, "idunidademergencia": 5004,
                "idusuario": ADMIN_B, "idaccidente": None,
                "motivo": "venta", "tipobaja": TIPO_BAJA_NORMAL,
                "fechahora": AHORA_MS - DIA_MS,
                "fecha_actualizacion": AHORA_MS - DIA_MS,
            },
        ]
    )


@pytest.fixture
def regiones_sembradas(mock_pinot, geografia_y_proveedores):
    """Los cuatro estados que importan, incluidos los dos que se confunden."""
    PINOT_STORE["Dim_RegionOperativa"].extend(
        [
            {"idregionoperativa": REGION_PROD, "idestado": ESTADO_GEO,
             "nombreregion": "Norte Operativa", "estadoregion": ESTADO_PRODUCCION,
             "activo": True, "fecha_actualizacion": AHORA_MS - 2 * DIA_MS},
            # **Sigue operando**, con cobertura degradada.
            {"idregionoperativa": REGION_ALERTA, "idestado": ESTADO_GEO,
             "nombreregion": "Centro Alerta", "estadoregion": ESTADO_EN_ALERTA,
             "activo": True, "fecha_actualizacion": AHORA_MS - 5 * DIA_MS},
            # Ya no opera.
            {"idregionoperativa": REGION_DESPUBLICADA, "idestado": ESTADO_GEO,
             "nombreregion": "Sur Retirada", "estadoregion": ESTADO_DESPUBLICADA,
             "activo": False, "fecha_actualizacion": AHORA_MS - 30 * DIA_MS},
            # Detenida en validación desde hace mucho: el caso de OT13.
            {"idregionoperativa": REGION_VALIDACION, "idestado": ESTADO_GEO,
             "nombreregion": "Este Pendiente", "estadoregion": ESTADO_EN_VALIDACION,
             "activo": True, "fecha_actualizacion": AHORA_MS - 60 * DIA_MS},
        ]
    )


@pytest.fixture
def validaciones_sembradas(mock_pinot, regiones_sembradas):
    """**Dos rechazos** sobre la misma región: el segundo no sustituye al primero."""
    PINOT_STORE["Dim_ValidacionRegion"].extend(
        [
            {"idvalidacionregion": 5201, "idregionoperativa": REGION_VALIDACION,
             "idusuario": ADMIN_A, "resultado": "Rechazada",
             "motivo": "cobertura insuficiente",
             "fechahora": AHORA_MS - 50 * DIA_MS,
             "fecha_actualizacion": AHORA_MS - 50 * DIA_MS},
            {"idvalidacionregion": 5202, "idregionoperativa": REGION_VALIDACION,
             "idusuario": ADMIN_A, "resultado": "Rechazada",
             "motivo": "sin proveedor asignado",
             "fechahora": AHORA_MS - 20 * DIA_MS,
             "fecha_actualizacion": AHORA_MS - 20 * DIA_MS},
            {"idvalidacionregion": 5203, "idregionoperativa": REGION_PROD,
             "idusuario": ADMIN_A, "resultado": "Aprobada", "motivo": None,
             "fechahora": AHORA_MS - 40 * DIA_MS,
             "fecha_actualizacion": AHORA_MS - 40 * DIA_MS},
        ]
    )


@pytest.fixture
def todo_sembrado(dos_flotas, bajas_sembradas, validaciones_sembradas):
    return True


def _headers(user_id: int, roles: list[str]) -> dict:
    token = create_access_token(user_id=user_id, roles=roles, session_id=1)
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


@pytest.fixture
def proveedor_a_headers(mock_pinot, mock_kafka):
    return _headers(ADMIN_A, ["Proveedor"])


@pytest.fixture
def proveedor_b_headers(mock_pinot, mock_kafka):
    return _headers(ADMIN_B, ["Proveedor"])


@pytest.fixture
def empleado_a_headers(mock_pinot, mock_kafka):
    """Vinculado al proveedor A pero **no** su administrador local.

    Con el criterio estricto de este módulo recibe `403` — igual que en la
    pantalla operativa de alta de unidades.
    """
    return _headers(EMPLEADO_A, ["Proveedor"])


@pytest.fixture
def director_tecnologico_headers(mock_pinot, mock_kafka):
    return _headers(5610, ["DirectorTecnologico"])


@pytest.fixture
def director_expansion_headers(mock_pinot, mock_kafka):
    return _headers(5611, ["DirectorExpansion"])
