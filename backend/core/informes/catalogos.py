"""Catálogos que pueblan los desplegables de los filtros de los listados.

⚠️ **Un catálogo es un control de acceso, aunque no lo parezca**
-----------------------------------------------------------------
Los filtros de los listados pedían identificadores numéricos escritos a mano
—«Cuenta (id)», «Partner (id)»— mientras las tablas mostraban solo nombres: no
había forma de averiguar el número desde la propia pantalla. Sustituirlos por
desplegables exige publicar la lista de opciones, y ahí aparece un riesgo que el
campo numérico no tenía.

Una lista de partners o de cuentas **no es una fila del listado, es metadato**, y
el acotamiento que protege las filas no la cubre por sí solo. Publicarla entera
diría quién más opera en la plataforma a quien solo debería verse a sí mismo — y
lo diría con su listado devolviendo lo de siempre, sin ningún síntoma.

Por eso todos los métodos de aquí reciben **explícitamente** el conjunto al que
acotar, con la misma convención que el resto del sistema:

* `None` → sin acotar (rol interno): catálogo completo;
* conjunto **vacío** → acotado a nada: **cero opciones**, nunca el catálogo
  completo. Es la lectura peligrosa que un `if permitidos:` haría al revés.
"""

from __future__ import annotations

from typing import Any, Iterable

from core.pinot.client import PinotClient

#: Tope de seguridad de las consultas de catálogo. No es paginación: un catálogo
#: que se acerque a esta cifra ya no cabe en un desplegable y el filtro tendría
#: que ser una búsqueda, no una lista.
TOPE_CATALOGO = 10_000


def opciones_catalogo(
    filas: Iterable[dict], campo_id: str, campo_nombre: str
) -> list[dict[str, Any]]:
    """`{id, nombre}` ordenado por nombre, saltando lo que no se puede nombrar.

    Una opción sin nombre se pintaría como una entrada en blanco que el operador
    puede seleccionar sin saber qué elige: mejor no ofrecerla.
    """
    opciones = [
        {"id": f[campo_id], "nombre": f[campo_nombre]}
        for f in filas
        if f.get(campo_id) is not None and f.get(campo_nombre)
    ]
    return sorted(opciones, key=lambda o: str(o["nombre"]))


