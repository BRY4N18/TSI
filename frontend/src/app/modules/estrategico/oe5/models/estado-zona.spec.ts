/** @marker unit */
import { cargaDeEnvelope, estadoDeZona } from './estado-zona';

describe('estadoDeZona (OE5)', () => {
  it('vacio_when_data_es_arreglo_vacio_no_es_cero_porciento', () => {
    expect(estadoDeZona({ loading: false, error: null, data: [] })).toBe('vacio');
  });

  it('sin_dato_when_metrica_ausente', () => {
    expect(
      estadoDeZona({
        loading: false,
        error: null,
        data: [{ con_compromiso: 0 }],
        metricaAusente: true,
      }),
    ).toBe('sin_dato');
  });

  it('dato_when_incumplidos_cero_en_fila', () => {
    expect(
      estadoDeZona({
        loading: false,
        error: null,
        data: [{ incumplidos: 0 }],
        metricaAusente: false,
      }),
    ).toBe('dato');
  });
});

describe('cargaDeEnvelope (OE5)', () => {
  it('extrae_data_como_array_no_resultados', () => {
    const carga = cargaDeEnvelope({
      data: [{ pct_cumplimiento: 0.9, con_compromiso: 14 }],
      meta: { cobertura: 'parcial' },
    });
    expect(carga.estado).toBe('dato');
    expect(carga.data[0]['con_compromiso']).toBe(14);
    expect(carga.meta.cobertura).toBe('parcial');
  });

  it('vacio_when_array_vacio', () => {
    const carga = cargaDeEnvelope({ data: [], meta: {} });
    expect(carga.estado).toBe('vacio');
  });
});
