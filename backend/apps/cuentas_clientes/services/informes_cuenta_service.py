"""Servicio de los dos listados de OT17 — ciclo de vida de la cuenta.

La garantia central de este modulo es negativa: **ninguna fila se omite porque
un catalogo no resuelva**.

Una cuenta cuyo `admin_local_id` no corresponde a ningun usuario vivo —el
propietario se dio de baja, o el identificador quedo huerfano tras una
migracion— es exactamente la anomalia que un informe de ciclo de vida debe
mostrar. Si se descartara la fila, el listado seria consistente y estaria
incompleto, y **nada avisaria**: la cuenta simplemente no estaria.

Por eso el propietario que no resuelve se presenta como `null`, que es una
afirmacion honesta —"no se sabe quien"— y no una omision silenciosa.
"""

from __future__ import annotations

from typing import Any

from core.informes.formato import a_fecha, a_iso
from core.informes.paginacion import Orden, Pagina
from core.repositories.cuentas_clientes.informes_cuenta_repository import (
    CURSOR_CUENTAS,
    CURSOR_TRANSFERENCIAS,
    ORDEN_CUENTAS,
    ORDEN_TRANSFERENCIAS,
    InformesCuentaRepository,
)


class InformesCuentaService:
    def __init__(self, repo: InformesCuentaRepository | None = None):
        self.repo = repo or InformesCuentaRepository()

    # ── L3 — Cuentas por estado ──────────────────────────────────────────────

    def cuentas_por_estado(
        self,
        *,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_CUENTAS,
        estado: str | None = None,
        tipo: str | None = None,
    ) -> Pagina:
        crudas = self.repo.cuentas(
            cursor=cursor, limit=limit, orden=orden, estado=estado, tipo=tipo
        )
        pagina = CURSOR_CUENTAS.recortar(crudas, limit)

        propietarios = self.repo.nombres_de_usuario(
            [f.get("admin_local_id") for f in pagina.filas]
        )

        return pagina._replace(
            filas=[
                {
                    "razon_social": fila.get("razon_social"),
                    "tipo": fila.get("tipo"),
                    "estado": fila.get("estado"),
                    "estado_onboarding": fila.get("estado_onboarding"),
                    "fecha_inicio_contrato": a_fecha(fila.get("fecha_inicio_contrato")),
                    # `None` cuando no resuelve. La fila **no se omite**: una
                    # cuenta sin propietario identificable es lo que hay que ver.
                    "propietario": propietarios.get(fila.get("admin_local_id")),
                }
                for fila in pagina.filas
            ]
        )

    # ── L4 — Transferencias de propiedad ─────────────────────────────────────

    def transferencias_propiedad(
        self,
        *,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_TRANSFERENCIAS,
        desde_ms: int | None = None,
        hasta_ms: int | None = None,
        idcliente: int | None = None,
    ) -> Pagina:
        crudas = self.repo.transferencias(
            cursor=cursor,
            limit=limit,
            orden=orden,
            desde_ms=desde_ms,
            hasta_ms=hasta_ms,
            idcliente=idcliente,
        )
        pagina = CURSOR_TRANSFERENCIAS.recortar(crudas, limit)

        usuarios = self.repo.nombres_de_usuario(
            [f.get("idusuarioanterior") for f in pagina.filas]
            + [f.get("idusuarionuevo") for f in pagina.filas]
        )
        razones = self.repo.razones_sociales([f.get("idcliente") for f in pagina.filas])

        return pagina._replace(
            filas=[
                {
                    "razon_social": razones.get(fila.get("idcliente")),
                    # Un propietario anterior ausente es legitimo: la primera
                    # asignacion de una cuenta no tiene "anterior".
                    "propietario_anterior": usuarios.get(fila.get("idusuarioanterior")),
                    "propietario_nuevo": usuarios.get(fila.get("idusuarionuevo")),
                    "fecha": a_iso(fila.get("fechahora")),
                }
                for fila in pagina.filas
            ]
        )
