"""Consultas de los cuatro listados de OT18 — acceso seguro y controlado por rol.

L5 usuarios y sus roles · L6 sesiones abiertas · L7 credenciales temporales ·
L8 accesos tecnicos de infraestructura.

⚠️ Prohibido `SELECT *` en este fichero (research D7)
-----------------------------------------------------
Tres de las cuatro tablas principales guardan material que **no puede salir en
ninguna respuesta**:

| Tabla | Columna prohibida |
|---|---|
| `Fact_Session` | `token` |
| `Dim_Credencial` | `contrasena` |
| `Dim_UsuariosServidor` | `contrasena` |

Por eso cada consulta **enumera sus columnas**. No es estilo: un `SELECT *` hace
que la credencial viaje hasta la capa de vista, donde basta que alguien serialice
la fila entera —o que una prueba vuelque la respuesta— para publicarla. Es una
fuga que no produce ningun error y que nadie detecta mirando el codigo de la
vista, porque el fallo esta aqui.

Los identificadores tampoco son dato de presentacion
----------------------------------------------------
`idusuario`, `idcredencial` y compania **si** se consultan: hacen falta para
componer el cursor y para resolver los catalogos. Lo que no hacen es llegar a la
respuesta — eso lo recorta el servicio (`design-system.md` §8).

Sin JOIN
--------
Pinot no los admite, asi que los catalogos se resuelven con una segunda consulta
y una union en memoria, el patron de `registro_repository._nombres_calles()`.
Traducir una etiqueta no convierte el listado en compuesto: no hay `GROUP BY`,
`COUNT` ni ratio (contrato comun §1).
"""

from __future__ import annotations

from typing import Any, Sequence

from core.informes.paginacion import ASC, DESC, CampoCursor, Cursor, Orden
from core.pinot.client import PinotClient
from core.repositories.cuentas_clientes.credential_repository import (
    ESTADO_CREDENCIAL_CAMBIO_PASSWORD,
)
from core.repositories.cuentas_clientes.session_repository import ESTADO_SESION_ACTIVA

# ── Correccion sobre `data-model.md` §2, L6 y L7 ─────────────────────────────
#
# El data-model declaraba dos literales que **no existen en el sistema**:
# `estadosession = 'Activa'` y `estadocredencial = 'Temporal'`. Los valores
# canonicos son `'Inicio sesion'` (`session_repository`) y `'Cambio contrasena'`
# (`credential_repository`).
#
# Implementarlo al pie de la letra habria dejado los dos listados **vacios para
# siempre**, respondiendo `200` con `data: []` — sin error, sin aviso y sin nada
# que distinga "no hay sesiones abiertas" de "el filtro no encaja con ningun
# valor real". Es exactamente el fallo que ya ocurrio en este proyecto y que
# documenta `credential_repository.py:14`: un seed escribia "ACTIVA" mientras el
# codigo comparaba contra "Activo", y eso invalidaba la credencial de todos los
# usuarios sembrados.
#
# Por eso los estados **se importan de su modulo canonico** en vez de repetirse
# como literal aqui: un literal nuevo es un desajuste futuro esperando a ocurrir.

# ── Declaracion de los cuatro listados ───────────────────────────────────────
# El cursor y el ORDER BY salen del MISMO objeto para que no puedan divergir.

CURSOR_USUARIOS = Cursor(CampoCursor("idusuario"))
ORDEN_USUARIOS = ASC  # el listado se lee como un padron: del primero al ultimo

CURSOR_SESIONES = Cursor(CampoCursor("fechahorainiciosesion"), CampoCursor("idsession"))
ORDEN_SESIONES = DESC  # lo mas reciente primero: la sesion sospechosa es la nueva

# `data-model.md` ordena L7 por `fecha_solicitud_cambio`. Esa columna existe en
# el esquema pero **ningun escritor la rellena**: `credential_repository` sella
# `fecha_actualizacion` en cada transicion a "Cambio contrasena" y nada mas. Un
# cursor sobre una columna siempre ausente no localiza ninguna fila, asi que la
# segunda pagina del listado habria fallado — y solo con datos suficientes para
# que hubiera segunda pagina, que es como este defecto llega a produccion.
#
# Se ordena por la columna que **si** lleva el dato y significa lo mismo: el
# instante en que la credencial paso a pendiente de cambio. El nombre del campo
# en la respuesta no cambia; el contrato se respeta.
CURSOR_CREDENCIALES = Cursor(
    CampoCursor("fecha_actualizacion"), CampoCursor("idcredencial")
)
ORDEN_CREDENCIALES = ASC  # bandeja: lo mas antiguo primero, lleva mas esperando

