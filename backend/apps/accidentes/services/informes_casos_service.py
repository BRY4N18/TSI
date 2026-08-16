"""Servicio del listado de casos — L1.

⚠️ Devuelve los TRES HECHOS, no un estado calculado
-----------------------------------------------------
`activo`, `hora_fin` y `duplicado_de` viajan por separado. **No hay campo
`estado` en la respuesta.**

Calcularlo funcionaría hoy porque el módulo de fusión garantiza que cerrado,
descartado y fusionado son mutuamente excluyentes — pero esa garantía vive en
otro módulo y podría cambiar sin que este se entere. Un campo derivado empezaría
a mentir el día que cambiara, y nadie lo notaría: seguiría teniendo la forma
correcta.

Devolver los hechos no pierde información: quien necesite el estado formal tiene
los informes agregados, que lo leen de donde está.
"""

from __future__ import annotations

from typing import Any

from core.informes.cobertura import Cobertura
from core.informes.formato import a_iso
from core.informes.paginacion import Orden, Pagina
from core.repositories.accidentes.informes_casos_repository import (
    CURSOR_CASOS,
    ORDEN_CASOS,
    SIN_VALOR,
    SITUACION_CERRADO,
    InformesCasosRepository,
)
from core.repositories.accidentes.informes_ubicacion_repository import (
    InformesUbicacionRepository,
)


class InformesCasosService:
    def __init__(
        self,
        repo: InformesCasosRepository | None = None,
        ubicaciones: InformesUbicacionRepository | None = None,
    ):
        self.repo = repo or InformesCasosRepository()
        self.ubicaciones = ubicaciones or InformesUbicacionRepository()

    def casos(
        self,
        *,
        cobertura: Cobertura,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_CASOS,
        idseveridad: int | None = None,
        idtiporeportado: int | None = None,
        idcondado: int | None = None,
        idciudad: int | None = None,
        situacion: str | None = None,
        desde_ms: int | None = None,
        hasta_ms: int | None = None,
    ) -> Pagina:
        idcalles = self._calles_a_consultar(cobertura, idcondado, idciudad)

        # ⚠️ El eje impone la situación al cliente; no la elige el consumidor.
        # La emergencia en curso es información operativa, y forzarlo aquí —y no
        # en la vista— evita que un listado nuevo se olvide de hacerlo.
        if cobertura.solo_cerrados:
            situacion = SITUACION_CERRADO

        crudas = self.repo.casos(
            cursor=cursor,
            limit=limit,
            orden=orden,
            idcalles=idcalles,
            idseveridad=idseveridad,
            idtiporeportado=idtiporeportado,
            situacion=situacion,
            desde_ms=desde_ms,
            hasta_ms=hasta_ms,
        )
        pagina = CURSOR_CASOS.recortar(crudas, limit)

        severidades = self.repo.severidades(
            [f.get("idseveridad") for f in pagina.filas]
        )
        tipos = self.repo.tipos_reportados(
            [f.get("idtiporeportado") for f in pagina.filas]
        )
        lugares = self.ubicaciones.ubicaciones_de_calle(
            [f.get("idcalle") for f in pagina.filas]
        )

        return pagina._replace(
            filas=[_fila(f, severidades, tipos, lugares) for f in pagina.filas]
        )

    def _calles_a_consultar(
        self, cobertura: Cobertura, idcondado: int | None, idciudad: int | None
    ) -> frozenset[int] | None:
        """Cruza el acotamiento con el filtro geográfico pedido.

        ⚠️ El resultado es un conjunto que puede quedar **vacío**, y vacío
        significa cero filas. `None` significa «no filtrar», y solo lo obtiene
        quien no está acotado y tampoco pidió ubicación.
        """
        pedidas: frozenset[int] | None = None
        if idciudad is not None:
            pedidas = self.ubicaciones.calles_de_ciudades([idciudad])
        elif idcondado is not None:
            pedidas = self.ubicaciones.calles_de_condados([idcondado])

        if not cobertura.acotado:
            return pedidas

        contratadas = self.ubicaciones.calles_de_condados(cobertura.ubicaciones)
        if pedidas is None:
            return contratadas
        # Pedir una zona ajena no amplía nada: la intersección la deja vacía.
        return contratadas & pedidas


def _fila(cruda, severidades, tipos, lugares) -> dict[str, Any]:
    lugar = lugares.get(cruda.get("idcalle")) or {}
    return {
        # El número de caso es lenguaje de negocio: así lo nombra quien lo
        # atiende, y ocultarlo obligaría a traducir en cada conversación.
        "numero_caso": cruda.get("idaccidente"),
        "severidad": severidades.get(cruda.get("idseveridad")),
        # Un caso sin ubicación resoluble llega con los tres ausentes y **no se
        # omite**: es una anomalía que la supervisión necesita ver — y además
        # nunca podrá acotarse a ninguna zona.
        "calle": lugar.get("calle"),
        "ciudad": lugar.get("ciudad"),
        "condado": lugar.get("condado"),
        "tipo_reportado": tipos.get(cruda.get("idtiporeportado")),
        "num_vehiculos": cruda.get("numvehiculos"),
        "num_heridos": cruda.get("numheridos"),
        "num_victimas": cruda.get("numvictimas"),
        "num_fallecidos": cruda.get("numfallecidos"),
        "fecha_accidente": a_iso(cruda.get("fechahoraaccidente")),
        # ── Los tres hechos, por separado y sin interpretar ──────────────────
        "activo": bool(cruda.get("activo")),
        # ⚠️ `horafin` es una columna **STRING que guarda epoch-ms**: la
        # escriben `cerrar_caso_service` y `cancelar_caso_service` con el reloj
        # del sistema. Devolverla verbatim entregaba `"1786625595899"`, que en
        # pantalla es un número ilegible y no se puede ordenar ni comparar como
        # fecha. Se normaliza como cualquier otra marca de tiempo de la API.
        "hora_fin": _hora_fin(cruda.get("horafin")),
        "duracion_minutos": cruda.get("duracionminutos"),
        "duplicado_de": _sin_centinela(cruda.get("idaccidenteorigen")),
    }


def _hora_fin(valor: Any) -> str | None:
    """Normaliza la hora de fin a ISO, tolerando que no sea numérica.

    La columna es `STRING` y el esquema no impide que alguien escriba otra cosa.
    Si no es un entero, se devuelve tal cual: inventar una fecha a partir de un
    texto desconocido sería peor que mostrar lo que hay.
    """
    texto = _sin_centinela(valor)
    if texto is None:
        return None
    try:
        return a_iso(int(texto))
    except (TypeError, ValueError):
        return texto


def _sin_centinela(valor: Any) -> str | None:
    """`''` y la cadena literal `'null'` son ausencia, no un valor."""
    if valor is None:
        return None
    texto = str(valor).strip()
    return None if texto in SIN_VALOR else texto
