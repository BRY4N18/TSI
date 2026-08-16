"""Paginacion keyset por cursor para los listados tacticos simples.

**Nunca `OFFSET`** (research D2). Con inserciones concurrentes —y estas tablas
las alimenta Kafka en continuo— `OFFSET` reparte filas repetidas o saltadas
entre paginas, que es justo lo que SC-005 prohibe. El keyset no sufre eso porque
no cuenta filas: arranca donde quedo la anterior.

Como funciona
-------------
Se piden `limit + 1` filas. Si vuelven mas de `limit`, hay pagina siguiente: se
descarta la sobrante y el cursor se compone con los valores de la **ultima fila
devuelta**. Es una fila real, no un contador, y por eso sigue siendo valida
aunque entren filas nuevas mientras el consumidor pagina.

Forma del cursor
----------------
Los valores del cursor unidos por `|`, en el orden en que ordena la consulta:
`"1786569480560|42"` para un cursor compuesto, `"42"` para uno escalar
(`data-model.md` §4). El contrato lo declara **opaco**: el consumidor lo copia
tal cual y no lo interpreta.

Por que casi todos son compuestos
---------------------------------
Un cursor sobre un campo no unico no puede desempatar: dos filas con la misma
fecha caen del mismo lado del `>`, asi que una se repite o se pierde en el corte
de pagina. Por eso todo listado ordena por su campo **mas** la clave primaria, y
el cursor lleva ambos. Cuando el campo de orden ya *es* la clave, el cursor es
escalar y el desempate sobra.
"""

from __future__ import annotations

from typing import Any, Callable, NamedTuple, Sequence

LIMIT_DEFECTO = 50
LIMIT_MAXIMO = 500

SEPARADOR = "|"


class LimiteInvalido(ValueError):
    """El `limit` pedido no es un entero valido o supera el maximo."""


class CursorInvalido(ValueError):
    """El cursor recibido no tiene la forma que este listado emite."""


class CampoCursor(NamedTuple):
    """Un componente del cursor: su columna y como se lee del texto recibido."""

    nombre: str
    convertir: Callable[[str], Any] = int


class Orden(NamedTuple):
    """Direccion del recorrido. Gobierna a la vez el `ORDER BY` y el cursor.

    Van juntos porque **deben** ir juntos: si el `ORDER BY` es `DESC` y el cursor
    compara con `>`, la consulta devuelve la pagina anterior en vez de la
    siguiente y el consumidor pagina en circulos sin recibir ningun error.
    """

    descendente: bool

    @property
    def sql(self) -> str:
        return "DESC" if self.descendente else "ASC"

    @property
    def comparador(self) -> str:
        return "<" if self.descendente else ">"


ASC = Orden(descendente=False)
DESC = Orden(descendente=True)


def parse_dir(query_params, *, por_defecto: Orden) -> Orden:
    """Lee `?dir=asc|desc`; ausente conserva el orden por defecto del listado.

    Un valor distinto de los dos es `400`: interpretarlo como el defecto le
    devolveria al consumidor el listado al reves de como cree haberlo pedido.
    """
    crudo = query_params.get("dir")
    if crudo is None or crudo == "":
        return por_defecto
    normalizado = str(crudo).strip().lower()
    if normalizado == "asc":
        return ASC
    if normalizado == "desc":
        return DESC
    raise LimiteInvalido(f"El parametro 'dir' debe ser 'asc' o 'desc'; se recibio '{crudo}'.")


class Pagina(NamedTuple):
    """El resultado ya recortado, con el cursor de la pagina siguiente."""

    filas: list[dict[str, Any]]
    cursor: str | None
    limit: int

    @property
    def has_next(self) -> bool:
        return self.cursor is not None

    def to_meta(self) -> dict[str, Any]:
        """Forma de `meta.pagination`. `cursor` es `null` en la ultima pagina."""
        return {"cursor": self.cursor, "limit": self.limit, "has_next": self.has_next}


def parse_limit(
    query_params, *, defecto: int = LIMIT_DEFECTO, maximo: int = LIMIT_MAXIMO
) -> int:
    """Lee y valida `?limit=`.

    Un `limit` sobre el maximo es `400`, **no se recorta en silencio** (FR-016).
    Recortarlo callando le haria creer al consumidor que recibio todo lo que
    pidio, y la unica forma de que lo notara seria cuadrar cifras contra otra
    fuente — es decir, tarde.
    """
    crudo = query_params.get("limit")
    if crudo is None or crudo == "":
        return defecto

    try:
        limit = int(crudo)
    except (TypeError, ValueError) as exc:
        raise LimiteInvalido(
            f"El parametro 'limit' debe ser un entero; se recibio '{crudo}'."
        ) from exc

    if limit < 1:
        raise LimiteInvalido(f"El parametro 'limit' debe ser mayor que cero; se recibio {limit}.")
    if limit > maximo:
        raise LimiteInvalido(
            f"El parametro 'limit' no puede superar {maximo}; se recibio {limit}."
        )
    return limit


