/** @marker unit */
import { cargaDeEnvelope, estadoDeZona } from './estado-zona';

describe('estadoDeZona (Ventas y CRM)', () => {
  it('vacio_when_data_es_arreglo_vacio_no_es_cero', () => {
    expect(estadoDeZona({ loading: false, error: null, data: [] })).toBe('vacio');
  });

  it('sin_dato_when_pct_conversion_es_nulo', () => {
    expect(
      estadoDeZona({
        loading: false,
        error: null,
        data: [{ pct_conversion: null }],
        metricaAusente: true,
      }),
    ).toBe('sin_dato');
  });

  it('dato_when_hay_filas_con_metrica', () => {
    expect(
      estadoDeZona({
        loading: false,
        error: null,
        data: [{ pct_conversion: 0 }],
        metricaAusente: false,
      }),
    ).toBe('dato');
  });

  it('error_when_falla_la_zona', () => {
    expect(estadoDeZona({ loading: false, error: 'falló', data: [] })).toBe('error');
  });
});

describe('cargaDeEnvelope (Ventas y CRM)', () => {
  it('vacio_when_data_vacia_conserva_acotado_a', () => {
    const carga = cargaDeEnvelope({
      data: [],
      meta: { acotado_a: 'propios' },
    });
    expect(carga.estado).toBe('vacio');
    expect(carga.meta.acotado_a).toBe('propios');
  });

  it('pct_conversion_nulo_when_se_marca_es_sin_dato_no_cero', () => {
    const carga = cargaDeEnvelope(
      { data: [{ pct_conversion: null }], meta: {} },
      true,
    );
    expect(carga.estado).toBe('sin_dato');
    expect(carga.data[0]['pct_conversion']).toBeNull();
  });
});
