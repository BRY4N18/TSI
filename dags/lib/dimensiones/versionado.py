"""Versionado de dimensiones: abrir una versión nueva solo cuando algo cambió.

Qué problema resuelve
---------------------
Si la dimensión guarda **el estado actual** de cada entidad, todo informe
histórico se reescribe solo. Cambiar hoy el proveedor de una unidad haría que
sus despachos de hace seis meses aparezcan bajo el proveedor nuevo — y la cifra
**parecería correcta**. Ese es el defecto documentado que el modelo existe para
corregir.

La solución es guardar una fila por **versión**: cada hecho apunta a la versión
vigente en su momento, no a la entidad. Este módulo decide cuándo nace una
versión.

Las tres decisiones posibles
----------------------------
1. **La entidad no existía** → se abre su primera versión.
2. **Existe y ningún atributo versionado cambió** → no se toca nada. Es el caso
   común, y no debe costar nada.
3. **Existe y algún atributo cambió** → se cierra la vigente y se abre una nueva.

`inicio_es_real` — la marca que evita mentir  ⚠️
------------------------------------------------
Una fecha de inicio puede significar dos cosas muy distintas:

- **`1`, real**: se sabe cuándo ocurrió el cambio, porque el origen lo historiza
  y la versión se reconstruyó desde ahí.
- **`0`, no real**: la fecha es el momento en que **el modelo empezó a mirar**,
  no cuando el cambio ocurrió.

Sin esta distinción el modelo presentaría *«no lo sabemos»* como *«siempre fue
así»* (research D2). Con ella, un informe puede decir «desde esta fecha la
atribución es exacta; antes, es el estado conocido al arrancar» — que es honesto
y sigue siendo útil.

**Detectar un cambio al cargar no lo convierte en observado.** El cambio pudo
ocurrir en cualquier instante desde la carga anterior; lo único que se sabe es
que ya había ocurrido al mirar. Por eso `inicio_es_real = 1` requiere que quien
llama **aporte el instante**, que solo puede salir de una tabla de historial del
origen. Es la razón de que las versiones de unidad lleven siempre `0`: nada en el
origen historiza el cambio de proveedor.

Este módulo es lógica pura
--------------------------
No consulta ni escribe: recibe el estado y devuelve la decisión. Así la regla que
sostiene la corrección histórica del modelo se puede probar sin levantar nada.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterable, Mapping

#: Atributos cuyo cambio abre una versión nueva de unidad. **El proveedor es el
#: motivo de todo esto**; los demás acompañan porque un informe histórico que los
#: use tiene el mismo problema.
ATRIBUTOS_VERSIONADOS_UNIDAD = ("idcliente", "proveedor", "idcondado", "zona_cobertura")

#: Inicio de la primera versión de una entidad. Es un intervalo abierto por la
#: izquierda, **no una fecha**: dice «hasta donde sabemos, siempre fue así», y
#: `inicio_es_real = 0` lo declara. Sin esto, los hechos anteriores a la primera
#: carga no tendrían versión que los cubriera.
INICIO_DESCONOCIDO = datetime(1970, 1, 1)


@dataclass(frozen=True)
class ResultadoVersionado:
    """Qué hacer con una entidad tras compararla con su versión vigente.

    `sin_cambios` no es redundante con las otras dos: distingue «no hay nada que
    escribir» de «hay algo que escribir», sin que quien llama tenga que deducirlo
    de dos comprobaciones de nulidad.
    """

    sin_cambios: bool
    version_cerrada: dict[str, Any] | None = None
    version_nueva: dict[str, Any] | None = None

    @property
    def filas(self) -> list[dict[str, Any]]:
        """Las filas a escribir, listas para insertar. Vacía si no cambió nada."""
        return [f for f in (self.version_cerrada, self.version_nueva) if f is not None]


def sk_de_version(clave_negocio: Any, valido_desde: datetime) -> int:
    """Clave sustituta **determinista** de una versión.

    Determinista a propósito: recargar el mismo período debe producir la misma
    clave, o el motor de deduplicación vería filas distintas y el hecho quedaría
    apuntando a una versión huérfana. Un contador incremental no serviría —
    daría claves distintas en cada corrida.

    Se deriva de (clave de negocio, inicio de vigencia), que es lo que identifica
    a una versión de forma única. Truncado a 63 bits: cabe en `UInt64` y deja
    fuera el `0`, reservado a la fila desconocida.
    """
    semilla = f"{clave_negocio}|{valido_desde.isoformat()}".encode("utf-8")
    digest = hashlib.blake2b(semilla, digest_size=8).digest()
    return (int.from_bytes(digest, "big") >> 1) or 1


def _difieren(
    origen: Mapping[str, Any],
    vigente: Mapping[str, Any],
    atributos: Iterable[str],
) -> list[str]:
    """Atributos versionados que cambiaron. Lista vacía = no cambió nada."""
    return [a for a in atributos if origen.get(a) != vigente.get(a)]


def decidir_version(
    fila_origen: Mapping[str, Any],
    version_vigente: Mapping[str, Any] | None,
    *,
    clave_negocio: str,
    atributos: Iterable[str],
    ahora: datetime,
    campo_sk: str = "sk_unidad",
    instante_observado: datetime | None = None,
) -> ResultadoVersionado:
    """Decide si abrir una versión nueva de esta entidad, y con qué vigencia.

    `instante_observado` es **el único camino a `inicio_es_real = 1`**: solo debe
    aportarse cuando el origen historiza el cambio y se conoce su fecha real.
    Omitirlo significa «esto es lo que veo al cargar», y la versión lo declara.

    Devuelve las filas a escribir; **no escribe nada**.
    """
    atributos = tuple(atributos)
    id_negocio = fila_origen[clave_negocio]

    if version_vigente is not None and not _difieren(fila_origen, version_vigente, atributos):
        return ResultadoVersionado(sin_cambios=True)

    es_real = instante_observado is not None
    if instante_observado is not None:
        desde = instante_observado
    elif version_vigente is None:
        # ⚠️ La PRIMERA versión de una entidad abre por la izquierda, no en el
        # instante de la carga. Si empezara hoy, todo hecho anterior quedaría sin
        # versión que lo cubra y se atribuiría a «desconocido» — es decir, el
        # modelo perdería de golpe la atribución de todo el histórico, que es
        # peor que el defecto que vino a corregir.
        #
        # `inicio_es_real = 0` sigue diciendo la verdad sobre esta fecha: no es
        # un inicio observado, es «esto es lo que sabemos al empezar a mirar».
        # Un cambio POSTERIOR sí abre una versión fechada, y a partir de ahí la
        # atribución es exacta.
        desde = INICIO_DESCONOCIDO
    else:
        desde = ahora

    nueva = dict(fila_origen)
    nueva[campo_sk] = sk_de_version(id_negocio, desde)
    nueva.update(
        valido_desde=desde,
        valido_hasta=None,
        es_vigente=1,
        inicio_es_real=1 if es_real else 0,
        version=ahora,
    )

    cerrada: dict[str, Any] | None = None
    if version_vigente is not None:
        cerrada = dict(version_vigente)
        cerrada.update(valido_hasta=desde, es_vigente=0, version=ahora)

    return ResultadoVersionado(sin_cambios=False, version_cerrada=cerrada, version_nueva=nueva)


def version_vigente_en(
    versiones: Iterable[Mapping[str, Any]],
    instante: datetime,
) -> Mapping[str, Any] | None:
    """La versión vigente en ese instante, o `None` si ninguna lo cubre.

    Es lo que convierte la dimensión versionada en atribución histórica real: el
    hecho de despacho la usa para apuntar a **la versión de unidad de aquel
    momento**, no a la actual.

    El intervalo es **cerrado por la izquierda y abierto por la derecha**:
    `valido_desde <= instante < valido_hasta`. No es un detalle — con ambos
    extremos cerrados, un despacho ocurrido exactamente en el instante del cambio
    de proveedor encajaría en dos versiones y se contaría dos veces.

    Una versión anterior al inicio del versionado devuelve `None`, y quien llama
    decide qué hacer. **Adivinar aquí sería justo el error que el modelo existe
    para evitar**: la respuesta honesta a «de quién era esta unidad antes de que
    empezáramos a mirar» es que no se sabe.
    """
    for version in versiones:
        desde = version.get("valido_desde")
        hasta = version.get("valido_hasta")
        if desde is not None and instante < desde:
            continue
        if hasta is not None and instante >= hasta:
            continue
        return version
    return None


def versionar_lote(
    filas_origen: Iterable[Mapping[str, Any]],
    vigentes_por_clave: Mapping[Any, Mapping[str, Any]],
    *,
    clave_negocio: str,
    atributos: Iterable[str],
    ahora: datetime,
) -> list[dict[str, Any]]:
    """Aplica `decidir_version` a un lote y devuelve solo las filas a escribir.

    Las entidades que no cambiaron **no producen fila alguna**: el mecanismo no
    debe penalizar el caso común, que es la inmensa mayoría de las corridas.
    """
    salida: list[dict[str, Any]] = []
    for fila in filas_origen:
        resultado = decidir_version(
            fila,
            vigentes_por_clave.get(fila[clave_negocio]),
            clave_negocio=clave_negocio,
            atributos=atributos,
            ahora=ahora,
        )
        salida.extend(resultado.filas)
    return salida
