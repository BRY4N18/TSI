"""T023 — ningún objetivo CALIBRAR devuelve un cumple booleano."""

from apps.informes_estrategicos.objetivo import construir_objetivo, objetivo_calibrar


class TestCalibrarNuncaSemaforiza:
    def test_cumple_es_null_sin_medido(self):
        objetivo = objetivo_calibrar(valor=8, unidad="min")
        assert objetivo["tipo"] == "CALIBRAR"
        assert objetivo["cumple"] is None

    def test_cumple_sigue_null_aunque_se_pase_un_valor_medido(self):
        # Un semáforo aquí inventaría el umbral y luego se mediría contra él.
        por_debajo = construir_objetivo(
            tipo="CALIBRAR", valor=8, unidad="min", medido=5
        )
        por_encima = construir_objetivo(
            tipo="CALIBRAR", valor=8, unidad="min", medido=20
        )
        assert por_debajo["cumple"] is None
        assert por_encima["cumple"] is None
        assert not isinstance(por_debajo["cumple"], bool)
        assert not isinstance(por_encima["cumple"], bool)

    def test_normativo_si_puede_ser_booleano(self):
        assert construir_objetivo(
            tipo="NORMATIVO", valor=2, unidad="min", medido=1.5
        )["cumple"] is True
        assert construir_objetivo(
            tipo="NORMATIVO", valor=2, unidad="min", medido=3
        )["cumple"] is False

    def test_normativo_lt_no_cumple_en_el_umbral(self):
        # E3-02 es <2 min, no ≤. Exactamente 2 minutos es rojo.
        from apps.informes_estrategicos.objetivo import objetivo_normativo

        assert objetivo_normativo(valor=2, unidad="min", medido=1.77, umbral="lt")["cumple"] is True
        assert objetivo_normativo(valor=2, unidad="min", medido=2.0, umbral="lt")["cumple"] is False
        assert isinstance(
            objetivo_normativo(valor=2, unidad="min", medido=1.77, umbral="lt")["cumple"],
            bool,
        )
