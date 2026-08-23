/** @marker unit */
import {
  BLOQUEADOS_UI,
  PANTALLAS,
  PUBLICADOS_UI,
  SLOTS_INGRESOS,
  SLOTS_PLANES,
  SLOTS_RIESGO,
  SLOTS_SERVICIO,
  informesDe,
} from './pantallas-oe5.definiciones';

describe('Definiciones OE5', () => {
  it('servicio_cita_exactamente_cuatro_slugs', () => {
    expect(informesDe(PANTALLAS['servicio']).sort()).toEqual([...SLOTS_SERVICIO].sort());
  });

  it('ingresos_cita_nrr', () => {
    expect(informesDe(PANTALLAS['ingresos']).sort()).toEqual([...SLOTS_INGRESOS].sort());
  });

  it('planes_cita_sla_movimientos_antiguedad', () => {
    expect(informesDe(PANTALLAS['planes']).sort()).toEqual([...SLOTS_PLANES].sort());
  });

  it('riesgo_cita_cuentas_en_riesgo', () => {
    expect(informesDe(PANTALLAS['riesgo']).sort()).toEqual([...SLOTS_RIESGO].sort());
  });

  it('union_son_nueve_sin_nps_ni_ciclo_oe1', () => {
    const citados = Object.values(PANTALLAS).flatMap((p) => informesDe(p));
    expect([...new Set(citados)].sort()).toEqual([...PUBLICADOS_UI].sort());
    expect(new Set(citados).size).toBe(9);
    for (const slug of BLOQUEADOS_UI) {
      expect(PUBLICADOS_UI).not.toContain(slug);
      expect(citados.join()).not.toContain(slug);
    }
  });
});
