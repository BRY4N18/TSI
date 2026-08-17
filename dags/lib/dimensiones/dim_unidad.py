"""`dim_unidad`: una fila por **versión** de unidad, no por unidad.

Es la dimensión que justifica el modelo entero. El origen guarda el proveedor
actual de cada unidad y **nada historiza su cambio**: si mañana la unidad 7 pasa
del proveedor A al B, todo informe de rendimiento por proveedor reatribuye al B
los seis meses de trabajo del A — y la cifra parece correcta.

Aquí, cada despacho apunta a la **versión** vigente cuando ocurrió, así que
conserva su proveedor pase lo que pase después.

Lo que este módulo NO puede arreglar ⚠️
---------------------------------------
**El pasado anterior a la primera carga.** Nadie guardó a qué proveedor
pertenecía una unidad hace seis meses; ese dato no existe. Por eso todas las
versiones iniciales llevan `inicio_es_real = 0`: el modelo no arregla el pasado,
**impide que se siga rompiendo** desde hoy, y lo declara en vez de fingir que lo
sabe (research D2, T033).

Capacidad, una trampa del origen
--------------------------------
`Dim_UnidadEmergencia.capacidad` es **texto** en el origen, no número. Se
convierte aquí, y lo que no sea convertible queda ausente en vez de cero: una
unidad con capacidad "N/A" no tiene capacidad cero, tiene capacidad desconocida,
y un promedio que las confunda queda arrastrado hacia abajo.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Iterable, Mapping

from lib.dimensiones.desconocido import ETIQUETA_DESCONOCIDA, ID_DESCONOCIDO
from lib.dimensiones.versionado import ATRIBUTOS_VERSIONADOS_UNIDAD, versionar_lote
from lib.clickhouse_http_client import query_clickhouse
from lib.pinot_http_client import query_pinot

LIMITE = 100_000

CONSULTA_UNIDADES = f"""
    SELECT idunidademergencia, unidademergencia, placa, tipounidademergencia,
           capacidad, idcliente, idcondado, zonacobertura, fecha_creacion
    FROM Dim_UnidadEmergencia
    LIMIT {LIMITE}
"""

CONSULTA_CLIENTES = f"SELECT idcliente, nombre, razon_social FROM Dim_Cliente LIMIT {LIMITE}"

CONSULTA_CONDADOS = f"SELECT idcondado, condado FROM Dim_Condado LIMIT {LIMITE}"

#: Red Operativa (US1). El **primer acceso** de una unidad: la primera vez que
#: se conecto de verdad, no la fecha en que se le creo el usuario.
#:
#: ⚠️ La distincion es el informe entero. «Pendientes de primer acceso» busca
#: unidades dadas de alta que **nunca llegaron a operar**, y confundir el alta
#: del usuario con su primer uso las haria desaparecer justo a todas: todas
#: tienen usuario desde el dia que se crearon.
#: ⚠️ El primer acceso **se deriva del estado de la credencial**, porque el
#: origen no guarda ninguna fecha de primer acceso.
#:
#: * `Activo` — la credencial esta en uso: la unidad entro.
#: * `Cambio contrasena` — se le exige cambiarla, es decir **todavia no entro de
#:   verdad**. Es el estado con el que nace una credencial recien creada.
#: * Sin credencial — nunca se le dio uno.
#:
#: Es una derivacion, no una medicion, y tiene un limite conocido: una unidad que
#: entro y luego pidio cambio de contrasena vuelve a contar como pendiente. Con
#: los datos de hoy son 2 de 31 credenciales. Se documenta en vez de disimularse
#: porque el informe se usa para perseguir altas que nunca arrancaron, y una
#: unidad que si arranco apareciendo en esa lista cuesta una llamada, no una
#: decision equivocada.
CONSULTA_CREDENCIALES = f"""
    SELECT idusuario, estadocredencial
    FROM Dim_Credencial
    LIMIT {LIMITE}
"""

#: Estado de credencial que significa «ya entro».
CREDENCIAL_EN_USO = "Activo"

#: La unidad y su usuario. `Dim_UnidadEmergencia.idusuario` los relaciona, y
#: **no se copia al modelo**: se usa aqui para resolver el primer acceso y se
#: descarta. Saber si una unidad opero no requiere saber quien la opera.
CONSULTA_UNIDAD_USUARIO = f"""
    SELECT idunidademergencia, idusuario
    FROM Dim_UnidadEmergencia
    LIMIT {LIMITE}
