"""Traduce zonas contratadas a un conjunto de calles, **por lotes**.

Es la pieza que hace del acotamiento por cobertura un **filtro** y no una
comprobación fila a fila. La cadena es condado → ciudades → calles, y son **tres
consultas por petición** —una por nivel—, no una por condado ni, mucho menos,
una por accidente.

El sistema ya documenta este patrón como el estándar para resolver un nivel
geográfico: `AccidenteRepository.list_activos` y
`HistorialEmergenciasService._resolver_calles_por_ubicacion` lo usan para
resolver un estado completo. La cadena que hace falta aquí es **un nivel más
corta** que aquella, así que si aquello es viable, esto lo es con más razón.

⚠️ La alternativa es lo que el módulo operativo hace hoy
---------------------------------------------------------
`historial_emergencias_service.py` contiene las dos formas a diez líneas de
distancia: el filtro por ubicación usa el conjunto resuelto —bien— y el
acotamiento del cliente resuelve el condado **mientras recorre**. Lo segundo no
es un filtro: el trabajo por fila incluye resolver la ubicación, y el número de
filas recorridas crece justamente cuando las zonas del cliente son escasas.
"""

from __future__ import annotations

from typing import Iterable, Sequence

from core.pinot.client import PinotClient

#: Tope de seguridad por consulta. Un cliente no contrata «todas las zonas» —lo
#: limita el negocio—, pero un tope evita que un dato corrupto pida el catálogo
#: entero.
TOPE_CATALOGO = 10_000


class InformesUbicacionRepository:
    """Solo lectura. Resuelve catálogos geográficos por lotes."""

    def __init__(self, pinot: PinotClient | None = None):
        self.pinot = pinot or PinotClient()

    def calles_de_condados(self, idcondados: Iterable[int]) -> frozenset[int]:
        """Calles de los condados dados. **Dos consultas**, no una por condado.

        Sin condados devuelve conjunto vacío, y eso significa **cero calles**.
        No es lo mismo que «no filtrar»: quien llama debe conservar la
        diferencia.
        """
        condados = _ids(idcondados)
        if not condados:
            return frozenset()

        ciudades = self.pinot.query(
            "SELECT idciudad, idcondado FROM Dim_Ciudad "
            "WHERE idcondado IN %(ids)s AND activo = true LIMIT %(limit)s",
            {"ids": condados, "limit": TOPE_CATALOGO},
        )
        idciudades = _ids(c.get("idciudad") for c in ciudades)
        if not idciudades:
            return frozenset()

        calles = self.pinot.query(
            "SELECT idcalle, idciudad FROM Dim_Calle "
            "WHERE idciudad IN %(ids)s AND activo = true LIMIT %(limit)s",
            {"ids": idciudades, "limit": TOPE_CATALOGO},
        )
        return frozenset(_ids(c.get("idcalle") for c in calles))

    def calles_de_ciudades(self, idciudades: Iterable[int]) -> frozenset[int]:
        """Calles de las ciudades dadas. **Una** consulta."""
        ciudades = _ids(idciudades)
        if not ciudades:
            return frozenset()
        calles = self.pinot.query(
            "SELECT idcalle, idciudad FROM Dim_Calle "
            "WHERE idciudad IN %(ids)s AND activo = true LIMIT %(limit)s",
            {"ids": ciudades, "limit": TOPE_CATALOGO},
        )
        return frozenset(_ids(c.get("idcalle") for c in calles))

    def ubicaciones_de_calle(self, idcalles: Sequence[int]) -> dict[int, dict]:
        """`idcalle` → `{calle, ciudad, condado}`. **Tres consultas.**

        Devuelve el **condado**, que es el nivel al que se contrata cobertura.
        `UbicacionCatalogoRepository.resolver_calles` devuelve el estado en su
        lugar, así que no sirve para este listado sin cambiarlo — y cambiarlo
        movería una pieza del módulo operativo por una necesidad de informes.
        """
        ids = _ids(idcalles)
        if not ids:
            return {}

        calles = self.pinot.query(
            "SELECT idcalle, calle, idciudad FROM Dim_Calle "
            "WHERE idcalle IN %(ids)s LIMIT %(limit)s",
            {"ids": ids, "limit": TOPE_CATALOGO},
        )
        idciudades = _ids(c.get("idciudad") for c in calles)
        ciudades = (
            self.pinot.query(
                "SELECT idciudad, ciudad, idcondado FROM Dim_Ciudad "
                "WHERE idciudad IN %(ids)s LIMIT %(limit)s",
                {"ids": idciudades, "limit": TOPE_CATALOGO},
            )
            if idciudades
            else []
        )
        idcondados = _ids(c.get("idcondado") for c in ciudades)
        condados = (
            self.pinot.query(
                "SELECT idcondado, condado, idestado FROM Dim_Condado "
                "WHERE idcondado IN %(ids)s LIMIT %(limit)s",
                {"ids": idcondados, "limit": TOPE_CATALOGO},
            )
            if idcondados
            else []
        )

        ciudad_por_id = {c["idciudad"]: c for c in ciudades}
        condado_por_id = {c["idcondado"]: c for c in condados}

        resultado: dict[int, dict] = {}
        for calle in calles:
            ciudad = ciudad_por_id.get(calle.get("idciudad"))
            condado = condado_por_id.get(ciudad["idcondado"]) if ciudad else None
            resultado[calle["idcalle"]] = {
                "calle": calle.get("calle"),
                "ciudad": ciudad.get("ciudad") if ciudad else None,
                "condado": condado.get("condado") if condado else None,
            }
        return resultado

    def zonas_contratadas(self, idcliente: int) -> frozenset[int]:
        """Condados contratados por un cliente.

        ⚠️ Un cliente sin preferencias devuelve conjunto vacío, y eso significa
        **cero resultados**. La lectura contraria daría el mapa de siniestralidad
        completo a quien no contrató nada.

        La columna es `id_cliente` con guion bajo, no `idcliente`.
        """
        from apps.seguimiento.services.historial_emergencias_service import (
            HistorialEmergenciasService,
        )

        filas = self.pinot.query(
            "SELECT id_cliente, zonas_geograficas FROM Dim_Preferencias_Cliente "
            "WHERE id_cliente = %(id_cliente)s LIMIT 1",
            {"id_cliente": idcliente},
        )
        if not filas:
            return frozenset()
        # Se reutiliza el mismo intérprete que ya usan Seguimiento y Partners:
        # el formato de esa columna es texto libre y tres lecturas distintas
        # darían tres alcances distintos para el mismo contrato.
        return frozenset(
            HistorialEmergenciasService.condados_desde_preferencias(
                filas[0].get("zonas_geograficas")
            )
        )


def _ids(valores: Iterable) -> list[int]:
    return sorted({int(v) for v in valores if v is not None and int(v) > 0})
