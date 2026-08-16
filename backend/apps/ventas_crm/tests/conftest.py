"""Datos sembrados para los informes tácticos de Ventas y CRM.

**`dos_carteras` es el fixture del que depende que este módulo esté probado.**
Con una sola cartera poblada, filtrar por ejecutivo y no filtrar devuelven lo
mismo, así que toda prueba de acotamiento pasa aunque el acotamiento no exista.
Es el fallo más fácil de cometer aquí, y por eso los dos gerentes tienen cartera
a la vez y de tamaños distintos.

El otro fixture crítico es `demos_formato_mixto`: `demo_expiracion` es texto y el
sistema acepta tres formatos. Dos demos con la misma fecha y distinto sufijo
deben aparecer o desaparecer **juntas**; si solo sale una, una comparación de
texto se coló en la consulta y el listado miente sin dar ningún error.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from conftest import PINOT_STORE
from core.jwt_utils import create_access_token

#: Instante fijo para que las aserciones no dependan del reloj real.
#: 2026-08-11T12:00:00Z
AHORA = datetime(2026, 8, 11, 12, 0, 0, tzinfo=timezone.utc)
AHORA_MS = int(AHORA.timestamp() * 1000)
DIA_MS = 86_400_000

GERENTE_A = 8801  # cartera de 3
GERENTE_B = 8802  # cartera de 2
OTRO_USUARIO = 8803


@pytest.fixture
def reloj_fijo():
    return lambda: AHORA


@pytest.fixture
def reloj_congelado(monkeypatch):
    """Congela el reloj del servicio de nutrición para las pruebas de API.

    Las de servicio inyectan el instante por constructor, pero la vista
    construye el servicio ella misma, así que a nivel de API hay que sustituir
    el reloj por defecto. Sin esto las pruebas dependerían de la fecha real: los
    datos sembrados caducan solos y la suite empieza a fallar un día cualquiera
    sin que nadie haya tocado nada.
    """
    import apps.ventas_crm.services.informes_nutricion_service as modulo

    monkeypatch.setattr(modulo, "_ahora_utc", lambda: AHORA)
    return AHORA


@pytest.fixture
def gerentes_sembrados(mock_pinot):
    PINOT_STORE["Dim_Usuarios"].extend(
        [
            {
                "idusuario": GERENTE_A,
                "nombres": "Lucia",
                "apellidos": "Ramos",
                "gmail": "lucia.ramos@tsi.com",
                "activo": True,
                "fecha_actualizacion": AHORA_MS,
            },
            {
                "idusuario": GERENTE_B,
                "nombres": "Pablo",
                "apellidos": "Andrade",
                "gmail": "pablo.andrade@tsi.com",
                "activo": True,
                "fecha_actualizacion": AHORA_MS,
            },
        ]
    )


def _prospecto(pid, *, empresa, idusuario, activo=True, motivo=None, etapa="Contactado",
               canal="Web", tipo="Privado", expiracion=None):
    return {
        "idprospecto": pid,
        "nombres": "Contacto",
        "apellidos": empresa.split()[0],
        # Datos de contacto sembrados a propósito: si aparecen en la respuesta,
        # la prueba de research D4 debe fallar.
        "gmail": f"NO-DEBE-SALIR-{pid}@ejemplo.com",
        "telefono": "NO-DEBE-SALIR-0999",
        "empresa": empresa,
        "tipo_organizacion": tipo,
        "cargo": "Responsable",
        "como_nos_conocio": canal,
        "etapa_actual": etapa,
        "idusuario": idusuario,
        "demo_expiracion": expiracion,
        "activo": activo,
        "motivo_inactividad": motivo,
        "valor_estimado": 10000.0,
        "fecha_registro": AHORA_MS - 10 * DIA_MS,
        "fecha_actualizacion": AHORA_MS,
    }


@pytest.fixture
def dos_carteras(mock_pinot, gerentes_sembrados):
    """Dos gerentes con cartera a la vez — el fixture que hace reales las pruebas.

    El gerente A tiene 3 prospectos y el B tiene 2: los tamaños son distintos a
    propósito, para que un conteo pueda distinguir «acotado» de «sin acotar»
    incluso si ambos conjuntos fueran del mismo tamaño por casualidad.

    Incluye además, en la cartera de A, **un perdido y un convertido a la vez**:
    los dos tienen `activo = false`, y confundirlos presentaría los éxitos
    comerciales como fracasos (research D1).
    """
    PINOT_STORE["Dim_Prospecto"].extend(
        [
            _prospecto(8101, empresa="Alfa Seguros", idusuario=GERENTE_A,
                       etapa="Negociación", canal="Referido"),
            _prospecto(8102, empresa="Beta Logistica", idusuario=GERENTE_A,
                       activo=False, motivo="perdido", etapa="Perdido"),
            _prospecto(8103, empresa="Gamma Municipal", idusuario=GERENTE_A,
                       activo=False, motivo="convertido", etapa="Ganado",
                       tipo="Público"),
            _prospecto(8201, empresa="Delta Transportes", idusuario=GERENTE_B),
            _prospecto(8202, empresa="Epsilon Flotas", idusuario=GERENTE_B,
                       etapa="Propuesta"),
        ]
    )
    # El motivo de la pérdida vive en la transición del embudo, no en el
    # prospecto: sin esta fila el listado no puede explicar por qué se perdió.
    PINOT_STORE["Fact_Pipeline"].append(
        {
            "id_transicion": 8102,
            "id_prospecto": 8102,
            "etapa_anterior": "Contactado",
            "etapa_nueva": "Perdido",
            "notas": "",
            "motivo_perdida": "eligio a un competidor",
            "gerente_id": GERENTE_A,
            "fecha_transicion": AHORA_MS - DIA_MS,
            "fecha_actualizacion": AHORA_MS - DIA_MS,
        }
    )


@pytest.fixture
def prospecto_sin_ejecutivo(mock_pinot):
    """Un prospecto que nadie está trabajando — la anomalía que hay que ver.

    Ocultarlo escondería justo lo que la supervisión busca (research D7).
    """
    PINOT_STORE["Dim_Prospecto"].append(
        _prospecto(8300, empresa="Huerfana S.A.", idusuario=None)
    )


@pytest.fixture
def demos_formato_mixto(mock_pinot, gerentes_sembrados):
    """Las cinco expiraciones que la consulta debe tratar igual o distinguir.

    Las tres primeras son **el mismo instante** escrito de tres formas que el
    sistema acepta. Deben salir o no salir juntas.
    """
    en_tres_dias = AHORA + timedelta(days=3)
    expirada_hoy = AHORA.replace(hour=0, minute=1)

    PINOT_STORE["Dim_Prospecto"].extend(
        [
            _prospecto(8401, empresa="Demo Zeta", idusuario=GERENTE_A,
                       expiracion=en_tres_dias.strftime("%Y-%m-%dT%H:%M:%SZ")),
            _prospecto(8402, empresa="Demo Offset", idusuario=GERENTE_A,
                       expiracion=en_tres_dias.isoformat()),
            _prospecto(8403, empresa="Demo SinZona", idusuario=GERENTE_A,
                       expiracion=en_tres_dias.strftime("%Y-%m-%dT%H:%M:%S")),
            # Expirada hoy más temprano: el prefiltro por día la deja pasar y el
            # refinamiento en el servicio debe descartarla.
            _prospecto(8404, empresa="Demo Expirada", idusuario=GERENTE_A,
                       expiracion=expirada_hoy.strftime("%Y-%m-%dT%H:%M:%SZ")),
            # Sin fecha: no es una demo activa.
            _prospecto(8405, empresa="Demo SinFecha", idusuario=GERENTE_A,
                       expiracion=None),
            # De otro gerente, para que el acotamiento tenga qué excluir.
            _prospecto(8406, empresa="Demo Ajena", idusuario=GERENTE_B,
                       expiracion=en_tres_dias.strftime("%Y-%m-%dT%H:%M:%SZ")),
        ]
    )


@pytest.fixture
def asignaciones_sembradas(mock_pinot, dos_carteras):
    """Una primera asignación (sin responsable anterior) y dos reasignaciones."""
    PINOT_STORE["Fact_Asignacion"].extend(
        [
            {
                "idasignacion": 8501,
                "idprospecto": 8101,
                # La primera asignación no tiene responsable anterior: debe
                # presentarse como ausente, no como cero ni cadena vacía.
                "idusuariogerenteanterior": None,
                "idusuariogerenteactual": GERENTE_A,
                "tipoasignacion": "automatica",
                "motivo": None,
                "fechahoraasignacion": AHORA_MS - 10 * DIA_MS,
                "fecha_actualizacion": AHORA_MS - 10 * DIA_MS,
            },
            {
                "idasignacion": 8502,
                "idprospecto": 8201,
                "idusuariogerenteanterior": GERENTE_A,
                "idusuariogerenteactual": GERENTE_B,
                "tipoasignacion": "manual",
                "motivo": "reparto de cartera",
                "fechahoraasignacion": AHORA_MS - 5 * DIA_MS,
                "fecha_actualizacion": AHORA_MS - 5 * DIA_MS,
            },
            {
                "idasignacion": 8503,
                "idprospecto": 8202,
                "idusuariogerenteanterior": GERENTE_B,
                "idusuariogerenteactual": GERENTE_A,
                "tipoasignacion": "manual",
                "motivo": "baja temporal",
                "fechahoraasignacion": AHORA_MS - DIA_MS,
                "fecha_actualizacion": AHORA_MS - DIA_MS,
            },
        ]
    )


@pytest.fixture
def notificaciones_sembradas(mock_pinot, dos_carteras):
    """Notificaciones dirigidas a los dos gerentes, para acotar por destinatario."""
    PINOT_STORE["Fact_NotificacionVentas"].extend(
        [
            {
                "idnotificacion": 8601,
                "id_prospecto": 8101,
                "idinteraccion": None,
                "idusuariogerentenotificado": GERENTE_A,
                "regladisparada": "visita repetida a precios",
                "canal": "correo",
                # La columna existe y ningún proceso la escribe: devolverla sería
                # presentar como dato algo que siempre está vacío.
                "estado_envio": "NO-DEBE-SALIR",
                "fechahoranotificacion": AHORA_MS - 2 * DIA_MS,
                "fecha_actualizacion": AHORA_MS - 2 * DIA_MS,
            },
            {
                "idnotificacion": 8602,
                "id_prospecto": 8201,
                "idinteraccion": None,
                "idusuariogerentenotificado": GERENTE_B,
                "regladisparada": "descarga de ficha tecnica",
                "canal": "push",
                "estado_envio": "NO-DEBE-SALIR",
                "fechahoranotificacion": AHORA_MS - DIA_MS,
                "fecha_actualizacion": AHORA_MS - DIA_MS,
            },
        ]
    )


def _headers(user_id: int, roles: list[str]) -> dict:
    return {"HTTP_AUTHORIZATION": f"Bearer {create_access_token(user_id=user_id, roles=roles, session_id=1)}"}


@pytest.fixture
def gerente_a_headers(mock_pinot, mock_kafka):
    return _headers(GERENTE_A, ["GerenteVentas"])


@pytest.fixture
def gerente_b_headers(mock_pinot, mock_kafka):
    return _headers(GERENTE_B, ["GerenteCuentasPublicas"])


@pytest.fixture
def director_marketing_headers(mock_pinot, mock_kafka):
    """La autoridad departamental del §5.1: ve los cuatro sin acotamiento."""
    return _headers(OTRO_USUARIO, ["DirectorMarketing"])
