"""Kafka write adapter for soporte_cliente domain — reuses core writer."""

from core.repositories.cuentas_clientes.kafka_writer import KafkaWriter

__all__ = ["KafkaWriter"]
