/** @marker unit */
import { cargaDeEnvelope, estadoDeZona } from './estado-zona';

describe('estadoDeZona (Cuentas)', () => {
  it('vacio_when_data_es_arreglo_vacio_no_es_cero', () => {
    expect(estadoDeZona({ loading: false, error: null, data: [] })).toBe('vacio');
  });

  it('sin_dato_when_la_metrica_es_nula', () => {
    expect(
      estadoDeZona({
        loading: false,
        error: null,
        data: [{ pct_ocupacion: null }],
        metricaAusente: true,
      }),
    ).toBe('sin_dato');
  });

  it('dato_when_hay_filas_con_churn_cero', () => {
    expect(
      estadoDeZona({
        loading: false,
        error: null,
        data: [{ pct_churn: 0 }],
        metricaAusente: false,
      }),
    ).toBe('dato');
  });

  it('dato_when_sin_actividad_conocida', () => {
    expect(
      estadoDeZona({
        loading: false,
        error: null,
        data: [{ sin_actividad_conocida: 1, dias_sin_actividad: null }],
        metricaAusente: false,
      }),
    ).toBe('dato');
  });
});

describe('cargaDeEnvelope (Cuentas)', () => {
  it('vacio_when_resultados_vacios_conserva_nota_cobertura', () => {
    const carga = cargaDeEnvelope({
      data: { resultados: [] },
      meta: { nota_cobertura: 'Solo el 9,5 % de los usuarios tiene organización declarada.' },
    });
    expect(carga.estado).toBe('vacio');
    expect(carga.meta.nota_cobertura).toContain('9,5');
  });

  it('extrae_resultados_del_objeto_data_no_trata_data_como_array', () => {
    const carga = cargaDeEnvelope({
      data: { resultados: [{ pct_churn: 0 }] },
      meta: {},
    });
    expect(carga.estado).toBe('dato');
    expect(carga.data[0]['pct_churn']).toBe(0);
  });

  it('pct_nulo_when_se_marca_es_sin_dato_no_cero', () => {
    const carga = cargaDeEnvelope(
      { data: { resultados: [{ pct_ocupacion: null }] }, meta: {} },
      true,
    );
    expect(carga.estado).toBe('sin_dato');
    expect(carga.data[0]['pct_ocupacion']).toBeNull();
  });
});
