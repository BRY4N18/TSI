/** @marker unit */
import {
  CAMPOS_COMPROBADOS_CALIDAD,
  PANTALLAS,
  PUBLICADOS_UI,
  VIGILADOS_UI,
  informesDe,
} from './pantallas-gestion.definiciones';

describe('Definiciones de pantallas de gestión', () => {
  it('calidad_when_declara_campos_son_severidad_y_condado', () => {
    expect(PANTALLAS['calidad'].camposComprobados).toEqual(['severidad', 'condado']);
    expect([...CAMPOS_COMPROBADOS_CALIDAD]).toEqual(['severidad', 'condado']);
  });

  it('las_tres_pantallas_when_se_unen_citan_exactamente_los_13_publicados', () => {
    const citados = new Set(
      Object.values(PANTALLAS).flatMap((p) => informesDe(p)),
    );
    expect([...citados].sort()).toEqual([...PUBLICADOS_UI].sort());
    expect(citados.size).toBe(13);
  });

  it('ningun_vigilado_when_se_revisa_aparece_en_una_zona', () => {
    const citados = new Set(
      Object.values(PANTALLAS).flatMap((p) => informesDe(p)),
    );
    for (const vigilado of VIGILADOS_UI) {
      expect(citados.has(vigilado)).toBeFalse();
    }
  });
});
