/** @marker unit */
import {
  BLOQUEADOS_UI,
  PANTALLAS,
  PUBLICADOS_UI,
  SLOTS_CALIDAD,
  SLOTS_COBERTURA,
  SLOTS_CONCENTRACION,
  SLOTS_IMPACTO,
  informesDe,
} from './pantallas-oe4.definiciones';

describe('Definiciones OE4', () => {
  it('calidad_cita_cuatro_slugs_de_expediente', () => {
    expect(informesDe(PANTALLAS['calidad']).sort()).toEqual([...SLOTS_CALIDAD].sort());
  });

  it('concentracion_cita_ranking_y_patron', () => {
    expect(informesDe(PANTALLAS['concentracion']).sort()).toEqual([...SLOTS_CONCENTRACION].sort());
  });

  it('impacto_cita_humano_y_vial', () => {
    expect(informesDe(PANTALLAS['impacto']).sort()).toEqual([...SLOTS_IMPACTO].sort());
  });

  it('cobertura_cita_solo_historico', () => {
    expect(informesDe(PANTALLAS['cobertura']).sort()).toEqual([...SLOTS_COBERTURA].sort());
  });

  it('union_son_nueve_sin_bloqueados', () => {
    const citados = Object.values(PANTALLAS).flatMap((p) => informesDe(p));
    expect([...new Set(citados)].sort()).toEqual([...PUBLICADOS_UI].sort());
    expect(new Set(citados).size).toBe(9);
    for (const slug of BLOQUEADOS_UI) {
      expect(PUBLICADOS_UI).not.toContain(slug);
      expect(citados.join()).not.toContain(slug);
    }
  });
});
