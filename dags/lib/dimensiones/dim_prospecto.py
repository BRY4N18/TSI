"""`dim_prospecto`: un prospecto del embudo comercial, **sin nombrarlo**.

⚠️ EL DESENLACE SE DERIVA, Y NUNCA DE `activo`
-----------------------------------------------
`Dim_Prospecto.activo` **no dice si el prospecto sigue en curso**: cubre a la vez
a los que se convirtieron y a los que se perdieron. Medido sobre los datos de
hoy: de los tres con `activo = false`, **dos son convertidos y uno perdido**.

Un informe que agrupara por esa columna juntaría el mejor desenlace posible con
el peor y devolvería «3 inactivos» — una cifra que no significa nada y que nadie
cuestionaría, porque suena a lo que se esperaba. Es el defecto que este módulo
existe para corregir (research D1).

`desenlace` tiene **tres** valores y sale de `motivo_inactividad` y
`etapa_actual`, que sí los distinguen.

⚠️ NINGÚN DATO PERSONAL ENTRA
------------------------------
El origen trae nombres, apellidos, correo, teléfono y cargo. La consulta **no los
pide**, y la tabla **no los tiene**. Las dos cosas: un dato que no se pide hoy
vuelve en cuanto alguien añada un `SELECT`; un dato que no está no puede volver
por descuido.

`idusuario` tampoco entra — quién gestiona el prospecto es identidad de persona,
y el acotamiento del ejecutivo comercial se resuelve en el permiso, no
publicando la columna.

Lo que sí entra es lo que hace analizable el embudo sin nombrar a nadie: empresa,
tipo de organización, canal, etapa y valor estimado.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Iterable, Mapping

from lib.dimensiones.desconocido import ETIQUETA_DESCONOCIDA, ID_DESCONOCIDO
from lib.pinot_http_client import query_pinot

LIMITE = 500_000

DESENLACE_CONVERTIDO = "convertido"
DESENLACE_PERDIDO = "perdido"
DESENLACE_EN_CURSO = "en_curso"

#: Etapas terminales del embudo. Se usan como **respaldo** cuando el motivo no
#: está registrado: un prospecto en `Ganado` se convirtió aunque nadie escribiera
#: el motivo.
ETAPA_GANADO = "Ganado"
ETAPA_PERDIDO = "Perdido"

#: ⚠️ Sin `nombres`, `apellidos`, `gmail`, `telefono`, `cargo` ni `idusuario`.
#: No se traen: no es que se descarten después.
CONSULTA_PROSPECTOS = f"""
    SELECT idprospecto, empresa, tipo_organizacion, como_nos_conocio,
           etapa_actual, motivo_inactividad, activo, valor_estimado, fecha_registro
    FROM Dim_Prospecto
    LIMIT {LIMITE}
"""


def extraer(consultar: Callable[[str], list[dict]] = query_pinot) -> list[dict]:
    return consultar(CONSULTA_PROSPECTOS)


def desenlace_de(prospecto: Mapping[str, Any]) -> str:
    """En qué acabó el prospecto: convertido, perdido o todavía en curso.

    ⚠️ **`activo` no participa en la decisión**, ni siquiera como respaldo. Es la
    columna que mezcla los dos desenlaces terminales, así que usarla para
    cualquier cosa reintroduciría el defecto por la puerta de atrás.

    El orden es deliberado: primero el motivo —que es lo que alguien declaró—,
    luego la etapa —que es donde quedó el prospecto—. Si ninguno dice nada, el
    prospecto sigue en curso: no hay evidencia de que terminara.
    """
    motivo = (prospecto.get("motivo_inactividad") or "").strip().lower()
    if motivo == DESENLACE_CONVERTIDO:
        return DESENLACE_CONVERTIDO
    if motivo == DESENLACE_PERDIDO:
        return DESENLACE_PERDIDO

    etapa = (prospecto.get("etapa_actual") or "").strip()
    if etapa == ETAPA_GANADO:
        return DESENLACE_CONVERTIDO
    if etapa == ETAPA_PERDIDO:
        return DESENLACE_PERDIDO

    return DESENLACE_EN_CURSO


def _fecha(epoch_ms: Any) -> str | None:
    """Epoch-ms → texto. **Ausente sigue ausente**, nunca la época cero.

    Un prospecto registrado en 1970 tendría cincuenta y seis años de antigüedad y
    encabezaría cualquier informe de prospectos estancados.
    """
    if epoch_ms in (None, 0):
        return None
    try:
        valor = int(epoch_ms)
    except (TypeError, ValueError):
        return None
    if valor <= 0:
        return None
    return datetime.fromtimestamp(valor / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def construir(
    prospectos: Iterable[Mapping[str, Any]],
    canales: Iterable[Mapping[str, Any]],
    ahora: datetime,
) -> list[dict]:
    """Una fila por prospecto. Lógica pura: no consulta ni escribe."""
    from lib.dimensiones.dim_canal import clave

    # ⚠️ **Se busca por clave de agrupación, no por la grafía publicada.**
    #
    # `dim_canal` muestra una sola grafía por canal —la más frecuente— mientras
    # que el prospecto conserva la suya. Cruzarlos por el texto haría que un
    # prospecto que escribió «linkedin» no encontrara el canal «LinkedIn» y
    # cayera en la fila desconocida: **perdería su canal sin que nada fallara**,
    # y el informe de captación repartiría mal la inversión.
    por_canal = {clave(c["canal"]): c["idcanal"] for c in canales}
    # ⚠️ **La columna `canal` que se denormaliza aquí es la que leen los
    # informes**, no `dim_canal.canal`: `ot01_captacion_por_canal` agrupa por
    # `p.canal`. Tiene que llevar la **grafía publicada**, no la clave de
    # agrupación — que está plegada a minúsculas y nunca se muestra. Ponerla
    # aquí no rompía nada: pintaba «linkedin» y «referido tsi» en el informe de
    # captación, que es justo lo que se estaba corrigiendo.
    grafia_por_clave = {clave(c["canal"]): c["canal"] for c in canales}
    version = ahora.strftime("%Y-%m-%d %H:%M:%S")

    filas = []
    for p in prospectos:
        canal = clave(p.get("como_nos_conocio"))
        filas.append(
            {
                "idprospecto": p["idprospecto"],
                "empresa": p.get("empresa"),
                "tipo_organizacion": p.get("tipo_organizacion"),
                # El prospecto sin canal cae en la fila desconocida y **cuenta en
                # los totales**: llegó igual, y dejarlo fuera haría que los
                # canales sumaran menos que el embudo.
                "idcanal": por_canal.get(canal, ID_DESCONOCIDO),
                "canal": grafia_por_clave.get(canal) or ETIQUETA_DESCONOCIDA,
                "etapa_actual": p.get("etapa_actual"),
                "desenlace": desenlace_de(p),
                "motivo_inactividad": p.get("motivo_inactividad"),
                "valor_estimado": p.get("valor_estimado"),
                "fecha_registro": _fecha(p.get("fecha_registro")),
                "version": version,
            }
        )
    return filas
