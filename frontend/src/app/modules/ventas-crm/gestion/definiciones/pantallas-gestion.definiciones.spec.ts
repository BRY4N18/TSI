/** @marker unit */
import {
  PANTALLAS,
  PUBLICADOS_UI,
  SLOTS_CAPTACION,
  SLOTS_EMBUDO,
  SLOTS_NUTRICION,
  informesDe,
} from './pantallas-gestion.definiciones';

const LISTADOS_SIMPLES = [
  'prospectos',
  'reasignaciones',
  'demos-activas',
  'notificaciones-enviadas',
];

describe('Definiciones de pantallas de Ventas y CRM', () => {
  it('embudo_when_se_declara_cita_exactamente_los_cinco_de_ot02', () => {
    expect(informesDe(PANTALLAS['embudo']).sort()).toEqual([...SLOTS_EMBUDO].sort());
  });

  it('captacion_when_se_declara_cita_exactamente_los_tres_de_ot01', () => {
    expect(informesDe(PANTALLAS['captacion']).sort()).toEqual([...SLOTS_CAPTACION].sort());
    expect(PANTALLAS['captacion'].apoyo).toBeUndefined();
  });

  it('nutricion_when_se_declara_cita_exactamente_los_cinco_de_ot03', () => {
    expect(informesDe(PANTALLAS['nutricion']).sort()).toEqual([...SLOTS_NUTRICION].sort());
  });

  it('las_tres_pantallas_when_se_unen_citan_exactamente_los_13_una_vez', () => {
    const citados = Object.values(PANTALLAS).flatMap((p) => informesDe(p));
    expect(citados.length).toBe(13);
    expect([...new Set(citados)].sort()).toEqual([...PUBLICADOS_UI].sort());
    expect(citados.length).toBe(new Set(citados).size);
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
});
