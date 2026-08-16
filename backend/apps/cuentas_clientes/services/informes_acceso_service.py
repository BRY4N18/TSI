"""Servicio de los cuatro listados de OT18 — acceso seguro y controlado por rol.

Hace tres cosas que el repositorio no debe hacer:

1. **Resolver catalogos** — `idusuario` → nombre, `idrol` → nombre de rol.
2. **Recortar la pagina y componer el cursor**, en ese orden y sobre la fila
   cruda: el cursor se compone de columnas que la respuesta no lleva
   (`idcredencial`, `fechahorainiciosesion`), asi que si se recortara la fila
   antes, el cursor se quedaria sin los valores con los que se construye.
3. **Retirar los identificadores internos**, que se consultaron para lo
   anterior y no son dato de presentacion (`design-system.md` §8).

El punto 3 es la ultima linea de defensa de research D7 y por eso las filas se
**construyen campo a campo** en vez de copiarse y limpiarse. Una lista de campos
a excluir falla en abierto: si manana la consulta trae una columna nueva, se
publica sola. Enumerando lo que sale, una columna nueva no aparece hasta que
alguien la anada aqui a proposito.
"""

from __future__ import annotations

from typing import Any

from core.informes.formato import a_iso
from core.informes.paginacion import Orden, Pagina
from core.repositories.cuentas_clientes.informes_acceso_repository import (
    CURSOR_ACCESOS,
    CURSOR_CREDENCIALES,
    CURSOR_SESIONES,
    CURSOR_USUARIOS,
    ORDEN_ACCESOS,
    ORDEN_CREDENCIALES,
    ORDEN_SESIONES,
    ORDEN_USUARIOS,
    InformesAccesoRepository,
)


class InformesAccesoService:
    def __init__(self, repo: InformesAccesoRepository | None = None):
        self.repo = repo or InformesAccesoRepository()

    # ── L5 — Usuarios y sus roles ────────────────────────────────────────────

    def usuarios_por_rol(
        self,
        *,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_USUARIOS,
        rol: str | None = None,
        activo: bool | None = None,
    ) -> Pagina:
        """Una fila por usuario, con sus roles como lista.

        Agrupar roles por usuario **no** convierte el listado en compuesto: da
        forma a la respuesta, no calcula una metrica. La prueba de pertenencia
        del contrato habla de `GROUP BY`, `COUNT`, ratios y series temporales, y
        aqui no interviene ninguno (research D4).
        """
        idusuarios = self.repo.idusuarios_con_rol(rol) if rol is not None else None

        crudas = self.repo.usuarios(
            cursor=cursor, limit=limit, orden=orden, activo=activo, idusuarios=idusuarios
        )
        pagina = CURSOR_USUARIOS.recortar(crudas, limit)

        roles_por_usuario = self.repo.roles_de([f["idusuario"] for f in pagina.filas])

        return pagina._replace(
            filas=[
                {
                    "nombre": _nombre(fila),
                    "gmail": fila.get("gmail"),
                    "activo": fila.get("activo"),
                    # `[]` y no ausencia: un usuario sin ningun rol es la anomalia
                    # que el Administrador necesita ver, no una fila incompleta
                    # (FR-023).
                    "roles": roles_por_usuario.get(fila["idusuario"], []),
                }
                for fila in pagina.filas
            ]
        )

    def roles_disponibles(self) -> list[str]:
        return self.repo.roles_disponibles()

    # ── L6 — Sesiones abiertas ───────────────────────────────────────────────

    def sesiones_activas(
        self,
        *,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_SESIONES,
        idusuario: int | None = None,
    ) -> Pagina:
        crudas = self.repo.sesiones_activas(
            cursor=cursor, limit=limit, orden=orden, idusuario=idusuario
        )
        pagina = CURSOR_SESIONES.recortar(crudas, limit)
        usuarios = self.repo.nombres_de_usuario([f["idusuario"] for f in pagina.filas])

        return pagina._replace(
            filas=[
                {
                    "usuario": usuarios.get(fila["idusuario"], {}).get("nombre", ""),
                    "navegador": fila.get("navegador"),
                    "fecha_inicio": a_iso(fila.get("fechahorainiciosesion")),
                }
                for fila in pagina.filas
            ]
        )

    # ── L7 — Credenciales temporales pendientes ──────────────────────────────

    def credenciales_temporales(
        self,
        *,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_CREDENCIALES,
    ) -> Pagina:
        crudas = self.repo.credenciales_temporales(cursor=cursor, limit=limit, orden=orden)
        pagina = CURSOR_CREDENCIALES.recortar(crudas, limit)
        usuarios = self.repo.nombres_de_usuario([f["idusuario"] for f in pagina.filas])

        return pagina._replace(
            filas=[
                {
                    "usuario": usuarios.get(fila["idusuario"], {}).get("nombre", ""),
                    "gmail": usuarios.get(fila["idusuario"], {}).get("gmail"),
                    # Ausente se presenta ausente: una credencial sin fecha de
                    # solicitud no lleva "hace 56 anios" esperando (FR-021).
                    "fecha_solicitud_cambio": a_iso(fila.get("fecha_actualizacion")),
                }
                for fila in pagina.filas
            ]
        )

    # ── L8 — Accesos tecnicos de infraestructura ─────────────────────────────

    def accesos_tecnicos(
        self,
        *,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_ACCESOS,
    ) -> Pagina:
        crudas = self.repo.accesos_tecnicos(cursor=cursor, limit=limit, orden=orden)
        pagina = CURSOR_ACCESOS.recortar(crudas, limit)

        roles = self.repo.roles_de_acceso_tecnico(
            [f["idusuarioservidor"] for f in pagina.filas]
        )
        usuarios = self.repo.nombres_de_usuario([f["idusuario"] for f in pagina.filas])

        return pagina._replace(
            filas=[
                {
                    "usuario": usuarios.get(fila["idusuario"], {}).get("nombre", ""),
                    "usuario_servidor": fila.get("usuario"),
                    "roles_servidor": roles.get(fila["idusuarioservidor"], {}).get(
                        "roles_servidor", []
                    ),
                    # Una cuenta tecnica sin mapeo a rol de negocio es una cuenta
                    # con acceso que nadie sabe a que habilita: `[]` la deja
                    # visible en el listado en vez de esconderla.
                    "roles_negocio": roles.get(fila["idusuarioservidor"], {}).get(
                        "roles_negocio", []
                    ),
                }
                for fila in pagina.filas
            ]
        )


def _nombre(fila: dict[str, Any]) -> str:
    partes = [fila.get("nombres"), fila.get("apellidos")]
    return " ".join(p for p in partes if p).strip()
