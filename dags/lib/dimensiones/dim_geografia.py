"""`dim_geografia`: una fila por calle **con sus ascendientes aplanados**.

El origen guarda la geografía como una cadena de cinco tablas —calle → ciudad →
condado → estado → país—, que es lo correcto para un sistema transaccional y lo
peor posible para analizar: agrupar por condado obliga a encadenar tres saltos, y
el almacén ni siquiera admite uniones en el origen.

Aquí se aplana una sola vez, al cargar. Después, agrupar por condado es **una
columna**.

Sin coordenadas
---------------
`Dim_UnidadEmergencia` y `Fact_Accidente` traen latitud y longitud, y **no se
copian**. La ubicación se expresa por nombre, igual que en los listados de
Emergencias y Red Operativa. Analizar cuántos accidentes hubo en un condado no
requiere saber dónde ocurrió cada uno con precisión de metros.

Una calle huérfana no se descarta
---------------------------------
Si la ciudad de una calle no está en el catálogo, la calle **se carga igualmente**
con sus ascendientes marcados como desconocidos. Descartarla haría desaparecer
del análisis todos los accidentes de esa calle, que es un precio absurdo por una
fila que falta en un catálogo intermedio.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Iterable, Mapping

from lib.dimensiones.desconocido import ETIQUETA_DESCONOCIDA, ID_DESCONOCIDO
from lib.pinot_http_client import query_pinot

#: Límite explícito: el cliente pone 10 000 por defecto y un catálogo mayor se
#: truncaría **en silencio**, dejando calles sin dimensión sin que nada falle.
LIMITE = 200_000

CONSULTAS = {
    "calles": f"SELECT idcalle, calle, idciudad FROM Dim_Calle LIMIT {LIMITE}",
    "ciudades": f"SELECT idciudad, ciudad, idcondado FROM Dim_Ciudad LIMIT {LIMITE}",
    "condados": f"SELECT idcondado, condado, idestado FROM Dim_Condado LIMIT {LIMITE}",
    "estados": f"SELECT idestado, estado, idpais FROM Dim_Estado LIMIT {LIMITE}",
    "paises": f"SELECT idpais, pais FROM Dim_Pais LIMIT {LIMITE}",
}


def extraer(consultar: Callable[[str], list[dict]] = query_pinot) -> dict[str, list[dict]]:
    """Los cinco catálogos, sin unir. **Pinot no admite uniones**: se cruzan aquí."""
    return {nombre: consultar(sql) for nombre, sql in CONSULTAS.items()}


def _indexar(filas: Iterable[Mapping[str, Any]], clave: str) -> dict[Any, Mapping[str, Any]]:
    return {f[clave]: f for f in filas}


def construir(catalogos: Mapping[str, Iterable[Mapping[str, Any]]], ahora: datetime) -> list[dict]:
    """Aplana la cadena. Lógica pura: no consulta ni escribe."""
    ciudades = _indexar(catalogos["ciudades"], "idciudad")
    condados = _indexar(catalogos["condados"], "idcondado")
    estados = _indexar(catalogos["estados"], "idestado")
    paises = _indexar(catalogos["paises"], "idpais")
    version = ahora.strftime("%Y-%m-%d %H:%M:%S")

    filas = []
    for calle in catalogos["calles"]:
        ciudad = ciudades.get(calle.get("idciudad"), {})
        condado = condados.get(ciudad.get("idcondado"), {})
        estado = estados.get(condado.get("idestado"), {})
        pais = paises.get(estado.get("idpais"), {})

        filas.append(
            {
                "idcalle": calle["idcalle"],
                "calle": calle.get("calle") or ETIQUETA_DESCONOCIDA,
                "idciudad": ciudad.get("idciudad", ID_DESCONOCIDO),
                "ciudad": ciudad.get("ciudad", ETIQUETA_DESCONOCIDA),
                "idcondado": condado.get("idcondado", ID_DESCONOCIDO),
                "condado": condado.get("condado", ETIQUETA_DESCONOCIDA),
                "idestado": estado.get("idestado", ID_DESCONOCIDO),
                "estado": estado.get("estado", ETIQUETA_DESCONOCIDA),
                "idpais": pais.get("idpais", ID_DESCONOCIDO),
                "pais": pais.get("pais", ETIQUETA_DESCONOCIDA),
                "version": version,
            }
        )
    return filas
