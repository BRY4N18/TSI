/** @marker unit */
import { cargaDeEnvelope, estadoDeZona } from './estado-zona';

describe('estadoDeZona', () => {
  it('vacio_when_data_es_arreglo_vacio_no_es_cero', () => {
    expect(estadoDeZona({ loading: false, error: null, data: [] })).toBe('vacio');
  });

  it('sin_dato_when_la_metrica_es_nula', () => {
    expect(
      estadoDeZona({
        loading: false,
        error: null,
        data: [{ pct_disponibilidad: null }],
        metricaAusente: true,
      }),
    ).toBe('sin_dato');
  });

  it('dato_when_hay_filas_con_metrica', () => {
    expect(
      estadoDeZona({
        loading: false,
        error: null,
        data: [{ pct_disponibilidad: 0 }],
        metricaAusente: false,
      }),
    ).toBe('dato');
  });

  it('error_when_falla_la_zona', () => {
    expect(estadoDeZona({ loading: false, error: 'falló', data: [] })).toBe('error');
  });
});

describe('cargaDeEnvelope', () => {
  it('vacio_when_data_vacia_conserva_medida_exacta_desde', () => {
    const carga = cargaDeEnvelope({
      data: [],
      meta: { medida_exacta_desde: '2026-08-14' },
    });
    expect(carga.estado).toBe('vacio');
    expect(carga.meta.medida_exacta_desde).toBe('2026-08-14');
  });

  it('pct_disponibilidad_nulo_when_se_marca_es_sin_dato_no_cero', () => {
    const carga = cargaDeEnvelope(
      { data: [{ pct_disponibilidad: null }], meta: {} },
      true,
    );
    expect(carga.estado).toBe('sin_dato');
    expect(carga.data[0]['pct_disponibilidad']).toBeNull();
  });
});
