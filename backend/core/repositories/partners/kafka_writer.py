"""Kafka write adapter para el dominio Partners y API — reutiliza el writer core."""

from core.repositories.cuentas_clientes.kafka_writer import KafkaWriter

__all__ = ["KafkaWriter"]
