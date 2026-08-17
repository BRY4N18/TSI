/** @marker unit */
import { esSinCapacidad } from './sin-capacidad';

describe('esSinCapacidad', () => {
  it('declara_sin_capacidad_when_hay_casos_y_cero_unidades', () => {
    expect(esSinCapacidad({ casos: 10, unidades_vigentes: 0, ratio: null })).toBeTrue();
  });

  it('declara_sin_capacidad_when_el_ratio_es_nulo', () => {
    expect(esSinCapacidad({ casos: 4, unidades_vigentes: null, ratio: null })).toBeTrue();
  });

  it('un_cero_real_when_hay_unidades_sigue_siendo_cero', () => {
    expect(esSinCapacidad({ casos: 0, unidades_vigentes: 3, ratio: 0 })).toBeFalse();
  });

  it('ratio_cero_with_unidades_no_es_sin_capacidad', () => {
    expect(esSinCapacidad({ casos: 0, unidades_vigentes: 2, ratio: 0 })).toBeFalse();
  });
});