def desambiguar_homonimos(opciones: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Marca las opciones que **comparten nombre** con su identificador.

    Dos entradas con el mismo texto son indistinguibles al elegir: quien
    selecciona una no sabe cuál seleccionó, y el listado se acota a un
    subconjunto sin ninguna explicación a la vista.

    Se cualifica **solo cuando hay ambigüedad**: añadir el id a todas sería ruido
    en el caso normal, que es el que no necesita ayuda.
    """
    repetidos: dict[str, int] = {}
    for opcion in opciones:
        nombre = str(opcion["nombre"])
        repetidos[nombre] = repetidos.get(nombre, 0) + 1

    return [
        {
            "id": o["id"],
            "nombre": (
                f"{o['nombre']} (#{o['id']})"
                if repetidos[str(o["nombre"])] > 1
                else o["nombre"]
            ),
        }
        for o in opciones
    ]


class CatalogosFiltrosRepository:
    """Solo lectura. Los catálogos comunes a varios departamentos."""

    def __init__(self, pinot: PinotClient | None = None):
        self.pinot = pinot or PinotClient()

    def partners(self, permitidos: frozenset[int] | None) -> list[dict[str, Any]]:
        if permitidos is not None and not permitidos:
            return []
        if permitidos is None:
            filas = self.pinot.query(
                "SELECT idpartner, nombrepartner FROM Dim_Partner LIMIT %(limit)s",
                {"limit": TOPE_CATALOGO},
            )
        else:
            filas = self.pinot.query(
                "SELECT idpartner, nombrepartner FROM Dim_Partner "
                "WHERE idpartner IN %(ids)s LIMIT %(limit)s",
                {"ids": sorted(permitidos), "limit": TOPE_CATALOGO},
            )
        return desambiguar_homonimos(
            opciones_catalogo(filas, "idpartner", "nombrepartner")
        )

    def clientes(self, permitidos: frozenset[int] | None) -> list[dict[str, Any]]:
        if permitidos is not None and not permitidos:
            return []
        if permitidos is None:
            filas = self.pinot.query(
                "SELECT idcliente, razon_social FROM Dim_Cliente LIMIT %(limit)s",
                {"limit": TOPE_CATALOGO},
            )
        else:
            filas = self.pinot.query(
                "SELECT idcliente, razon_social FROM Dim_Cliente "
                "WHERE idcliente IN %(ids)s LIMIT %(limit)s",
                {"ids": sorted(permitidos), "limit": TOPE_CATALOGO},
            )
        return desambiguar_homonimos(
            opciones_catalogo(filas, "idcliente", "razon_social")
        )

    def servicios(self) -> list[dict[str, Any]]:
        """Catálogo de referencia del sistema: no dice nada de nadie."""
        filas = self.pinot.query(
            "SELECT id_servicio, nombre FROM Dim_Servicio LIMIT %(limit)s",
            {"limit": TOPE_CATALOGO},
        )
        return desambiguar_homonimos(opciones_catalogo(filas, "id_servicio", "nombre"))

    def usuarios(self, permitidos: frozenset[int] | None) -> list[dict[str, Any]]:
        """Usuarios por nombre y apellido.

        ⚠️ **Sin correo ni teléfono.** El desplegable necesita distinguir
        personas, no publicar cómo contactarlas: enumerar el directorio con sus
        correos es un dato de contacto masivo que ningún filtro justifica. Dos
        homónimos se separan con su identificador, no con su correo.
        """
        if permitidos is not None and not permitidos:
            return []
        if permitidos is None:
            filas = self.pinot.query(
                "SELECT idusuario, nombres, apellidos FROM Dim_Usuarios "
                "WHERE activo = true LIMIT %(limit)s",
                {"limit": TOPE_CATALOGO},
            )
        else:
            filas = self.pinot.query(
                "SELECT idusuario, nombres, apellidos FROM Dim_Usuarios "
                "WHERE idusuario IN %(ids)s AND activo = true LIMIT %(limit)s",
                {"ids": sorted(permitidos), "limit": TOPE_CATALOGO},
            )
        con_nombre = [
            {
                "idusuario": f.get("idusuario"),
                "nombre": " ".join(
                    p for p in (f.get("nombres"), f.get("apellidos")) if p
                ).strip(),
            }
            for f in filas
        ]
        return desambiguar_homonimos(
            opciones_catalogo(con_nombre, "idusuario", "nombre")
        )

    def prospectos(self, permitidos: frozenset[int] | None) -> list[dict[str, Any]]:
        """Prospectos por **empresa**, no por persona de contacto.

        ⚠️ Sin nombre, correo ni teléfono del contacto. Este es el departamento
        con más dato personal del sistema, y un desplegable solo necesita
        distinguir oportunidades comerciales, no publicar a quién llamar.
        """
        if permitidos is not None and not permitidos:
            return []
        if permitidos is None:
            filas = self.pinot.query(
                "SELECT idprospecto, empresa FROM Dim_Prospecto LIMIT %(limit)s",
                {"limit": TOPE_CATALOGO},
            )
        else:
            filas = self.pinot.query(
                "SELECT idprospecto, empresa FROM Dim_Prospecto "
                "WHERE idprospecto IN %(ids)s LIMIT %(limit)s",
                {"ids": sorted(permitidos), "limit": TOPE_CATALOGO},
            )
        return desambiguar_homonimos(
            opciones_catalogo(filas, "idprospecto", "empresa")
        )

    def usuarios_con_rol(self, roles: Iterable[str]) -> list[dict[str, Any]]:
        """Usuarios que llevan **alguno** de esos roles.

        ⚠️ **No es lo mismo que el directorio entero.** Un filtro «Agente» que
        ofrezca las treinta y una personas del sistema —incluidas las unidades
        registradas como usuario— no ayuda a elegir y sugiere que cualquiera de
        ellas podría atender un ticket. El desplegable tiene que ofrecer a quien
        de verdad puede aparecer en esa columna.

        Un rol sin nadie devuelve lista vacía, no el directorio: es la misma
        distinción entre «acotado a nada» y «sin acotar» de todo este módulo.
        """
        from core.repositories.cuentas_clientes.role_repository import RoleRepository

        repo = RoleRepository(pinot=self.pinot)
        ids: set[int] = set()
        for rol in roles:
            ids.update(repo.list_user_ids_for_role(rol))
        return self.usuarios(frozenset(ids))

    def origenes_despacho(self) -> list[dict[str, Any]]:
        """Catálogo de referencia: cómo se originó la asignación."""
        filas = self.pinot.query(
            "SELECT idorigendespacho, origendespacho FROM Dim_OrigenDespacho "
            "LIMIT %(limit)s",
            {"limit": TOPE_CATALOGO},
        )
        return desambiguar_homonimos(
            opciones_catalogo(filas, "idorigendespacho", "origendespacho")
        )

    def unidades(self) -> list[dict[str, Any]]:
        """Unidades de emergencia, cualificadas con su placa.

        ⚠️ La placa **no es decoración**: hay unidades con el mismo nombre
        («Humo», «AlzaCarros»), y en el origen incluso placas repetidas. Sin ella
        el desplegable ofrecería entradas indistinguibles.

        Sin coordenadas ni contacto del proveedor: son dato sensible con su
        propio control, y un desplegable no los necesita.
        """
        filas = self.pinot.query(
            "SELECT idunidademergencia, unidademergencia, placa "
            "FROM Dim_UnidadEmergencia LIMIT %(limit)s",
            {"limit": TOPE_CATALOGO},
        )
        con_placa = [
            {
                "idunidademergencia": f.get("idunidademergencia"),
                "nombre": (
                    f"{f.get('unidademergencia')} ({f.get('placa')})"
                    if f.get("placa")
                    else f.get("unidademergencia")
                ),
            }
            for f in filas
        ]
        return desambiguar_homonimos(
            opciones_catalogo(con_placa, "idunidademergencia", "nombre")
        )

    def regiones_operativas(self) -> list[dict[str, Any]]:
        filas = self.pinot.query(
            "SELECT idregionoperativa, nombreregion FROM Dim_RegionOperativa "
            "LIMIT %(limit)s",
            {"limit": TOPE_CATALOGO},
        )
        return desambiguar_homonimos(
            opciones_catalogo(filas, "idregionoperativa", "nombreregion")
        )
