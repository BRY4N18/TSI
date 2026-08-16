"""Pertenencia de un usuario a una cuenta cliente.

`Dim_Usuario_Cliente` es la tabla de vinculos, y hasta 2026-08-15 **ningun
codigo de produccion escribia en ella**: la tabla y su topic estaban declarados
en `database/tablas.json`, pero `settings.KAFKA_TOPICS` no tenia la entrada, asi
que no habia forma de publicar.

La consecuencia era que toda la pertenencia se resolvia por el respaldo
—`Dim_Cliente.admin_local_id`—, y de una organizacion con cinco usuarios **solo
uno** podia consultar los datos de su cuenta: sus tickets, sus expedientes y los
accidentes de sus zonas contratadas. Los demas recibian `403`.

Resuelto por la decision #23: **cualquier usuario vinculado ve los datos de su
organizacion**. `vincular()` es lo que faltaba.

El respaldo por `admin_local_id` **se conserva**: las cuentas creadas antes de
este cambio no tienen filas de vinculo, y quitarlo dejaria sin acceso a sus
administradores. No hace falta migrar nada.
"""

from __future__ import annotations

from typing import Any

from django.conf import settings

from core.pinot.client import PinotClient
from core.pinot.tiempo import ahora_ms
from core.repositories.cuentas_clientes.cliente_repository import ClienteRepository
from core.repositories.cuentas_clientes.kafka_writer import KafkaWriter
from core.repositories.cuentas_clientes.user_repository import UserRepository


class CuentaUsuarioRepository:
    """Resuelve —y ahora tambien escribe— la pertenencia a una cuenta."""

    TOPIC = settings.KAFKA_TOPICS["usuario_cliente"]

    def __init__(
        self,
        pinot: PinotClient | None = None,
        user_repo: UserRepository | None = None,
        cliente_repo: ClienteRepository | None = None,
        kafka: KafkaWriter | None = None,
    ):
        pinot = pinot or PinotClient()
        self.pinot = pinot
        self.user_repo = user_repo or UserRepository(pinot=pinot)
        self.cliente_repo = cliente_repo or ClienteRepository(pinot=pinot)
        self.kafka = kafka or KafkaWriter()

    def vincular(self, user_id: int, cliente_id: int) -> dict[str, Any]:
        """Da de alta la pertenencia de un usuario a una cuenta.

        Es idempotente por diseno de la tabla: `Dim_Usuario_Cliente` es upsert
        por la pareja usuario-cuenta, asi que republicar el mismo vinculo no
        duplica nada.

        ⚠️ **Escribir aqui amplia el acceso de lectura en tres departamentos a la
        vez** —Soporte, Seguimiento y Emergencias—, porque los tres resuelven la
        cuenta del solicitante por esta tabla. No es un registro administrativo
        inocuo: es la concesion de acceso.
        """
        payload = {
            "idusuario": int(user_id),
            "idcliente": int(cliente_id),
            "activo": True,
            "fecha_actualizacion": ahora_ms(),
        }
        self.kafka.publish(self.TOPIC, payload)
        return payload

    def desvincular(self, user_id: int, cliente_id: int) -> dict[str, Any]:
        """Retira la pertenencia marcandola inactiva.

        **No se borra la fila**: las tres consultas filtran por `activo = true`,
        y conservar el registro deja rastro de que el vinculo existio. Borrar
        haria indistinguible «nunca perteneció» de «se le retiro el acceso».
        """
        payload = {
            "idusuario": int(user_id),
            "idcliente": int(cliente_id),
            "activo": False,
            "fecha_actualizacion": ahora_ms(),
        }
        self.kafka.publish(self.TOPIC, payload)
        return payload

    def list_active_by_cliente(self, cliente_id: int) -> list[dict[str, Any]]:
        cliente = self.cliente_repo.find_by_id(cliente_id)
        if not cliente:
            return []
        admin_id = cliente.get("admin_local_id")
        if not admin_id:
            return []
        user = self.user_repo.find_by_id(admin_id)
        if user and user.get("activo", False):
            return [user]
        return []

    def user_belongs_to_cliente(self, user_id: int, cliente_id: int) -> bool:
        cliente = self.cliente_repo.find_by_id(cliente_id)
        if not cliente:
            return False
        return cliente.get("admin_local_id") == user_id

    def get_cliente_ids_for_user(self, user_id: int) -> list[int]:
        cliente = self.cliente_repo.find_by_admin_local(user_id)
        if cliente:
            return [cliente["idcliente"]]
        return []

    def list_miembros(self, cliente_id: int) -> list[dict[str, Any]]:
        """Usuarios activos que pertenecen a la organización del cliente.

        La pertenencia vive en `Dim_Usuario_Cliente`, que es lo que ya consultan
        Seguimiento (expedientes del cliente) y Soporte para resolver a qué
        cuenta pertenece un usuario. Los métodos de arriba la deducen del
        `admin_local_id`, y con ese criterio una organización tiene como mucho
        una persona — cuando el plan contratado limita precisamente el «número
        máximo de usuarios» de la organización.

        Se incluye al administrador local aunque no tenga fila de vínculo: es
        miembro por definición y su fila puede faltar en cuentas antiguas.
        """
        filas = self.pinot.query(
            "SELECT idusuario FROM Dim_Usuario_Cliente "
            "WHERE idcliente = %(idcliente)s AND activo = true LIMIT 200",
            {"idcliente": cliente_id},
        ) or []
        ids = {int(f["idusuario"]) for f in filas}

        cliente = self.cliente_repo.find_by_id(cliente_id)
        admin_id = cliente.get("admin_local_id") if cliente else None
        if admin_id:
            ids.add(int(admin_id))

        miembros = []
        for idusuario in sorted(ids):
            user = self.user_repo.find_by_id(idusuario)
            if user and user.get("activo", False):
                miembros.append(user)
        return miembros

    def es_miembro(self, user_id: int, cliente_id: int) -> bool:
        """¿Este usuario pertenece a la organización del cliente?"""
        return any(u["idusuario"] == user_id for u in self.list_miembros(cliente_id))

    def list_cuentas_del_usuario(self, user_id: int) -> list[dict[str, Any]]:
        """Cuentas a las que pertenece el usuario, por vínculo o por ser su admin local.

        Se usa en el login para rechazar a quien pertenece a una organización
        dada de baja (SRS §3.2.1). `get_cliente_ids_for_user` no sirve para eso:
        solo mira el `admin_local_id`, así que un miembro que no fuera el
        administrador quedaba fuera de la comprobación.
        """
        filas = self.pinot.query(
            "SELECT idcliente FROM Dim_Usuario_Cliente "
            "WHERE idusuario = %(idusuario)s AND activo = true LIMIT 50",
            {"idusuario": user_id},
        ) or []
        ids = {int(f["idcliente"]) for f in filas}

        cliente_admin = self.cliente_repo.find_by_admin_local(user_id)
        if cliente_admin:
            ids.add(int(cliente_admin["idcliente"]))

        cuentas = []
        for idcliente in sorted(ids):
            cliente = self.cliente_repo.find_by_id(idcliente)
            if cliente:
                cuentas.append(cliente)
        return cuentas
