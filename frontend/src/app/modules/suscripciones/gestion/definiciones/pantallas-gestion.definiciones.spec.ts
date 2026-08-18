/** @marker unit */
import {
  PANTALLAS,
  PUBLICADOS_UI,
  SLOTS_CATALOGO,
  SLOTS_COBRO,
  SLOTS_MOVIMIENTOS,
  informesDe,
} from './pantallas-gestion.definiciones';

describe('Definiciones de pantallas de Suscripciones', () => {
  it('cobro_when_declara_materia_es_finanzas_y_son_los_seis_de_ot06', () => {
    expect(PANTALLAS['cobro'].materia).toBe('finanzas');
    expect(informesDe(PANTALLAS['cobro']).sort()).toEqual([...SLOTS_COBRO].sort());
  });

  it('movimientos_when_declara_materia_es_finanzas_y_no_incluye_catalogo_ni_mrr', () => {
    expect(PANTALLAS['movimientos'].materia).toBe('finanzas');
    const slugs = informesDe(PANTALLAS['movimientos']);
    expect(slugs.sort()).toEqual([...SLOTS_MOVIMIENTOS].sort());
    expect(slugs).not.toContain('distribucion-cartera');
    expect(slugs).not.toContain('mrr');
  });

  it('catalogo_when_declara_materia_son_exactamente_tres_slugs_y_no_cita_mrr_ni_nrr', () => {
    expect(PANTALLAS['catalogo'].materia).toBe('catalogo');
    expect(informesDe(PANTALLAS['catalogo']).sort()).toEqual([...SLOTS_CATALOGO].sort());
    expect(informesDe(PANTALLAS['catalogo'])).not.toContain('mrr');
    expect(informesDe(PANTALLAS['catalogo'])).not.toContain('nrr');
  });

  it('las_tres_pantallas_when_se_unen_citan_exactamente_los_13_una_vez', () => {
    const citados = Object.values(PANTALLAS).flatMap((p) => informesDe(p));
    expect(citados.length).toBe(13);
    expect([...new Set(citados)].sort()).toEqual([...PUBLICADOS_UI].sort());
    expect(citados.length).toBe(new Set(citados).size);
  });

  it('ningun_slug_de_catalogo_when_se_revisa_aparece_en_cobro_o_movimientos', () => {
    const finanzas = new Set([
      ...informesDe(PANTALLAS['cobro']),
      ...informesDe(PANTALLAS['movimientos']),
    ]);
    for (const slug of SLOTS_CATALOGO) {
      expect(finanzas.has(slug)).toBeFalse();
    }
  });
});
