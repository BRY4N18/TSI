"""Los dos instantes de una evidencia fotográfica.

⚠️ **Esta prueba existe porque la columna estaba vacía en el 100 % de las filas.**

`Dim_EvidenciaFoto.fecha_sincronizacion` existe en el esquema, el modelo la lee y
el informe de latencia de sincronización se apoya en ella — y **ninguna ruta de
escritura del sistema la rellenaba**. Las evidencias llegaban marcadas
`sincronizado = true` y sin el instante en que llegaron, así que la latencia era
imposible de medir: el informe decía «latencia medible en 0 de 50».

Lo que se vigila aquí no es que el campo exista, sino que **los dos instantes
sean distintos cuando el mundo dice que lo son**. Escribirle `fechahora` a los
dos —lo más fácil— daría latencia cero siempre, es decir la mejor marca posible
justo en las evidencias que más tardaron en llegar.
"""

from __future__ import annotations

from core.repositories.evidencia.evidencia_foto_repository import (
    EvidenciaFotoRepository,
)


class _KafkaEspia:
    def __init__(self):
        self.publicado: list[tuple[str, dict]] = []

    def publish(self, topic, payload):
        self.publicado.append((topic, payload))


def _repo():
    kafka = _KafkaEspia()
    repo = EvidenciaFotoRepository()
    repo.kafka = kafka
    return repo, kafka


class TestLosDosInstantes:
    def test_publica_el_instante_de_sincronizacion(self):
        repo, kafka = _repo()

        repo.create(
            idaccidente="ACC-1",
            idusuario=1,
            urlevidenciafoto="https://x/y.jpg",
            fechahora=1_700_000_000_000,
        )

        _, payload = kafka.publicado[-1]
        assert payload.get("fecha_sincronizacion"), (
            "sin este instante la latencia de sincronización no se puede medir, "
            "y el informe lo declara como «no medible» para siempre"
        )

    def test_la_captura_diferida_conserva_su_hora_y_no_la_de_llegada(self):
        """⚠️ El caso que hace útil la medida.

        Una foto tomada sin conexión y subida horas después tiene que conservar
        **cuándo se tomó** y declarar aparte **cuándo llegó**. Si las dos fueran
        iguales, la latencia saldría cero precisamente en la evidencia que peor
        se comportó.
        """
        repo, kafka = _repo()
        capturada_ayer = 1_700_000_000_000

        repo.create(
            idaccidente="ACC-1",
            idusuario=1,
            urlevidenciafoto="https://x/y.jpg",
            fechahora=capturada_ayer,
        )

        _, payload = kafka.publicado[-1]
        assert payload["fechahora"] == capturada_ayer
        assert payload["fecha_sincronizacion"] > capturada_ayer, (
            "el instante de llegada se copió del de captura: la latencia saldría "
            "cero aunque la foto tardara horas"
        )

    def test_sincronizado_y_su_fecha_viajan_juntos(self):
        """Marcar «llegó» sin decir cuándo es lo que dejó la columna vacía."""
        repo, kafka = _repo()

        repo.create(
            idaccidente="ACC-1",
            idusuario=1,
            urlevidenciafoto="https://x/y.jpg",
            fechahora=1_700_000_000_000,
        )

        _, payload = kafka.publicado[-1]
        assert payload["sincronizado"] is True
        assert payload["fecha_sincronizacion"] is not None
