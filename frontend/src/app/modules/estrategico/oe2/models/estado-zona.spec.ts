/** @marker unit */
import { cargaDeEnvelope, estadoDeZona } from './estado-zona';

describe('estadoDeZona (OE2)', () => {
  it('vacio_when_data_es_arreglo_vacio_no_es_cero', () => {
    expect(estadoDeZona({ loading: false, error: null, data: [] })).toBe('vacio');
  });

  it('sin_dato_when_la_metrica_es_nula', () => {
    expect(
      estadoDeZona({
        loading: false,
        error: null,
        data: [{ latencia_p95_ms: null }],
        metricaAusente: true,
      }),
    ).toBe('sin_dato');
  });

  it('dato_when_hay_filas_con_llamadas_cero', () => {
    expect(
      estadoDeZona({
        loading: false,
        error: null,
        data: [{ llamadas: 0 }],
        metricaAusente: false,
      }),
    ).toBe('dato');
  });

  it('dato_when_percentil_no_es_fiable', () => {
    expect(
      estadoDeZona({
        loading: false,
        error: null,
        data: [{ percentil_fiable: 0, latencia_p95_ms: 90, muestras: 2 }],
        metricaAusente: false,
      }),
    ).toBe('dato');
  });
});

describe('cargaDeEnvelope (OE2)', () => {
  it('extrae_data_como_array_no_resultados', () => {
    const carga = cargaDeEnvelope({
      data: [{ llamadas: 0 }],
      meta: { cobertura: 'completa' },
    });
    expect(carga.estado).toBe('dato');
    expect(carga.data[0]['llamadas']).toBe(0);
  });

  it('vacio_when_array_vacio', () => {
    const carga = cargaDeEnvelope({ data: [], meta: {} });
    expect(carga.estado).toBe('vacio');
  });
});
