/** @marker unit */
import {
  BLOQUEADOS_UI,
  PANTALLAS,
  PUBLICADOS_UI,
  SLOTS_CAPTACION,
  SLOTS_CARTERA,
  SLOTS_CICLO,
  SLOTS_INGRESO,
  informesDe,
} from './pantallas-oe1.definiciones';

describe('Definiciones OE1', () => {
  it('ingreso_cita_exactamente_tres_slugs', () => {
    expect(informesDe(PANTALLAS['ingreso']).sort()).toEqual([...SLOTS_INGRESO].sort());
  });

  it('cartera_cita_exactamente_dos_slugs', () => {
    expect(informesDe(PANTALLAS['cartera']).sort()).toEqual([...SLOTS_CARTERA].sort());
  });

  it('captacion_cita_embudo_y_velocidad', () => {
    expect(informesDe(PANTALLAS['captacion']).sort()).toEqual([...SLOTS_CAPTACION].sort());
  });

  it('ciclo_cita_churn_abandono_tiempo', () => {
    expect(informesDe(PANTALLAS['ciclo']).sort()).toEqual([...SLOTS_CICLO].sort());
  });

  it('union_son_diez_sin_cac_ni_mercados', () => {
    const citados = Object.values(PANTALLAS).flatMap((p) => informesDe(p));
    expect([...new Set(citados)].sort()).toEqual([...PUBLICADOS_UI].sort());
    expect(new Set(citados).size).toBe(10);
    for (const slug of BLOQUEADOS_UI) {
      expect(PUBLICADOS_UI).not.toContain(slug);
      expect(citados.join()).not.toContain(slug);
    }
    expect(citados.join()).not.toContain('disponibilidad');
  });
});
