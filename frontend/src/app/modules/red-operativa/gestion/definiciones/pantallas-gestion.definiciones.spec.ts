/** @marker unit */
import {
  PANTALLAS,
  PUBLICADOS_UI,
  SLOTS_FLOTA,
  SLOTS_MERCADOS,
  SLOTS_VALIDACION,
  TEXTO_GRANO,
  informesDe,
} from './pantallas-gestion.definiciones';

describe('Definiciones de pantallas de Red Operativa', () => {
  it('flota_when_declara_materia_es_crecimiento_y_son_los_ocho_de_ot12', () => {
    expect(PANTALLAS['flota'].materia).toBe('crecimiento');
    expect(informesDe(PANTALLAS['flota']).sort()).toEqual([...SLOTS_FLOTA].sort());
  });

  it('mercados_when_declara_materia_es_crecimiento_y_no_incluye_validacion', () => {
    expect(PANTALLAS['mercados'].materia).toBe('crecimiento');
    const slugs = informesDe(PANTALLAS['mercados']);
    expect(slugs.sort()).toEqual([...SLOTS_MERCADOS].sort());
    expect(slugs).not.toContain('tasa-aprobacion-primer-intento');
    expect(slugs).not.toContain('motivos-rechazo');
  });

  it('validacion_when_declara_materia_son_exactamente_dos_slugs_y_el_grano_son_intentos', () => {
    expect(PANTALLAS['validacion'].materia).toBe('validacion');
    expect(informesDe(PANTALLAS['validacion']).sort()).toEqual([...SLOTS_VALIDACION].sort());
    expect(PANTALLAS['validacion'].lecturaTexto).toBe(TEXTO_GRANO);
    expect(TEXTO_GRANO.toLowerCase()).toContain('intentos');
    expect(TEXTO_GRANO.toLowerCase()).not.toContain('se cuentan regiones');
  });

  it('las_tres_pantallas_when_se_unen_citan_exactamente_los_15_una_vez', () => {
    const citados = Object.values(PANTALLAS).flatMap((p) => informesDe(p));
    expect(citados.length).toBe(15);
    expect([...new Set(citados)].sort()).toEqual([...PUBLICADOS_UI].sort());
    expect(citados.length).toBe(new Set(citados).size);
  });

  it('ningun_slug_de_validacion_when_se_revisa_aparece_en_flota_o_mercados', () => {
    const crecimiento = new Set([
      ...informesDe(PANTALLAS['flota']),
      ...informesDe(PANTALLAS['mercados']),
    ]);
    for (const slug of SLOTS_VALIDACION) {
      expect(crecimiento.has(slug)).toBeFalse();
    }
  });
});
