import pytest
from django.http import QueryDict

from apps.informes_tacticos.periodo import PeriodoInvalido, parse_periodo


def _qs(**kwargs) -> QueryDict:
    qd = QueryDict(mutable=True)
    for k, v in kwargs.items():
        qd[k] = v
    return qd


@pytest.mark.unit
class TestParsePeriodo:
    def test_parse_periodo_with_default_granularidad_returns_dia(self):
        # Arrange
        params = _qs(desde="2026-07-01", hasta="2026-07-31")

        # Act
        periodo = parse_periodo(params)

        # Assert
        assert periodo.granularidad == "dia"
        assert periodo.datetrunc_unit == "day"

    @pytest.mark.parametrize(
        "granularidad,expected_unit",
        [("dia", "day"), ("semana", "week"), ("mes", "month")],
    )
    def test_parse_periodo_accepts_supported_granularidades(self, granularidad, expected_unit):
        # Arrange
        params = _qs(desde="2026-07-01", hasta="2026-07-31", granularidad=granularidad)

        # Act
        periodo = parse_periodo(params)

        # Assert
        assert periodo.datetrunc_unit == expected_unit

    def test_parse_periodo_range_is_inclusive_of_hasta_day(self):
        # Arrange
        params = _qs(desde="2026-07-01", hasta="2026-07-01")

        # Act
        periodo = parse_periodo(params)

        # Assert
        assert periodo.hasta_ms > periodo.desde_ms
        assert periodo.hasta_ms - periodo.desde_ms == 24 * 60 * 60 * 1000 - 1

    def test_parse_periodo_missing_desde_raises(self):
        # Arrange
        params = _qs(hasta="2026-07-31")

        # Act / Assert
        with pytest.raises(PeriodoInvalido):
            parse_periodo(params)

    def test_parse_periodo_desde_after_hasta_raises(self):
        # Arrange
        params = _qs(desde="2026-08-01", hasta="2026-07-01")

        # Act / Assert
        with pytest.raises(PeriodoInvalido):
            parse_periodo(params)

    def test_parse_periodo_unsupported_granularidad_raises(self):
        # Arrange
        params = _qs(desde="2026-07-01", hasta="2026-07-31", granularidad="hora")

        # Act / Assert
        with pytest.raises(PeriodoInvalido):
            parse_periodo(params)

    def test_parse_periodo_invalid_date_format_raises(self):
        # Arrange
        params = _qs(desde="01-07-2026", hasta="2026-07-31")

        # Act / Assert
        with pytest.raises(PeriodoInvalido):
            parse_periodo(params)
