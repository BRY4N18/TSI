/** @marker unit */
import { cargaDeEnvelope, estadoDeZona } from './estado-zona';

describe('estadoDeZona (OE6)', () => {
  it('vacio_when_data_es_arreglo_vacio_no_es_cero_min', () => {
    expect(estadoDeZona({ loading: false, error: null, data: [] })).toBe('vacio');
  });

  it('sin_dato_when_metrica_ausente', () => {
    expect(
      estadoDeZona({
        loading: false,
        error: null,
        data: [{ p95_min: null }],
        metricaAusente: true,
      }),
    ).toBe('sin_dato');
  });

  it('dato_when_hay_filas', () => {
    expect(
      estadoDeZona({
        loading: false,
        error: null,
        data: [{ mediana_min: 8 }],
        metricaAusente: false,
      }),
    ).toBe('dato');
  });
});

describe('cargaDeEnvelope (OE6)', () => {
  it('extrae_data_como_array_no_resultados', () => {
    const carga = cargaDeEnvelope({
      data: [{ mediana_min: 8, casos_con_llegada: 40 }],
      meta: { cobertura: 'parcial' },
    });
    expect(carga.estado).toBe('dato');
    expect(carga.data[0]['casos_con_llegada']).toBe(40);
  });

  it('vacio_when_array_vacio', () => {
    const carga = cargaDeEnvelope({ data: [], meta: {} });
    expect(carga.estado).toBe('vacio');
  });
});
