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
        data: [{ pct_renovacion: null }],
        metricaAusente: true,
      }),
    ).toBe('sin_dato');
  });

  it('dato_when_hay_filas_con_metrica', () => {
    expect(
      estadoDeZona({
        loading: false,
        error: null,
        data: [{ pct_renovacion: 0 }],
        metricaAusente: false,
      }),
    ).toBe('dato');
  });

  it('error_when_falla_la_zona', () => {
    expect(estadoDeZona({ loading: false, error: 'falló', data: [] })).toBe('error');
  });
});

describe('cargaDeEnvelope', () => {
  it('vacio_when_data_vacia_conserva_mes_y_nota_periodo', () => {
    const carga = cargaDeEnvelope({
      data: [],
      meta: { mes: '2026-07', nota_periodo: 'Se mide por mes natural.' },
    });
    expect(carga.estado).toBe('vacio');
    expect(carga.meta.mes).toBe('2026-07');
    expect(carga.meta.nota_periodo).toContain('mes natural');
  });

  it('pct_renovacion_nulo_when_se_marca_es_sin_dato_no_cero', () => {
    const carga = cargaDeEnvelope({ data: [{ pct_renovacion: null }], meta: {} }, true);
    expect(carga.estado).toBe('sin_dato');
    expect(carga.data[0]['pct_renovacion']).toBeNull();
  });
});
