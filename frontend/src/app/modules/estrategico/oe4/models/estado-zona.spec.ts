/** @marker unit */
import { cargaDeEnvelope, estadoDeZona } from './estado-zona';

describe('estadoDeZona (OE4)', () => {
  it('vacio_when_data_es_arreglo_vacio_no_es_cero_pct', () => {
    expect(estadoDeZona({ loading: false, error: null, data: [] })).toBe('vacio');
  });

  it('dato_when_hay_filas', () => {
    expect(
      estadoDeZona({
        loading: false,
        error: null,
        data: [{ indice_consolidado: 0.5 }],
        metricaAusente: false,
      }),
    ).toBe('dato');
  });
});

describe('cargaDeEnvelope (OE4)', () => {
  it('extrae_data_como_array_no_resultados', () => {
    const carga = cargaDeEnvelope({
      data: [{ indice_consolidado: 0.5 }],
      meta: { cobertura: 'parcial' },
    });
    expect(carga.estado).toBe('dato');
    expect(carga.data[0]['indice_consolidado']).toBe(0.5);
  });
});