class Cursor:
    """Codifica y descodifica el cursor de un listado concreto.

    Se construye una vez por listado con los campos que lo componen, en el mismo
    orden que el `ORDER BY`. Si ese orden y este no coinciden, la paginacion
    salta filas sin dar ningun error, asi que van juntos a proposito: el
    repositorio construye ambos desde la misma declaracion.
    """

    def __init__(self, *campos: CampoCursor):
        if not campos:
            raise ValueError("Un cursor necesita al menos un campo.")
        self.campos: tuple[CampoCursor, ...] = campos

    @property
    def escalar(self) -> bool:
        return len(self.campos) == 1

    def decodificar(self, texto: str | None) -> tuple[Any, ...] | None:
        """Convierte el cursor recibido en los valores de arranque, o `None`.

        Un cursor mal formado es `400`, no una primera pagina silenciosa:
        devolver el principio del listado ante un cursor corrupto haria que el
        consumidor recorriera en bucle las mismas filas creyendo que avanza.
        """
        if texto is None or texto == "":
            return None

        partes = texto.split(SEPARADOR)
        if len(partes) != len(self.campos):
            raise CursorInvalido(
                f"El cursor debe tener {len(self.campos)} componente(s) separados por "
                f"'{SEPARADOR}'; se recibieron {len(partes)}."
            )

        try:
            return tuple(campo.convertir(parte) for campo, parte in zip(self.campos, partes))
        except (TypeError, ValueError) as exc:
            raise CursorInvalido(f"El cursor '{texto}' no tiene un formato reconocible.") from exc

    def codificar(self, fila: dict[str, Any]) -> str:
        """Compone el cursor desde la ultima fila devuelta."""
        valores = []
        for campo in self.campos:
            valor = fila.get(campo.nombre)
            if valor is None:
                # Un centinela coercionado a None en una columna de orden rompe
                # el keyset: el cursor resultante no localiza ninguna fila y la
                # paginacion se detiene o se repite. Falla aqui, ruidosamente,
                # en vez de emitir un cursor que no funciona.
                raise CursorInvalido(
                    f"La columna de orden '{campo.nombre}' llego sin valor; no se puede "
                    f"componer un cursor sobre una columna que admite ausencia."
                )
            valores.append(str(valor))
        return SEPARADOR.join(valores)

    def order_by(self, orden: Orden) -> str:
        """`ORDER BY` que este cursor exige, con todos sus campos y desempates."""
        return ", ".join(f"{campo.nombre} {orden.sql}" for campo in self.campos)

    def clausula(self, orden: Orden, *, prefijo: str = "cursor") -> str:
        """Condicion SQL de arranque, derivada de los mismos campos que el orden.

        Escalar:   `idcliente > %(cursor_0)s`
        Compuesto: `(f < %(cursor_0)s OR (f = %(cursor_0)s AND id < %(cursor_1)s))`

        La forma anidada es lo que hace que el desempate funcione: sin ella, dos
        filas con la misma fecha caen del mismo lado de la comparacion y una se
        repite o se pierde en el corte de pagina.
        """
        cmp = orden.comparador
        nombres = [campo.nombre for campo in self.campos]

        if len(nombres) == 1:
            return f"{nombres[0]} {cmp} %({prefijo}_0)s"

        ramas = []
        for i, nombre in enumerate(nombres):
            iguales = " AND ".join(
                f"{previo} = %({prefijo}_{j})s" for j, previo in enumerate(nombres[:i])
            )
            desigual = f"{nombre} {cmp} %({prefijo}_{i})s"
            ramas.append(f"({iguales} AND {desigual})" if iguales else desigual)
        return "(" + " OR ".join(ramas) + ")"

    def params(self, valores: Sequence[Any], *, prefijo: str = "cursor") -> dict[str, Any]:
        """Parametros que `clausula()` espera, en el mismo orden de campos."""
        return {f"{prefijo}_{i}": valor for i, valor in enumerate(valores)}

    def recortar(self, filas: Sequence[dict[str, Any]], limit: int) -> Pagina:
        """Recorta a `limit` las `limit + 1` filas pedidas y compone el cursor.

        Que vuelvan mas de `limit` es la senal de pagina siguiente. Preguntarle a
        la fuente "¿cuantas hay en total?" seria una segunda consulta agregada
        sobre cada peticion, y ademas el total cambia mientras se pagina.
        """
        hay_siguiente = len(filas) > limit
        pagina = list(filas[:limit])
        cursor = self.codificar(pagina[-1]) if (hay_siguiente and pagina) else None
        return Pagina(filas=pagina, cursor=cursor, limit=limit)
