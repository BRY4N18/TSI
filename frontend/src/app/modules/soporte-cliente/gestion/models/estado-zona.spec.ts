/** @marker unit */
import { cargaDeEnvelope, estadoDeZona } from './estado-zona';

describe('estadoDeZona (Soporte al Cliente)', () => {
  it('vacio_when_data_es_arreglo_vacio_no_es_cero', () => {
    expect(estadoDeZona({ loading: false, error: null, data: [] })).toBe('vacio');
  });

  it('sin_dato_when_pct_cumplimiento_es_nulo', () => {
    expect(
      estadoDeZona({
        loading: false,
        error: null,
        data: [{ pct_cumplimiento: null }],
        metricaAusente: true,
      }),
    ).toBe('sin_dato');
  });

  it('dato_when_hay_fila_con_tickets_cero', () => {
    expect(
      estadoDeZona({
        loading: false,
        error: null,
        data: [{ tickets: 0 }],
        metricaAusente: false,
      }),
    ).toBe('dato');
  });

  it('error_when_falla_la_zona', () => {
    expect(estadoDeZona({ loading: false, error: 'falló', data: [] })).toBe('error');
  });
});

describe('cargaDeEnvelope (Soporte al Cliente)', () => {
  it('vacio_when_resultados_vacios_conserva_acotado_a', () => {
    const carga = cargaDeEnvelope({
      data: { resultados: [], declaraciones: [] },
      meta: { acotado_a: 'propios' },
    });
    expect(carga.estado).toBe('vacio');
    expect(carga.meta.acotado_a).toBe('propios');
  });

  it('pct_cumplimiento_nulo_when_se_marca_es_sin_dato_no_cero', () => {
    const carga = cargaDeEnvelope(
      {
        data: { resultados: [{ pct_cumplimiento: null, tickets: 4 }], declaraciones: [] },
        meta: {},
      },
      true,
    );
    expect(carga.estado).toBe('sin_dato');
    expect(carga.data[0]['pct_cumplimiento']).toBeNull();
  });

  it('tickets_cero_en_serie_es_dato_no_vacio', () => {
    const carga = cargaDeEnvelope({
      data: { resultados: [{ tickets: 0, periodo: '2026-08-01' }], declaraciones: [] },
      meta: { acotado_a: 'todos' },
    });
    expect(carga.estado).toBe('dato');
    expect(carga.meta.acotado_a).toBe('todos');
  });
});
