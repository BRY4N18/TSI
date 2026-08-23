/** @marker unit */
import {
  BLOQUEADOS_UI,
  PANTALLAS,
  PUBLICADOS_UI,
  SLOTS_DIAGNOSTICO,
  SLOTS_EJECUCION,
  SLOTS_LLEGADA,
  SLOTS_PERSONAS,
  informesDe,
} from './pantallas-oe6.definiciones';

describe('Definiciones OE6', () => {
  it('llegada_cita_exactamente_dos_slugs', () => {
    expect(informesDe(PANTALLAS['llegada']).sort()).toEqual([...SLOTS_LLEGADA].sort());
  });

  it('diagnostico_cita_tramos_origen_desviacion', () => {
    expect(informesDe(PANTALLAS['diagnostico']).sort()).toEqual([...SLOTS_DIAGNOSTICO].sort());
  });

  it('ejecucion_cita_cuatro_slugs', () => {
    expect(informesDe(PANTALLAS['ejecucion']).sort()).toEqual([...SLOTS_EJECUCION].sort());
  });

  it('personas_cita_impacto_escaladas_evidencia', () => {
    expect(informesDe(PANTALLAS['personas']).sort()).toEqual([...SLOTS_PERSONAS].sort());
  });

  it('union_son_doce_sin_oe3_ni_eta', () => {
    const citados = Object.values(PANTALLAS).flatMap((p) => informesDe(p));
    expect([...new Set(citados)].sort()).toEqual([...PUBLICADOS_UI].sort());
    expect(new Set(citados).size).toBe(12);
    for (const slug of BLOQUEADOS_UI) {
      expect(PUBLICADOS_UI).not.toContain(slug);
      expect(citados.join()).not.toContain(slug);
    }
  });
});