CURSOR_ACCESOS = Cursor(CampoCursor("idusuarioservidor"))
ORDEN_ACCESOS = ASC


class InformesAccesoRepository:
    """Solo lectura. Ningun metodo escribe ni publica en Kafka."""

    def __init__(self, pinot: PinotClient | None = None):
        self.pinot = pinot or PinotClient()

    # ── L5 — Usuarios y sus roles ────────────────────────────────────────────

    def usuarios(
        self,
        *,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_USUARIOS,
        activo: bool | None = None,
        idusuarios: Sequence[int] | None = None,
    ) -> list[dict[str, Any]]:
        """Pagina sobre `Dim_Usuarios`, **no** sobre `Dim_Usuario_Rol` (research D4).

        Paginar la tabla de relacion partiria a un usuario de dos roles en dos
        filas que ademas pueden caer en paginas distintas — lo que el escenario 2
        de la User Story 1 prohibe. Paginando el usuario, la unidad de paginacion
        es lo que el consumidor cuenta, el cursor es escalar porque `idusuario`
        es clave unica, y **FR-023 sale gratis**: un usuario sin ningun rol
        aparece de forma natural, que es justo la anomalia a vigilar.

        `idusuarios` acota a un conjunto ya resuelto (filtro por rol): invierte el
        orden de consulta, pero la unidad de paginacion sigue siendo el usuario.
        """
        condiciones: list[str] = []
        params: dict[str, Any] = {"limit": limit + 1}

        if activo is not None:
            condiciones.append("activo = %(activo)s")
            params["activo"] = activo
        if idusuarios is not None:
            if not idusuarios:
                return []  # conjunto vacio: ninguna fila, sin ir a Pinot
            condiciones.append("idusuario IN %(idusuarios)s")
            params["idusuarios"] = list(idusuarios)
        if cursor:
            condiciones.append(CURSOR_USUARIOS.clausula(orden))
            params.update(CURSOR_USUARIOS.params(cursor))

        sql = (
            "SELECT idusuario, nombres, apellidos, gmail, activo FROM Dim_Usuarios"
            f"{_where(condiciones)} "
            f"ORDER BY {CURSOR_USUARIOS.order_by(orden)} LIMIT %(limit)s"
        )
        return self.pinot.query(sql, params)

    def roles_de(self, idusuarios: Sequence[int]) -> dict[int, list[str]]:
        """Roles activos de los usuarios **de la pagina ya resuelta**.

        Se consulta despues de paginar, no antes: asi la segunda consulta es
        acotada (50 usuarios) en vez de recorrer la relacion entera.
        """
        if not idusuarios:
            return {}

        relaciones = self.pinot.query(
            "SELECT idusuario, idrol FROM Dim_Usuario_Rol "
            "WHERE idusuario IN %(idusuarios)s AND activo = true LIMIT %(limit)s",
            {"idusuarios": list(idusuarios), "limit": len(idusuarios) * 50},
        )
        if not relaciones:
            return {}

        nombres = self._nombres_de_rol({r["idrol"] for r in relaciones})

        agrupado: dict[int, list[str]] = {}
        for relacion in relaciones:
            nombre = nombres.get(relacion["idrol"])
            if nombre is None:
                # Un rol que no resuelve no se inventa ni se rellena: se omite.
                # Inventarlo mostraria un rol que nadie asigno.
                continue
            agrupado.setdefault(relacion["idusuario"], []).append(nombre)

        return {idusuario: sorted(roles) for idusuario, roles in agrupado.items()}

    def idusuarios_con_rol(self, rol: str) -> list[int]:
        """Usuarios que ejercen un rol, por su **nombre** — no por `idrol`.

        El consumidor filtra por 'Administrador', no por un numero: exigirle el
        identificador seria pedirle que conozca el catalogo interno, que es lo
        mismo que `design-system.md` §8 prohibe mostrar.
        """
        filas = self.pinot.query(
            "SELECT idrol FROM Dim_Rol WHERE rol = %(rol)s AND activo = true LIMIT 10",
            {"rol": rol},
        )
        if not filas:
            return []

        idroles = [f["idrol"] for f in filas]
        relaciones = self.pinot.query(
            "SELECT idusuario, idrol FROM Dim_Usuario_Rol "
            "WHERE idrol IN %(idroles)s AND activo = true LIMIT 10000",
            {"idroles": idroles},
        )
        return sorted({r["idusuario"] for r in relaciones})

    def roles_disponibles(self) -> list[str]:
        """Nombres de rol validos, para que un filtro invalido pueda nombrarlos."""
        filas = self.pinot.query(
            "SELECT idrol, rol FROM Dim_Rol WHERE activo = true LIMIT 1000"
        )
        return sorted({f["rol"] for f in filas if f.get("rol")})

    def _nombres_de_rol(self, idroles: set[int]) -> dict[int, str]:
        if not idroles:
            return {}
        filas = self.pinot.query(
            "SELECT idrol, rol FROM Dim_Rol WHERE idrol IN %(idroles)s LIMIT %(limit)s",
            {"idroles": sorted(idroles), "limit": len(idroles)},
        )
        return {f["idrol"]: f["rol"] for f in filas if f.get("rol")}

    # ── L6 — Sesiones abiertas ───────────────────────────────────────────────

    def sesiones_activas(
        self,
        *,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_SESIONES,
        idusuario: int | None = None,
    ) -> list[dict[str, Any]]:
        """⚠️ Columnas enumeradas: `token` no aparece en la lista y no puede salir."""
        condiciones = ["estadosession = %(estado)s"]
        params: dict[str, Any] = {"estado": ESTADO_SESION_ACTIVA, "limit": limit + 1}

        if idusuario is not None:
            condiciones.append("idusuario = %(idusuario)s")
            params["idusuario"] = idusuario
        if cursor:
            condiciones.append(CURSOR_SESIONES.clausula(orden))
            params.update(CURSOR_SESIONES.params(cursor))

        sql = (
            "SELECT idsession, idusuario, navegador, fechahorainiciosesion FROM Fact_Session"
            f"{_where(condiciones)} "
            f"ORDER BY {CURSOR_SESIONES.order_by(orden)} LIMIT %(limit)s"
        )
        return self.pinot.query(sql, params)

    # ── L7 — Credenciales temporales pendientes ──────────────────────────────

    def credenciales_temporales(
        self,
        *,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_CREDENCIALES,
    ) -> list[dict[str, Any]]:
        """⚠️ Columnas enumeradas: `contrasena` no aparece y no puede salir."""
        condiciones = ["estadocredencial = %(estado)s"]
        params: dict[str, Any] = {
            "estado": ESTADO_CREDENCIAL_CAMBIO_PASSWORD,
            "limit": limit + 1,
        }

        if cursor:
            condiciones.append(CURSOR_CREDENCIALES.clausula(orden))
            params.update(CURSOR_CREDENCIALES.params(cursor))

        sql = (
            "SELECT idcredencial, idusuario, fecha_actualizacion FROM Dim_Credencial"
            f"{_where(condiciones)} "
            f"ORDER BY {CURSOR_CREDENCIALES.order_by(orden)} LIMIT %(limit)s"
        )
        return self.pinot.query(sql, params)

    # ── L8 — Accesos tecnicos de infraestructura ─────────────────────────────

    def accesos_tecnicos(
        self,
        *,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_ACCESOS,
    ) -> list[dict[str, Any]]:
        """⚠️ Columnas enumeradas: `contrasena` de servidor no aparece y no sale."""
        condiciones = ["activo = true"]
        params: dict[str, Any] = {"limit": limit + 1}

        if cursor:
            condiciones.append(CURSOR_ACCESOS.clausula(orden))
            params.update(CURSOR_ACCESOS.params(cursor))

        sql = (
            "SELECT idusuarioservidor, idusuario, usuario FROM Dim_UsuariosServidor"
            f"{_where(condiciones)} "
            f"ORDER BY {CURSOR_ACCESOS.order_by(orden)} LIMIT %(limit)s"
        )
        return self.pinot.query(sql, params)

    def roles_de_acceso_tecnico(
        self, idusuariosservidor: Sequence[int]
    ) -> dict[int, dict[str, list[str]]]:
        """Resuelve la cadena de cuatro tablas de L8, en tres consultas acotadas.

        `Dim_UsuariosServidorRolesServidor` → `Dim_RolesServidor` (rol tecnico)
        → `Dim_RolesServidorRoles` → `Dim_Rol` (rol de negocio).

        El mapeo a rol de negocio es lo que hace util el listado: responde "quien
        tiene shell en los servidores y que le habilita eso en el negocio", que
        es la pregunta de CU-O08. Sin el segundo tramo solo se veria una lista de
        cuentas de sistema.
        """
        if not idusuariosservidor:
            return {}

        asignaciones = self.pinot.query(
            "SELECT idusuarioservidor, idrolservidor FROM Dim_UsuariosServidorRolesServidor "
            "WHERE idusuarioservidor IN %(ids)s AND activo = true LIMIT %(limit)s",
            {"ids": list(idusuariosservidor), "limit": len(idusuariosservidor) * 50},
        )
        if not asignaciones:
            return {}

        idroles_servidor = sorted({a["idrolservidor"] for a in asignaciones})

        nombres_servidor = {
            f["idrolservidor"]: f["rolservidor"]
            for f in self.pinot.query(
                "SELECT idrolservidor, rolservidor FROM Dim_RolesServidor "
                "WHERE idrolservidor IN %(ids)s LIMIT %(limit)s",
                {"ids": idroles_servidor, "limit": len(idroles_servidor)},
            )
            if f.get("rolservidor")
        }

        mapeos = self.pinot.query(
            "SELECT idrolservidor, idrol FROM Dim_RolesServidorRoles "
            "WHERE idrolservidor IN %(ids)s AND activo = true LIMIT %(limit)s",
            {"ids": idroles_servidor, "limit": len(idroles_servidor) * 50},
        )
        nombres_negocio = self._nombres_de_rol({m["idrol"] for m in mapeos})

        negocio_por_rol_servidor: dict[int, set[str]] = {}
        for mapeo in mapeos:
            nombre = nombres_negocio.get(mapeo["idrol"])
            if nombre:
                negocio_por_rol_servidor.setdefault(mapeo["idrolservidor"], set()).add(nombre)

        resultado: dict[int, dict[str, set[str]]] = {}
        for asignacion in asignaciones:
            destino = resultado.setdefault(
                asignacion["idusuarioservidor"], {"servidor": set(), "negocio": set()}
            )
            idrol_servidor = asignacion["idrolservidor"]
            nombre_servidor = nombres_servidor.get(idrol_servidor)
            if nombre_servidor:
                destino["servidor"].add(nombre_servidor)
            destino["negocio"] |= negocio_por_rol_servidor.get(idrol_servidor, set())

        return {
            idusuarioservidor: {
                "roles_servidor": sorted(roles["servidor"]),
                "roles_negocio": sorted(roles["negocio"]),
            }
            for idusuarioservidor, roles in resultado.items()
        }

    # ── Catalogo compartido por los cuatro listados ──────────────────────────

    def nombres_de_usuario(self, idusuarios: Sequence[int]) -> dict[int, dict[str, Any]]:
        """Resuelve `idusuario` → nombre y correo, para no mostrar el numero."""
        ids = sorted({i for i in idusuarios if i is not None})
        if not ids:
            return {}

        filas = self.pinot.query(
            "SELECT idusuario, nombres, apellidos, gmail FROM Dim_Usuarios "
            "WHERE idusuario IN %(ids)s LIMIT %(limit)s",
            {"ids": ids, "limit": len(ids)},
        )
        return {
            f["idusuario"]: {
                "nombre": nombre_completo(f),
                "gmail": f.get("gmail"),
            }
            for f in filas
        }


def nombre_completo(fila: dict[str, Any]) -> str:
    """Nombre presentable a partir de nombres y apellidos.

    Si ambos faltan —centinela coercionado a `None`— se devuelve cadena vacia y
    **no** el identificador: mostrar el numero seria exactamente lo que
    `design-system.md` §8 prohibe, y ocurriria justo en la fila mas anomala.
    """
    partes = [fila.get("nombres"), fila.get("apellidos")]
    return " ".join(p for p in partes if p).strip()


def _where(condiciones: Sequence[str]) -> str:
    return f" WHERE {' AND '.join(condiciones)}" if condiciones else ""
