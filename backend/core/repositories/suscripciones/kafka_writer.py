"""Re-export KafkaWriter for suscripciones repositories."""

from core.repositories.cuentas_clientes.kafka_writer import KafkaWriter

__all__ = ["KafkaWriter"]
