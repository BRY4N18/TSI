/** @marker unit */
import { estadoDeZona } from './estado-zona';

describe('estadoDeZona', () => {
  it('vacio_when_data_es_arreglo_vacio_no_es_cero', () => {
    expect(
      estadoDeZona({ loading: false, error: null, data: [] }),
    ).toBe('vacio');
  });

  it('sin_dato_when_la_metrica_es_nula', () => {
    expect(
      estadoDeZona({
        loading: false,
        error: null,
        data: [{ pct_completitud: null }],
        metricaAusente: true,
      }),
    ).toBe('sin_dato');
  });

  it('dato_when_hay_filas_con_metrica', () => {
    expect(
      estadoDeZona({
        loading: false,
        error: null,
        data: [{ pct_completitud: 0.95 }],
        metricaAusente: false,
      }),
    ).toBe('dato');
  });

  it('error_when_falla_la_zona', () => {
    expect(
      estadoDeZona({ loading: false, error: 'falló', data: [] }),
    ).toBe('error');
  });
});