"""

#: Las versiones vigentes ya cargadas. `FINAL` es obligatorio: sin él, una
#: unidad con dos versiones a medio fusionar devolvería ambas como vigentes y el
#: versionado compararía contra la equivocada.
CONSULTA_VIGENTES = """
    SELECT * FROM dim_unidad FINAL WHERE es_vigente = 1
"""


def _a_entero(valor: Any) -> int | None:
    """Capacidad textual → número, o ausente. **Nunca cero.**"""
    try:
        return int(str(valor).strip())
    except (TypeError, ValueError):
        return None


def extraer(
    consultar_origen: Callable[[str], list[dict]] = query_pinot,
    consultar_modelo: Callable[[str], list[dict]] = query_clickhouse,
) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    return (
        consultar_origen(CONSULTA_UNIDADES),
        consultar_origen(CONSULTA_CLIENTES),
        consultar_origen(CONSULTA_CONDADOS),
        consultar_modelo(CONSULTA_VIGENTES),
        consultar_origen(CONSULTA_CREDENCIALES),
        consultar_origen(CONSULTA_UNIDAD_USUARIO),
    )


def aplanar(
    unidades: Iterable[Mapping[str, Any]],
    clientes: Iterable[Mapping[str, Any]],
    condados: Iterable[Mapping[str, Any]],
    credenciales: Iterable[Mapping[str, Any]] = (),
    unidad_usuario: Iterable[Mapping[str, Any]] = (),
) -> list[dict]:
    """Fila del origen → fila candidata a versión, con proveedor y condado por nombre."""
    por_cliente = {c["idcliente"]: c for c in clientes}
    por_condado = {c["idcondado"]: c for c in condados}
    estado_credencial = {c["idusuario"]: c.get("estadocredencial") for c in credenciales}
    usuario_de_unidad = {
        u["idunidademergencia"]: u.get("idusuario") for u in unidad_usuario
    }

    filas = []
    for u in unidades:
        cliente = por_cliente.get(u.get("idcliente"), {})
        condado = por_condado.get(u.get("idcondado"), {})
        filas.append(
            {
                "idunidademergencia": u["idunidademergencia"],
                "placa": u.get("placa") or ETIQUETA_DESCONOCIDA,
                "nombre_unidad": u.get("unidademergencia"),
                "tipo_unidad": u.get("tipounidademergencia"),
                "capacidad": _a_entero(u.get("capacidad")),
                "idcliente": u.get("idcliente") if u.get("idcliente") is not None else ID_DESCONOCIDO,
                "proveedor": cliente.get("nombre")
                or cliente.get("razon_social")
                or ETIQUETA_DESCONOCIDA,
                "idcondado": u.get("idcondado"),
                "condado": condado.get("condado"),
                "zona_cobertura": u.get("zonacobertura"),
                # Red Operativa (US1). Ninguno de los dos abre version.
                "fecha_alta": _fecha(u.get("fecha_creacion")),
                "tuvo_primer_acceso": 1
                if estado_credencial.get(usuario_de_unidad.get(u["idunidademergencia"]))
                == CREDENCIAL_EN_USO
                else 0,
            }
        )
    return filas


def _fecha(epoch_ms: Any) -> str | None:
    """Epoch-ms del origen → texto. **Ausente sigue ausente**, no epoca cero.

    Una unidad sin fecha de alta con `1970-01-01` tendria cincuenta y seis anos
    de antiguedad, y el informe de rotacion la contaria como la mas veterana de
    la flota.
    """
    from datetime import datetime, timezone

    if epoch_ms in (None, 0):
        return None
    try:
        valor = int(epoch_ms)
    except (TypeError, ValueError):
        return None
    if valor <= 0:
        return None
    return datetime.fromtimestamp(valor / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _serializar(fila: dict) -> dict:
    """Fechas a texto para el almacén. `valido_hasta` ausente queda nulo, no época cero."""
    salida = dict(fila)
    for campo in ("valido_desde", "valido_hasta", "version"):
        valor = salida.get(campo)
        if isinstance(valor, datetime):
            salida[campo] = valor.strftime("%Y-%m-%d %H:%M:%S")
    return salida


def construir(
    unidades: Iterable[Mapping[str, Any]],
    clientes: Iterable[Mapping[str, Any]],
    condados: Iterable[Mapping[str, Any]],
    vigentes: Iterable[Mapping[str, Any]],
    ahora: datetime,
    credenciales: Iterable[Mapping[str, Any]] = (),
    unidad_usuario: Iterable[Mapping[str, Any]] = (),
) -> list[dict]:
    """Filas a escribir. **Vacía si ninguna unidad cambió**, que es lo normal."""
    por_clave = {v["idunidademergencia"]: v for v in vigentes}
    candidatas = aplanar(unidades, clientes, condados, credenciales, unidad_usuario)
    filas = versionar_lote(
        candidatas,
        por_clave,
        clave_negocio="idunidademergencia",
        atributos=ATRIBUTOS_VERSIONADOS_UNIDAD,
        ahora=ahora,
    )
    _verificar_sin_inicio_real(filas)
    filas.extend(_refrescar_no_versionados(candidatas, por_clave, filas, ahora))
    return [_serializar(f) for f in filas]


#: Atributos que **no abren versión** pero sí tienen que llegar al almacén.
#:
#: El alta no cambia y el primer acceso ocurre una vez: versionarlos llenaría la
#: dimensión de versiones nuevas sin que nada de negocio hubiera pasado.
ATRIBUTOS_NO_VERSIONADOS = ("fecha_alta", "tuvo_primer_acceso")


def _refrescar_no_versionados(candidatas, vigentes_por_clave, ya_escritas, ahora):
    """Reescribe la versión vigente con los atributos no versionados al día.

    ⚠️ **Sin esto, estas columnas no llegan nunca al almacén.** El versionado no
    escribe nada cuando ningún atributo versionado cambió —que es lo normal y lo
    correcto—, así que una unidad estable nunca vería actualizado su primer
    acceso. La columna existiría, estaría a cero para siempre, y el informe de
    pendientes de primer acceso diría que **ninguna unidad ha entrado nunca**.

    No abre versión: reescribe **la misma fila** —misma clave de negocio, mismo
    `valido_desde`, mismo `sk_unidad`— con un `version` mayor.
    `ReplacingMergeTree(version)` la sustituye. Cambiar `valido_desde` habría
    creado una fila nueva en vez de reemplazar, y la unidad habría acabado con
    dos versiones vigentes a la vez.

    Las unidades cuya versión sí cambió no entran aquí: su fila nueva ya trae los
    valores frescos, y reescribirlas ademas duplicaría la clave.
    """
    ya_versionadas = {f["idunidademergencia"] for f in ya_escritas}

    refrescadas = []
    for candidata in candidatas:
        clave = candidata["idunidademergencia"]
        if clave in ya_versionadas:
            continue
        vigente = vigentes_por_clave.get(clave)
        if vigente is None:
            continue
        if all(
            vigente.get(a) == candidata.get(a) for a in ATRIBUTOS_NO_VERSIONADOS
        ):
            # Nada que refrescar. No escribir es lo correcto: una reescritura por
            # corrida llenaría la tabla de versiones idénticas.
            continue

        fila = dict(vigente)
        fila.update({a: candidata.get(a) for a in ATRIBUTOS_NO_VERSIONADOS})
        fila["version"] = ahora
        refrescadas.append(fila)
    return refrescadas


def _verificar_sin_inicio_real(filas: Iterable[Mapping[str, Any]]) -> None:
    """Ninguna versión de unidad puede declarar un inicio real (T033, FR-021).

    Se comprueba aquí y no solo en una prueba porque es una afirmación **sobre el
    origen**, no sobre este código: nada historiza el cambio de unidad a
    proveedor. Si alguna vez el origen empezara a historizarlo, este error salta
    y obliga a decidir conscientemente —reconstruir el histórico— en vez de que
    la marca cambie de significado sin que nadie lo advierta.
    """
    mentirosas = [f for f in filas if f.get("inicio_es_real") == 1]
    if mentirosas:
        claves = sorted({f["idunidademergencia"] for f in mentirosas})
        raise ValueError(
            "versiones de unidad con inicio_es_real=1: el origen no historiza el "
            f"cambio de proveedor, así que esa fecha no puede ser real. Unidades: {claves}"
        )
