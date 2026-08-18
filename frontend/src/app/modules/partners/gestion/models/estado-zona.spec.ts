/** @marker unit */
import { cargaDeEnvelope, estadoDeZona } from './estado-zona';

describe('estadoDeZona (Partners)', () => {
  it('vacio_when_data_es_arreglo_vacio_no_es_cero', () => {
    expect(estadoDeZona({ loading: false, error: null, data: [] })).toBe('vacio');
  });

  it('sin_dato_when_la_metrica_es_nula', () => {
    expect(
      estadoDeZona({
        loading: false,
        error: null,
        data: [{ pct: null }],
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

describe('cargaDeEnvelope (Partners)', () => {
  it('vacio_when_resultados_vacios_conserva_nota_muestras', () => {
    const carga = cargaDeEnvelope({
      data: { resultados: [] },
      meta: { nota_muestras: 'Hay medidas calculadas sobre pocas llamadas.' },
    });
    expect(carga.estado).toBe('vacio');
    expect(carga.meta.nota_muestras).toContain('pocas llamadas');
  });

  it('extrae_resultados_del_objeto_data_no_trata_data_como_array', () => {
    const carga = cargaDeEnvelope({
      data: { resultados: [{ llamadas: 0 }] },
      meta: {},
    });
    expect(carga.estado).toBe('dato');
    expect(carga.data[0]['llamadas']).toBe(0);
  });

  it('pct_nulo_when_se_marca_es_sin_dato_no_cero', () => {
    const carga = cargaDeEnvelope(
      { data: { resultados: [{ pct: null }] }, meta: {} },
      true,
    );
    expect(carga.estado).toBe('sin_dato');
    expect(carga.data[0]['pct']).toBeNull();
  });
});
