"""Catálogos que pueblan los desplegables de los filtros — L1.

⚠️ **Un catálogo es un control de acceso, aunque no lo parezca**
-----------------------------------------------------------------
Hasta el 2026-08-18 los filtros de ubicación se pedían como identificadores
numéricos escritos a mano («Condado (id)»), y la tabla solo mostraba nombres: no
había forma de averiguar el número desde la pantalla. Sustituirlos por
desplegables exige publicar la lista de opciones, y ahí aparece el riesgo que el
formulario numérico no tenía.

`Cobertura` acota **qué filas** ve un cliente, pero la lista de condados no es
una fila del listado: es metadato. Publicarla entera revelaría dónde opera el
sistema a quien contrató una sola zona — y lo revelaría **aunque su listado
siguiera devolviendo cero filas**, que es lo que haría creer que no pasa nada.

Por eso el acotamiento se aplica aquí con la misma regla que en los listados, y
con la misma distinción entre `None` (rol interno, todo) y conjunto vacío
(cliente sin zonas, nada).

Severidad y tipo de reporte **no** se acotan: son catálogos de referencia del
sistema y no dicen dónde opera nadie.
"""

from __future__ import annotations

from typing import Any

from core.informes.cobertura import Cobertura
from core.repositories.accidentes.informes_casos_repository import (
    InformesCasosRepository,
)
from core.repositories.accidentes.informes_ubicacion_repository import (
    InformesUbicacionRepository,
)


class InformesCatalogosService:
    def __init__(
        self,
        repo: InformesCasosRepository | None = None,
        ubicaciones: InformesUbicacionRepository | None = None,
    ):
        self.repo = repo or InformesCasosRepository()
        self.ubicaciones = ubicaciones or InformesUbicacionRepository()

    def catalogos(self, *, cobertura: Cobertura) -> dict[str, list[dict[str, Any]]]:
        """Los cuatro catálogos del listado de casos, en una sola respuesta.

        Van juntos a propósito: la barra de filtros los necesita todos a la vez
        para poder pintarse, y cuatro peticiones darían cuatro estados de carga
        que pueden fallar por separado — con el formulario a medio poblar y sin
        nada que explique por qué falta un desplegable.
        """
        contratados = cobertura.ubicaciones
        condados = self.ubicaciones.catalogo_condados(contratados)
        return {
            "severidad": self.repo.catalogo_severidades(),
            "tipo_reportado": self.repo.catalogo_tipos_reportados(),
            "condado": condados,
            "ciudad": _desambiguar_ciudades(
                self.ubicaciones.catalogo_ciudades(contratados), condados
            ),
        }


def _desambiguar_ciudades(
    ciudades: list[dict[str, Any]], condados: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Añade el condado a las ciudades **homónimas**, y solo a esas.

    ⚠️ No es cosmética. Hay dos ciudades llamadas «Ciudad de Mexico», una en
    Cuauhtémoc y otra en Benito Juárez, y el desplegable las pintaba como dos
    entradas idénticas: quien elegía una no podía saber cuál estaba eligiendo, y
    el listado devolvía un subconjunto sin ninguna explicación a la vista.

    Se cualifica **solo cuando hay ambigüedad**: repetir el condado en todas las
    ciudades sería ruido en el caso normal, que es el que no necesita ayuda.

    Una ciudad cuyo condado no resuelve se deja con su nombre desnudo: inventar
    un condado para poder distinguirla sería peor que la ambigüedad.
    """
    repetidos: dict[str, int] = {}
    for ciudad in ciudades:
        nombre = str(ciudad["nombre"])
        repetidos[nombre] = repetidos.get(nombre, 0) + 1

    nombre_condado = {c["id"]: c["nombre"] for c in condados}

    resultado = []
    for ciudad in ciudades:
        nombre = str(ciudad["nombre"])
        condado = nombre_condado.get(ciudad.get("idcondado"))
        if repetidos[nombre] > 1 and condado:
            nombre = f"{nombre} · {condado}"
        resultado.append({"id": ciudad["id"], "nombre": nombre})
    return resultado
