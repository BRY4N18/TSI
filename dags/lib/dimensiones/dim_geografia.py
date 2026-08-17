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
    # Red Operativa (US1). La vecindad entre condados es una **relacion estatica
    # entre entidades ya modeladas**: no tiene instante ni grano propio, asi que
    # es un atributo de la geografia y no un hecho (research D3). Un hecho de
    # vecindad seria una tabla de dos filas con su flujo y su DAG.
    "vecinos": f"SELECT idcondado, idcondadovecino FROM Dim_CondadoVecino WHERE activo = true LIMIT {LIMITE}",
    # ⚠️ La region operativa se relaciona con la geografia **por estado**, no por
    # condado: `Dim_RegionOperativa.idestado`. No existe ninguna tabla que ate
    # region y condado directamente —se comprobo—, asi que el condado hereda la
    # region de su estado.
    #
    # Tiene una consecuencia que conviene saber: **todos los condados de un
    # estado comparten region**. Si algun dia una region cubriera parte de un
    # estado, esta derivacion se la atribuiria entera, y la cobertura por region
    # saldria de mas sin que nada fallara.
    "regiones": f"SELECT idregionoperativa, idestado FROM Dim_RegionOperativa WHERE activo = true LIMIT {LIMITE}",
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

    # ⚠️ La vecindad es **simetrica**: si A es vecino de B, B lo es de A. El
    # origen guarda una sola direccion, y leerla tal cual dejaria a la mitad de
    # los condados sin vecinos declarados — que en el informe de cobertura
    # critica es la marca de «sin alternativas», la situacion mas grave que
    # reporta. Un fallo de lectura se publicaria como una emergencia operativa.
    vecinos_por_condado: dict[Any, set] = {}
    for rel in catalogos.get("vecinos", []):
        a, b = rel.get("idcondado"), rel.get("idcondadovecino")
        if a is None or b is None:
            continue
        vecinos_por_condado.setdefault(a, set()).add(b)
        vecinos_por_condado.setdefault(b, set()).add(a)

    # ⚠️ UN ESTADO PUEDE TENER VARIAS REGIONES, Y ENTONCES LA REGION ES AMBIGUA
    # -------------------------------------------------------------------------
    # La version obvia de esto es un diccionario `idestado -> idregionoperativa`,
    # y **miente en silencio**: hoy las dos regiones del sistema comparten
    # `idestado = 1`, asi que el diccionario se queda con la ultima que llegue y
    # atribuye TODOS los condados a esa. Con los datos actuales serian todos a
    # «Region Prueba Norte», una region de pruebas.
    #
    # El orden en que Pinot devuelva las filas decidiria la respuesta, y la
    # cobertura por region saldria completa y equivocada — el peor resultado
    # posible: una cifra que nadie cuestiona porque no parece rota.
    #
    # Cuando el estado tiene mas de una region, la region del condado es
    # **ausente**: no se sabe cual lo cubre. Es informacion honesta, y deja el
    # informe de cobertura por region senalando lo que falta en vez de inventarlo.
    por_estado: dict[Any, set] = {}
    for r in catalogos.get("regiones", []):
        if r.get("idestado") is None or r.get("idregionoperativa") is None:
            continue
        por_estado.setdefault(r["idestado"], set()).add(r["idregionoperativa"])

    region_por_estado = {
        estado: next(iter(regiones)) if len(regiones) == 1 else None
        for estado, regiones in por_estado.items()
    }
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
                # Vacio significa **sin vecinos declarados**, que es un dato y no
                # una ausencia: un condado sin alternativas es lo que la
                # cobertura critica tiene que senalar, no omitir.
                "condados_vecinos": sorted(
                    vecinos_por_condado.get(condado.get("idcondado"), ())
                ),
                "idregionoperativa": region_por_estado.get(condado.get("idestado")),
                "idestado": estado.get("idestado", ID_DESCONOCIDO),
                "estado": estado.get("estado", ETIQUETA_DESCONOCIDA),
                "idpais": pais.get("idpais", ID_DESCONOCIDO),
                "pais": pais.get("pais", ETIQUETA_DESCONOCIDA),
                "version": version,
            }
        )
    return filas
