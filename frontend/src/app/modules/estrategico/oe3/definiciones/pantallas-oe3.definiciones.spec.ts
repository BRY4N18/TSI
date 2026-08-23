/** @marker unit */
import {
  BLOQUEADOS_UI,
  PANTALLAS,
  PUBLICADOS_UI,
  SLOTS_CALIDAD,
  SLOTS_CAPACIDAD,
  SLOTS_LATENCIA,
  SLOTS_RESPALDO,
  informesDe,
} from './pantallas-oe3.definiciones';

describe('Definiciones OE3', () => {
  it('latencia_cita_exactamente_dos_slugs', () => {
    expect(informesDe(PANTALLAS['latencia']).sort()).toEqual([...SLOTS_LATENCIA].sort());
  });

  it('calidad_cita_error_y_primer_intento', () => {
    expect(informesDe(PANTALLAS['calidad']).sort()).toEqual([...SLOTS_CALIDAD].sort());
  });

  it('capacidad_cita_ratio_y_perdida_senal', () => {
    expect(informesDe(PANTALLAS['capacidad']).sort()).toEqual([...SLOTS_CAPACIDAD].sort());
  });

  it('respaldo_cita_exactamente_cobertura', () => {
    expect(informesDe(PANTALLAS['respaldo']).sort()).toEqual([...SLOTS_RESPALDO].sort());
  });

  it('union_son_siete_sin_bloqueados_ni_oe6', () => {
    const citados = Object.values(PANTALLAS).flatMap((p) => informesDe(p));
    expect([...new Set(citados)].sort()).toEqual([...PUBLICADOS_UI].sort());
    expect(new Set(citados).size).toBe(7);
    for (const slug of BLOQUEADOS_UI) {
      expect(PUBLICADOS_UI).not.toContain(slug);
      expect(citados.join()).not.toContain(slug);
    }
    expect(citados.join()).not.toContain('tiempo-respuesta-global');
    expect(PUBLICADOS_UI).not.toContain('uptime-por-region');
    expect(PUBLICADOS_UI).not.toContain('tiempo-puesta-operacion');
    expect(PUBLICADOS_UI).not.toContain('curva-maduracion');
    expect(PUBLICADOS_UI).not.toContain('cohorte-region');
    expect(PUBLICADOS_UI).not.toContain('margen-operativo');
    expect(PUBLICADOS_UI).not.toContain('reasignacion-manual');
    expect(PUBLICADOS_UI).not.toContain('cobertura-pruebas');
  });
});
