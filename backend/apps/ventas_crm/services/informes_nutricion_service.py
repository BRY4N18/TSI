"""Servicio de la nutrición del prospecto — L3 demos activas y L4 notificaciones.

Aquí vive el **segundo paso** del filtro de research D3, y la razón de que el
reloj sea inyectable no es solo la de siempre (poder probarlo): es que el
prefiltro y el cálculo **deben usar el mismo instante**.

Si uno usara el reloj del broker de Pinot y el otro el del proceso, una demo
podría aparecer con «0 días restantes» habiendo sido ya descartada, o al revés —
mostrarse como vigente una que el prefiltro dejó pasar y el refinamiento debería
haber quitado. Un solo `ahora` para los dos elimina la clase entera de fallo.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from apps.ventas_crm.demo_tokens import parse_iso_expiracion
from core.informes.acotamiento import Acotamiento
from core.informes.formato import a_iso
from core.informes.paginacion import Orden, Pagina
from core.repositories.ventas_crm.informes_nutricion_repository import (
    CURSOR_DEMOS,
    CURSOR_NOTIFICACIONES,
    ORDEN_DEMOS,
    ORDEN_NOTIFICACIONES,
    InformesNutricionRepository,
)

SEGUNDOS_POR_DIA = 86_400


def _ahora_utc() -> datetime:
    return datetime.now(timezone.utc)


class InformesNutricionService:
    def __init__(
        self,
        repo: InformesNutricionRepository | None = None,
        ahora: Callable[[], datetime] | None = None,
    ):
        self.repo = repo or InformesNutricionRepository()
        #: Se inyecta como **función** para que cada petición lea el instante al
        #: atenderse. Un valor fijado en el constructor envejecería con el
        #: proceso, y aquí eso significaría demos expiradas presentadas como
        #: vigentes.
        #:
        #: El defecto se resuelve aquí y **no** como valor por defecto del
        #: parámetro: aquél se evalúa al definir la clase, así que quedaría
        #: atado a la función original y no podría sustituirse. La vista
        #: construye el servicio ella misma, y sin esto no habría forma de fijar
        #: el instante en una prueba de API.
        self.ahora = ahora or (lambda: _ahora_utc())

    # ── L3 — Demos activas ───────────────────────────────────────────────────

    def demos_activas(
        self,
        *,
        acotamiento: Acotamiento,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_DEMOS,
    ) -> Pagina:
        """Demos vigentes, resueltas en dos pasos con **un solo instante**.

        El paginado se compone sobre las filas **crudas** —las que el prefiltro
        devolvió— y no sobre las refinadas: el cursor tiene que apuntar a una
        fila que la consulta pueda volver a encontrar. Si se compusiera tras
        descartar, la página siguiente arrancaría después de una fila que el
        refinamiento ya quitó, y saltaría demos vigentes.
        """
        ahora = self.ahora()

        crudas = self.repo.demos_con_expiracion_desde(
            prefijo_hoy=ahora.strftime("%Y-%m-%d"),
            cursor=cursor,
            limit=limit,
            orden=orden,
            titular=acotamiento.titular,
        )
        pagina = CURSOR_DEMOS.recortar(crudas, limit)

        ejecutivos = self.repo.nombres_de_usuario(
            [f.get("idusuario") for f in pagina.filas]
        )

        filas = []
        for cruda in pagina.filas:
            expira = parse_iso_expiracion(cruda.get("demo_expiracion"))
            # Sin fecha o no interpretable: **no es una demo activa**. No se
            # supone vigente ni se inventa una expiración.
            if expira is None or expira <= ahora:
                continue
            filas.append(
                {
                    "empresa": cruda.get("empresa"),
                    "nombre_contacto": _nombre(cruda),
                    "ejecutivo": ejecutivos.get(cruda.get("idusuario")),
                    # Se devuelve normalizada, no como vino: el consumidor no
                    # tiene por qué lidiar con los tres formatos del origen.
                    "expiracion": expira.isoformat(),
                    "dias_restantes": self._dias_restantes(ahora, expira),
                }
            )

        return pagina._replace(filas=filas)

    @staticmethod
    def _dias_restantes(ahora: datetime, expira: datetime) -> int:
        """Días completos que faltan, redondeando hacia arriba.

        Una demo que vence en seis horas tiene **1 día restante**, no 0: un `0`
        se lee como «ya venció», que es justo lo contrario. La demo está viva
        hasta que expira.
        """
        segundos = (expira - ahora).total_seconds()
        return max(1, -(-int(segundos) // SEGUNDOS_POR_DIA))

    # ── L4 — Notificaciones enviadas ─────────────────────────────────────────

    def notificaciones_enviadas(
        self,
        *,
        acotamiento: Acotamiento,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_NOTIFICACIONES,
        desde_ms: int | None = None,
        hasta_ms: int | None = None,
        regla: str | None = None,
        canal: str | None = None,
    ) -> Pagina:
        crudas = self.repo.notificaciones(
            cursor=cursor,
            limit=limit,
            orden=orden,
            titular=acotamiento.titular,
            desde_ms=desde_ms,
            hasta_ms=hasta_ms,
            regla=regla,
            canal=canal,
        )
        pagina = CURSOR_NOTIFICACIONES.recortar(crudas, limit)

        empresas = self.repo.empresas_de_prospecto(
            [f.get("id_prospecto") for f in pagina.filas]
        )
        usuarios = self.repo.nombres_de_usuario(
            [f.get("idusuariogerentenotificado") for f in pagina.filas]
        )

        return pagina._replace(
            filas=[
                {
                    "empresa": empresas.get(fila.get("id_prospecto")),
                    "ejecutivo_notificado": usuarios.get(
                        fila.get("idusuariogerentenotificado")
                    ),
                    "regla_disparada": fila.get("regladisparada"),
                    "canal": fila.get("canal"),
                    "fecha": a_iso(fila.get("fechahoranotificacion")),
                }
                for fila in pagina.filas
            ]
        )


def _nombre(fila: dict[str, Any]) -> str:
    partes = [fila.get("nombres"), fila.get("apellidos")]
    return " ".join(p for p in partes if p).strip()
