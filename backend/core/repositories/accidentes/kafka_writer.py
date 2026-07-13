"""Kafka write adapter for accidentes domain — reuses core writer."""

from core.repositories.cuentas_clientes.kafka_writer import KafkaWriter

__all__ = ["KafkaWriter"]
