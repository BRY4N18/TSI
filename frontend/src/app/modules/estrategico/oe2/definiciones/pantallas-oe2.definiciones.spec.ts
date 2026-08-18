/** @marker unit */
import {
  PANTALLAS,
  PUBLICADOS_UI,
  SLOTS_DINERO,
  SLOTS_ECOSISTEMA,
  SLOTS_USO,
  informesDe,
} from './pantallas-oe2.definiciones';

describe('Definiciones OE2', () => {
  it('uso_cita_exactamente_cuatro_slugs', () => {
    expect(informesDe(PANTALLAS['uso']).sort()).toEqual([...SLOTS_USO].sort());
  });

  it('dinero_cita_exactamente_tres_slugs', () => {
    expect(informesDe(PANTALLAS['dinero']).sort()).toEqual([...SLOTS_DINERO].sort());
  });

  it('ecosistema_cita_tres_slugs', () => {
    expect(informesDe(PANTALLAS['ecosistema']).sort()).toEqual([...SLOTS_ECOSISTEMA].sort());
  });

  it('union_son_diez_y_sin_disponibilidad', () => {
    const citados = Object.values(PANTALLAS).flatMap((p) => informesDe(p));
    expect([...new Set(citados)].sort()).toEqual([...PUBLICADOS_UI].sort());
    expect(new Set(citados).size).toBe(10);
    expect(PUBLICADOS_UI).not.toContain('disponibilidad-api');
    expect(citados.join()).not.toContain('disponibilidad');
  });
});
