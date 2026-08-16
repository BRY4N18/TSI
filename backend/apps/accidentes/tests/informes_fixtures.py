"""Datos sembrados para los informes tácticos de Emergencias.

Se importa desde `conftest.py`, que ya existe con la siembra del módulo
operativo y **no se toca**.

**`dos_condados` es el fixture del que depende que este módulo esté probado.**
Con casos en un solo condado, el acotamiento por zona contratada pasa aunque no
exista: filtrar y no filtrar devuelven lo mismo.

Los demás casos protegen defectos concretos:

* un caso **cerrado**, uno **descartado por falsa alarma** y uno **fusionado**
  como duplicado — las tres formas de quedar inactivo, que un recuento sin
  distinguir sumaría como si fueran la misma cosa;
* un caso **abierto en la zona del cliente**, que el cliente **no** debe ver;
* un caso **sin ubicación resoluble**, que aparece con la ubicación ausente;
* un despacho **en tránsito** y otro con **retiro forzado**;
* evidencia **capturada sin conexión y sincronizada** frente a evidencia **en
  línea** — el contraste sin el cual no se distingue una implementación correcta
  de una que sella la hora de subida en los dos campos;
* un cierre **sin calificación** y otro **sin observaciones**;
* un **cliente sin zonas contratadas**, que debe obtener cero casos.

`latitudinicio` y `longitudinicio` se siembran con valores reconocibles: si
aparecen en una respuesta, la prueba de research D4 debe fallar.
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
MIN_MS = 60_000

ESTADO_GEO = 7100
CONDADO_CONTRATADO = 7201
CONDADO_AJENO = 7202
CIUDAD_CONTRATADA = 7301
CIUDAD_AJENA = 7302
CALLE_CONTRATADA = 7401
CALLE_AJENA = 7402

SEVERIDAD_ALTA = 7501
SEVERIDAD_LEVE = 7502
TIPO_REPORTADO = 7601

CUENTA_CLIENTE = 7701
CUENTA_SIN_ZONAS = 7702
USUARIO_CLIENTE = 7801
USUARIO_SIN_ZONAS = 7802
OPERADOR = 7803
TECNICO_CAMPO = 7804
DIRECTOR_OPERACIONES = 7805
PARTNER = 7806

UNIDAD = 7901
ORIGEN_AUTOMATICO = 7911
ORIGEN_MANUAL = 7912

CASO_CERRADO = "ACC-7000-CERRADO"
CASO_DESCARTADO = "ACC-7000-DESCARTADO"
CASO_FUSIONADO = "ACC-7000-FUSIONADO"
CASO_ABIERTO = "ACC-7000-ABIERTO"
CASO_AJENO = "ACC-7000-AJENO"
CASO_SIN_UBICACION = "ACC-7000-SINUBIC"

#: Valores que jamás pueden aparecer en una respuesta.
LAT_PROHIBIDA = -99.7654321
LON_PROHIBIDA = -98.1234567


@pytest.fixture
def reloj_fijo():
    return lambda: AHORA_MS


@pytest.fixture
def geografia_sembrada(mock_pinot):
    """Dos condados, cada uno con su ciudad y su calle.

    Es lo que hace real el acotamiento: sin el segundo condado, un cliente
    acotado y otro sin acotar obtienen exactamente lo mismo.
    """
    PINOT_STORE["Dim_Condado"].extend(
        [
            {"idcondado": CONDADO_CONTRATADO, "condado": "Valle Norte",
             "idestado": ESTADO_GEO, "activo": True, "fecha_actualizacion": AHORA_MS},
            {"idcondado": CONDADO_AJENO, "condado": "Sierra Sur",
             "idestado": ESTADO_GEO, "activo": True, "fecha_actualizacion": AHORA_MS},
        ]
    )
    PINOT_STORE["Dim_Ciudad"].extend(
        [
            {"idciudad": CIUDAD_CONTRATADA, "ciudad": "San Ramón",
             "idcondado": CONDADO_CONTRATADO, "activo": True,
             "fecha_actualizacion": AHORA_MS},
            {"idciudad": CIUDAD_AJENA, "ciudad": "Puerto Alto",
             "idcondado": CONDADO_AJENO, "activo": True,
             "fecha_actualizacion": AHORA_MS},
        ]
    )
    PINOT_STORE["Dim_Calle"].extend(
        [
            {"idcalle": CALLE_CONTRATADA, "calle": "Avenida Central",
             "idciudad": CIUDAD_CONTRATADA, "activo": True,
             "fecha_actualizacion": AHORA_MS},
            {"idcalle": CALLE_AJENA, "calle": "Ruta del Puerto",
             "idciudad": CIUDAD_AJENA, "activo": True,
             "fecha_actualizacion": AHORA_MS},
        ]
    )
    PINOT_STORE["Dim_Severidad"].extend(
        [
            {"idseveridad": SEVERIDAD_ALTA, "severidad": "Grave",
             "descripcion": "", "activo": True, "fecha_actualizacion": AHORA_MS},
            {"idseveridad": SEVERIDAD_LEVE, "severidad": "Leve",
             "descripcion": "", "activo": True, "fecha_actualizacion": AHORA_MS},
        ]
    )
    PINOT_STORE["Dim_TipoReportado"].append(
        {"idtiporeportado": TIPO_REPORTADO, "tiporeportado": "Colisión",
         "activo": True, "fecha_actualizacion": AHORA_MS}
    )
    PINOT_STORE["Dim_Usuarios"].extend(
        [
            {"idusuario": USUARIO_CLIENTE, "nombres": "Elena", "apellidos": "Ruiz",
             "gmail": "elena.ruiz@cliente.com", "activo": True,
             "fecha_actualizacion": AHORA_MS},
            {"idusuario": USUARIO_SIN_ZONAS, "nombres": "Tomás", "apellidos": "Vidal",
             "gmail": "tomas.vidal@cliente.com", "activo": True,
             "fecha_actualizacion": AHORA_MS},
            {"idusuario": TECNICO_CAMPO, "nombres": "Nadia", "apellidos": "Cortés",
             "gmail": "nadia.cortes@tsi.com", "activo": True,
             "fecha_actualizacion": AHORA_MS},
            {"idusuario": OPERADOR, "nombres": "Hugo", "apellidos": "Lemos",
             "gmail": "hugo.lemos@tsi.com", "activo": True,
             "fecha_actualizacion": AHORA_MS},
        ]
    )
    PINOT_STORE["Dim_Cliente"].extend(
        [
            {"idcliente": CUENTA_CLIENTE, "razon_social": "Aseguradora Ruiz S.A.",
             "tipo": "Corporativo", "estado": "Activo",
             "admin_local_id": USUARIO_CLIENTE,
             "fecha_creacion": AHORA_MS, "fecha_actualizacion": AHORA_MS},
            {"idcliente": CUENTA_SIN_ZONAS, "razon_social": "Vidal Sin Zonas S.A.",
             "tipo": "Corporativo", "estado": "Activo",
             "admin_local_id": USUARIO_SIN_ZONAS,
             "fecha_creacion": AHORA_MS, "fecha_actualizacion": AHORA_MS},
        ]
    )
    PINOT_STORE["Dim_Usuario_Cliente"].extend(
        [
            {"idusuario": USUARIO_CLIENTE, "idcliente": CUENTA_CLIENTE,
             "activo": True},
            {"idusuario": USUARIO_SIN_ZONAS, "idcliente": CUENTA_SIN_ZONAS,
             "activo": True},
        ]
    )
    PINOT_STORE["Dim_Preferencias_Cliente"].extend(
        [
            {"id_preferencia": 7951, "id_cliente": CUENTA_CLIENTE,
             "umbrales_alerta": "", "canales_notificacion": "correo",
             "telefono_sms": "", "zonas_geograficas": f"[{CONDADO_CONTRATADO}]",
             "destinatarios_reportes": "", "frecuencia_reportes": "mensual",
             "formato_reportes": "PDF", "activo": True,
             "fecha_actualizacion": AHORA_MS},
            # ⚠️ Sin zonas: **cero casos**, nunca el listado completo.
            {"id_preferencia": 7952, "id_cliente": CUENTA_SIN_ZONAS,
             "umbrales_alerta": "", "canales_notificacion": "",
             "telefono_sms": "", "zonas_geograficas": "[]",
             "destinatarios_reportes": "", "frecuencia_reportes": "",
             "formato_reportes": "", "activo": True,
             "fecha_actualizacion": AHORA_MS},
        ]
    )


def _caso(idaccidente, *, idcalle, activo, horafin="", origen="",
          idseveridad=SEVERIDAD_ALTA, hace_dias=1):
    return {
        "idaccidente": idaccidente,
        "idseveridad": idseveridad,
        "idcalle": idcalle,
        "idusuario": OPERADOR,
        "idtiporeportado": TIPO_REPORTADO,
        "idreferenciaestacion": 0,
        "idaccidenteorigen": origen,
        "horainicio": "08:00",
        "horafin": horafin,
        "descripcion": "Relato libre del reporte, que no sale en el listado",
        "codigopostal": "00000",
        "activo": activo,
        "duracionminutos": 45,
        "numvehiculos": 2,
        "numvictimas": 0,
        "numheridos": 1,
        "numfallecidos": 0,
        # ⛔ Nunca deben aparecer en una respuesta.
        "latitudinicio": LAT_PROHIBIDA,
        "longitudinicio": LON_PROHIBIDA,
        "distanciamillas": 0.0,
        "fechahoraaccidente": AHORA_MS - hace_dias * DIA_MS,
        "fecha_actualizacion": AHORA_MS,
    }


@pytest.fixture
def dos_condados(mock_pinot, geografia_sembrada):
    """Casos en el condado contratado y en el ajeno, en varias situaciones."""
    PINOT_STORE["Fact_Accidente"].extend(
        [
            # Cerrado: inactivo **con** hora de fin y sin caso origen.
            _caso(CASO_CERRADO, idcalle=CALLE_CONTRATADA, activo=False,
                  horafin="09:30", hace_dias=1),
            # ⚠️ Descartado: inactivo **sin** hora de fin ni caso origen.
            _caso(CASO_DESCARTADO, idcalle=CALLE_CONTRATADA, activo=False,
                  hace_dias=2),
            # ⚠️ Fusionado: inactivo **apuntando** a otro caso. No se borra.
            _caso(CASO_FUSIONADO, idcalle=CALLE_CONTRATADA, activo=False,
                  origen=CASO_CERRADO, hace_dias=3),
            # ⚠️ Abierto **en la zona del cliente**: el cliente NO debe verlo.
            _caso(CASO_ABIERTO, idcalle=CALLE_CONTRATADA, activo=True,
                  idseveridad=SEVERIDAD_LEVE, hace_dias=4),
            # Cerrado, pero en el condado ajeno.
            _caso(CASO_AJENO, idcalle=CALLE_AJENA, activo=False,
                  horafin="11:00", hace_dias=5),
            # ⚠️ Sin ubicación resoluble: aparece con la ubicación ausente y
            # **no se omite**. Nunca podrá acotarse a ninguna zona.
            _caso(CASO_SIN_UBICACION, idcalle=0, activo=False,
                  horafin="12:00", hace_dias=6),
        ]
    )


@pytest.fixture
def despachos_sembrados(mock_pinot, dos_condados):
    """Uno en tránsito, uno con retiro forzado y uno normal, dos sobre el mismo caso."""
    PINOT_STORE["Dim_UnidadEmergencia"].append(
        {"idunidademergencia": UNIDAD, "idusuario": TECNICO_CAMPO,
         "idcliente": CUENTA_CLIENTE, "tipopropiedad": "Propia",
         "placa": "AMB-001", "capacidad": "2", "idcondado": CONDADO_CONTRATADO,
         "zonacobertura": "", "contactoproveedor": "NO-DEBE-SALIR-555",
         "unidademergencia": "Ambulancia 01",
         "tipounidademergencia": "Ambulancia", "activo": True,
         "latitud": LAT_PROHIBIDA, "longitud": LON_PROHIBIDA,
         "fecha_creacion": AHORA_MS, "fecha_actualizacion": AHORA_MS}
    )
    PINOT_STORE["Dim_OrigenDespacho"].extend(
        [
            {"idorigendespacho": ORIGEN_AUTOMATICO,
             "origendespacho": "Asignación automática", "activo": True,
             "fecha_actualizacion": AHORA_MS},
            {"idorigendespacho": ORIGEN_MANUAL,
             "origendespacho": "Asignación manual", "activo": True,
             "fecha_actualizacion": AHORA_MS},
        ]
    )
    PINOT_STORE["Fact_Despacho"].extend(
        [
            # ⚠️ En tránsito: despachado, **sin llegada ni retiro**. `0` es el
            # centinela de «aún no ha ocurrido», no la época.
            {"iddespacho": 7961, "idaccidente": CASO_ABIERTO,
             "idunidademergencia": UNIDAD, "idnotificaciondespacho": 0,
             "idorigendespacho": ORIGEN_AUTOMATICO, "estado_unidad_previo": "Activa",
             "retiro_forzado": False, "activo": True,
             "fechahoradespacho": AHORA_MS - 30 * MIN_MS,
             "fechahorallegada": 0, "fechahoraretiro": 0,
             "fecha_actualizacion": AHORA_MS},
            # ⚠️ Retiro **forzado**: la central retiró a la unidad.
            {"iddespacho": 7962, "idaccidente": CASO_CERRADO,
             "idunidademergencia": UNIDAD, "idnotificaciondespacho": 0,
             "idorigendespacho": ORIGEN_AUTOMATICO, "estado_unidad_previo": "Activa",
             "retiro_forzado": True, "activo": True,
             "fechahoradespacho": AHORA_MS - DIA_MS,
             "fechahorallegada": AHORA_MS - DIA_MS + 15 * MIN_MS,
             "fechahoraretiro": AHORA_MS - DIA_MS + 40 * MIN_MS,
             "fecha_actualizacion": AHORA_MS},
            # Segundo intento sobre **el mismo caso**, de otro origen: conviven.
            {"iddespacho": 7963, "idaccidente": CASO_CERRADO,
             "idunidademergencia": UNIDAD, "idnotificaciondespacho": 0,
             "idorigendespacho": ORIGEN_MANUAL, "estado_unidad_previo": "Activa",
             "retiro_forzado": False, "activo": True,
             "fechahoradespacho": AHORA_MS - DIA_MS + 45 * MIN_MS,
             "fechahorallegada": AHORA_MS - DIA_MS + 60 * MIN_MS,
             "fechahoraretiro": AHORA_MS - DIA_MS + 90 * MIN_MS,
             "fecha_actualizacion": AHORA_MS},
        ]
    )


@pytest.fixture
def evidencia_sembrada(mock_pinot, dos_condados):
    """El contraste sin el cual la hora de captura no queda probada.

    Una evidencia **en línea** tiene las dos horas iguales; una capturada **sin
    conexión** las tiene distintas. Verificar solo la primera no distinguiría una
    implementación correcta de otra que sella la hora de subida en ambas.
    """
    captura_offline = AHORA_MS - 3 * DIA_MS
    subida_offline = captura_offline + 131_000  # 131 s después, como el caso real
    en_linea = AHORA_MS - DIA_MS

    PINOT_STORE["Dim_EvidenciaFoto"].extend(
        [
            # Capturada sin conexión y sincronizada después: **dos horas**.
            {"idevidenciafoto": 7971, "idaccidente": CASO_CERRADO,
             "idusuario": TECNICO_CAMPO, "sincronizado": True,
             "urlevidenciafoto": "https://tsi/ev/7971.jpg", "activo": True,
             "fechahora": captura_offline,
             "fecha_sincronizacion": subida_offline,
             "fecha_actualizacion": subida_offline},
            # Tomada en línea: las dos horas **coinciden**.
            {"idevidenciafoto": 7972, "idaccidente": CASO_CERRADO,
             "idusuario": TECNICO_CAMPO, "sincronizado": True,
             "urlevidenciafoto": "https://tsi/ev/7972.jpg", "activo": True,
             "fechahora": en_linea, "fecha_sincronizacion": en_linea,
             "fecha_actualizacion": en_linea},
            # ⚠️ Levantada y **nunca llegada**: es la que hay que recuperar.
            {"idevidenciafoto": 7973, "idaccidente": CASO_DESCARTADO,
             "idusuario": OPERADOR, "sincronizado": False,
             "urlevidenciafoto": "https://tsi/ev/7973.jpg", "activo": True,
             "fechahora": captura_offline, "fecha_sincronizacion": 0,
             "fecha_actualizacion": captura_offline},
        ]
    )
    PINOT_STORE["Dim_NotaAccidente"].extend(
        [
            # ⚠️ Sin conexión: `fecha_actualizacion` es la hora de subida.
            {"idnotaaccidentes": 7981, "idaccidente": CASO_CERRADO,
             "idusuario": TECNICO_CAMPO, "sincronizado": True,
             "nota": "Vía despejada al llegar", "tipo": "observacion",
             "activo": True, "fechahora": captura_offline,
             "fecha_actualizacion": subida_offline},
            # En línea: las dos coinciden.
            {"idnotaaccidentes": 7982, "idaccidente": CASO_CERRADO,
             "idusuario": OPERADOR, "sincronizado": True,
             "nota": "Confirmado por central", "tipo": "seguimiento",
             "activo": True, "fechahora": en_linea,
             "fecha_actualizacion": en_linea},
            {"idnotaaccidentes": 7983, "idaccidente": CASO_DESCARTADO,
             "idusuario": TECNICO_CAMPO, "sincronizado": False,
             "nota": "Sin incidencia en el punto", "tipo": "observacion",
             "activo": True, "fechahora": captura_offline,
             "fecha_actualizacion": captura_offline},
        ]
    )


@pytest.fixture
def cierres_sembrados(mock_pinot, dos_condados):
    """Uno completo, uno sin calificación y uno sin observaciones."""
    PINOT_STORE["Fact_CierreAccidente"].extend(
        [
            {"idaccidente": CASO_CERRADO, "resultado_atencion": "Atendido",
             "observaciones_finales": "Traslado al hospital regional",
             "calificacion": 5, "fecha_actualizacion": AHORA_MS},
            # ⚠️ Sin calificar. **Nunca debe presentarse como cero.**
            {"idaccidente": CASO_AJENO, "resultado_atencion": "Atendido",
             "observaciones_finales": "Sin novedad",
             "calificacion": 0, "fecha_actualizacion": AHORA_MS},
            # Sin observaciones: ausentes, no cadena vacía.
            {"idaccidente": CASO_SIN_UBICACION,
             "resultado_atencion": "Falsa alarma",
             "observaciones_finales": "", "calificacion": 3,
             "fecha_actualizacion": AHORA_MS},
        ]
    )


@pytest.fixture
def emergencias_sembradas(dos_condados, despachos_sembrados, evidencia_sembrada,
                          cierres_sembrados):
    return True


def _headers(user_id: int, roles: list[str]) -> dict:
    token = create_access_token(user_id=user_id, roles=roles, session_id=1)
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


@pytest.fixture
def operador_informes_headers(mock_pinot, mock_kafka):
    return _headers(OPERADOR, ["Operador"])


@pytest.fixture
def director_operaciones_headers(mock_pinot, mock_kafka):
    """Autoridad del departamento. ⚠️ Su exención es de **acotamiento**: no
    levanta la exclusión de coordenadas ni de identidad (FR-014b)."""
    return _headers(DIRECTOR_OPERACIONES, ["DirectorOperaciones"])


@pytest.fixture
def cliente_informes_headers(mock_pinot, mock_kafka):
    return _headers(USUARIO_CLIENTE, ["Cliente"])


@pytest.fixture
def cliente_sin_zonas_headers(mock_pinot, mock_kafka):
    return _headers(USUARIO_SIN_ZONAS, ["Cliente"])


@pytest.fixture
def partner_informes_headers(mock_pinot, mock_kafka):
    """El acceso programático a estos datos tiene su propio camino, con su
    alcance y su auditoría. Aquí recibe `403`."""
    return _headers(PARTNER, ["PartnerIntegracion"])
