/** @marker unit */
import {
  PANTALLAS,
  PUBLICADOS_UI,
  RUTA_HTTP,
  SLOTS_COLA,
  SLOTS_CUMPLIMIENTO,
  SLOTS_TENDENCIAS,
  informesDe,
} from './pantallas-gestion.definiciones';

const LISTADOS_SIMPLES = ['tickets', 'escalados'];

describe('Definiciones de pantallas de Soporte al Cliente', () => {
  it('cumplimiento_when_se_declara_cita_exactamente_los_cuatro_de_ot19', () => {
    expect(informesDe(PANTALLAS['cumplimiento']).sort()).toEqual([...SLOTS_CUMPLIMIENTO].sort());
  });

  it('cola_when_se_declara_cita_exactamente_los_tres_de_ot20_ahora', () => {
    expect(informesDe(PANTALLAS['cola']).sort()).toEqual([...SLOTS_COLA].sort());
    expect(PANTALLAS['cola'].apoyo).toBeUndefined();
  });

  it('tendencias_when_se_declara_cita_carga_y_reincidencia', () => {
    expect(informesDe(PANTALLAS['tendencias']).sort()).toEqual([...SLOTS_TENDENCIAS].sort());
    expect(PANTALLAS['tendencias'].heroe.informes).toEqual(['carga-entrante-resuelta']);
    expect(PANTALLAS['tendencias'].visual.informes).toEqual(['carga-entrante-resuelta']);
  });

  it('las_tres_pantallas_when_se_unen_citan_exactamente_los_9', () => {
    const citados = Object.values(PANTALLAS).flatMap((p) => informesDe(p));
    expect([...new Set(citados)].sort()).toEqual([...PUBLICADOS_UI].sort());
    expect(new Set(citados).size).toBe(9);
  });

  it('ningun_slug_when_se_revisa_sale_de_publicados_ni_es_listado_simple', () => {
    const publicados = new Set(PUBLICADOS_UI);
    for (const pantalla of Object.values(PANTALLAS)) {
      for (const slug of informesDe(pantalla)) {
        expect(publicados.has(slug)).toBeTrue();
        expect(LISTADOS_SIMPLES).not.toContain(slug);
      }
    }
  });

  it('por_plan_when_se_mapea_usa_ruta_anidada', () => {
    expect(RUTA_HTTP['cumplimiento-sla-por-plan']).toBe('cumplimiento-sla/por-plan');
  });
});
