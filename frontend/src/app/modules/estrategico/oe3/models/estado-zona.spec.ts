/** @marker unit */
import { cargaDeEnvelope, estadoDeZona } from './estado-zona';

describe('estadoDeZona (OE3)', () => {
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
        data: [{ p95_min: 1.8 }],
        metricaAusente: false,
      }),
    ).toBe('dato');
  });
});

describe('cargaDeEnvelope (OE3)', () => {
  it('extrae_data_como_array_no_resultados', () => {
    const carga = cargaDeEnvelope({
      data: [{ p95_min: 1.8, casos_asignados: 40 }],
      meta: { cobertura: 'parcial' },
    });
    expect(carga.estado).toBe('dato');
    expect(carga.data[0]['casos_asignados']).toBe(40);
  });

  it('vacio_when_array_vacio', () => {
    const carga = cargaDeEnvelope({ data: [], meta: {} });
    expect(carga.estado).toBe('vacio');
  });

  it('sin_capacidad_no_es_infinito_es_fila_con_flag', () => {
    const carga = cargaDeEnvelope({
      data: [{ condado: 'X', casos: 4, unidades_vigentes: 0, sin_capacidad: 1 }],
      meta: {},
    });
    expect(carga.estado).toBe('dato');
    expect(carga.data[0]['sin_capacidad']).toBe(1);
  });
});
