"""Reconstruir el histórico de las dimensiones cuyo origen **sí lo guarda**.

El versionado normal empieza el día de la primera carga: no puede saber nada
anterior. Pero algunas dimensiones sí tienen su historia registrada en el origen
—partner→plan en la bitácora de acceso, región→estado en sus validaciones— y ahí
sería absurdo empezar de cero cuando el pasado está escrito.

Estas versiones son las **únicas** que llevan `inicio_es_real = 1`: su fecha de
inicio es un cambio observado y fechado, no «desde que empezamos a mirar»
(research D2).

Tres trampas de las bitácoras reales ⚠️
----------------------------------------
Se descubrieron mirando `Fact_HistorialAccesoPartner`, y las tres producen
versiones falsas si se ignoran:

1. **Hay eventos que no cambian nada.** Un `revocacion_credencial` aparece con
   `Activo → Activo`: se registró un suceso, pero el atributo que versionamos no
   se movió. Tomar cada evento como un cambio llenaría la dimensión de versiones
   idénticas consecutivas, y un informe que cuente «cuántas veces cambió de
   plan» daría una cifra inflada.

2. **Hay eventos duplicados a milisegundos.** Dos `desactivacion_por_cascada` del
   mismo partner con 46 ms de diferencia y los mismos valores. Es el mismo hecho
   registrado dos veces.

3. **Lo anterior al primer evento no tiene fecha.** El valor con el que la
   entidad empezó es conocido —lo dice el `estado_anterior` del primer evento—
   pero **desde cuándo, no**. Esa primera versión abre por la izquierda y lleva
   `inicio_es_real = 0`, igual que en el versionado normal. Mezclarlas sería
   afirmar una fecha que nadie registró.

Lo que este módulo NO hace
--------------------------
**No reconstruye unidad→proveedor**, que es el caso que motivó el modelo: nada en
el origen lo historiza. No es una limitación del módulo, es que el dato no
existe (T033).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable, Mapping

from lib.dimensiones.versionado import INICIO_DESCONOCIDO, sk_de_version


def _ordenados(eventos: Iterable[Mapping[str, Any]], campo_instante: str) -> list[Mapping[str, Any]]:
    return sorted(eventos, key=lambda e: e.get(campo_instante) or 0)


def reconstruir_entidad(
    eventos: Iterable[Mapping[str, Any]],
    *,
    campo_anterior: str,
    campo_nuevo: str,
    campo_instante: str,
    ahora: datetime,
    convertir_instante=None,
) -> list[dict[str, Any]]:
    """Versiones de **una** entidad, a partir de su bitácora.

    Devuelve las versiones en orden cronológico. La primera abre por la izquierda
    con `inicio_es_real = 0`; las demás llevan `1` y su fecha real.

    Los eventos que no mueven el atributo **no abren versión**, y eso resuelve de
    una vez las dos primeras trampas: un evento sin cambio y un evento duplicado
    son, para este propósito, lo mismo.
    """
    ordenados = _ordenados(eventos, campo_instante)
    if not ordenados:
        return []

    convertir = convertir_instante or (lambda v: v)

    valor = ordenados[0].get(campo_anterior)
    versiones = [
        {
            "valor": valor,
            "valido_desde": INICIO_DESCONOCIDO,
            "valido_hasta": None,
            "es_vigente": 1,
            "inicio_es_real": 0,
            "version": ahora,
        }
    ]

    for evento in ordenados:
        nuevo = evento.get(campo_nuevo)
        if nuevo == valor:
            continue  # el evento no movió el atributo, o es un duplicado
        instante = convertir(evento.get(campo_instante))
        if instante is None:
            continue
        versiones[-1].update(valido_hasta=instante, es_vigente=0)
        versiones.append(
            {
                "valor": nuevo,
                "valido_desde": instante,
                "valido_hasta": None,
                "es_vigente": 1,
                "inicio_es_real": 1,
                "version": ahora,
            }
        )
        valor = nuevo

    return versiones


def reconstruir(
    eventos: Iterable[Mapping[str, Any]],
    *,
    clave_negocio: str,
    campo_anterior: str,
    campo_nuevo: str,
    campo_instante: str,
    ahora: datetime,
    convertir_instante=None,
) -> list[dict[str, Any]]:
    """Versiones de todas las entidades presentes en la bitácora."""
    por_entidad: dict[Any, list[Mapping[str, Any]]] = {}
    for evento in eventos:
        por_entidad.setdefault(evento[clave_negocio], []).append(evento)

    salida: list[dict[str, Any]] = []
    for id_negocio, propios in por_entidad.items():
        for version in reconstruir_entidad(
            propios,
            campo_anterior=campo_anterior,
            campo_nuevo=campo_nuevo,
            campo_instante=campo_instante,
            ahora=ahora,
            convertir_instante=convertir_instante,
        ):
            version[clave_negocio] = id_negocio
            version["sk"] = sk_de_version(id_negocio, version["valido_desde"])
            salida.append(version)
    return salida


def divergencias(
    versiones: Iterable[Mapping[str, Any]],
    valor_actual_por_clave: Mapping[Any, Any],
    *,
    clave_negocio: str,
) -> list[dict[str, Any]]:
    """Entidades cuya última versión reconstruida **no coincide** con su valor actual.

    Existe porque una bitácora incompleta produce una historia que parece
    correcta y termina en un valor equivocado — y entonces el error no está en la
    última versión sino en todas. Comprobarlo contra el estado actual, que sí es
    fiable, es la única forma barata de detectarlo.

    Devolver la lista en vez de lanzar es deliberado: una divergencia **no debe
    detener la carga**, porque la historia reconstruida sigue siendo mejor que
    ninguna. Debe verse.
    """
    ultima_por_clave = {
        v[clave_negocio]: v for v in versiones if v.get("es_vigente") == 1
    }
    return [
        {
            clave_negocio: clave,
            "reconstruido": version.get("valor"),
            "actual": valor_actual_por_clave.get(clave),
        }
        for clave, version in ultima_por_clave.items()
        if clave in valor_actual_por_clave and version.get("valor") != valor_actual_por_clave[clave]
    ]
