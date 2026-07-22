"""Kafka write adapter for red_operativa domain — reuses core writer."""

from core.repositories.cuentas_clientes.kafka_writer import KafkaWriter

__all__ = ["KafkaWriter"]
