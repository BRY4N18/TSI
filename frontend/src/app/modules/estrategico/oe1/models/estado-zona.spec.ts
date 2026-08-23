/** @marker unit */
import { cargaDeEnvelope, estadoDeZona } from './estado-zona';

describe('estadoDeZona (OE1)', () => {
  it('vacio_when_data_es_arreglo_vacio_no_es_cero_euros', () => {
    expect(estadoDeZona({ loading: false, error: null, data: [] })).toBe('vacio');
  });

  it('sin_dato_when_pct_churn_nulo', () => {
    expect(
      estadoDeZona({
        loading: false,
        error: null,
        data: [{ pct_churn: null, n: 4 }],
        metricaAusente: true,
      }),
    ).toBe('sin_dato');
  });

  it('dato_when_transiciones_cero', () => {
    expect(
      estadoDeZona({
        loading: false,
        error: null,
        data: [{ transiciones: 0 }],
        metricaAusente: false,
      }),
    ).toBe('dato');
  });
});

describe('cargaDeEnvelope (OE1)', () => {
  it('extrae_data_como_array_no_resultados', () => {
    const carga = cargaDeEnvelope({
      data: [{ mrr: 12000, recuento: 4 }],
      meta: { cobertura: 'parcial' },
    });
    expect(carga.estado).toBe('dato');
    expect(carga.data[0]['recuento']).toBe(4);
    expect(carga.meta.cobertura).toBe('parcial');
  });

  it('vacio_when_array_vacio', () => {
    const carga = cargaDeEnvelope({ data: [], meta: {} });
    expect(carga.estado).toBe('vacio');
  });
});
