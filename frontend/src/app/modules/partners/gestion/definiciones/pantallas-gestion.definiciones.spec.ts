/** @marker unit */
import {
  PANTALLAS,
  PUBLICADOS_UI,
  SLOTS_CONSUMO,
  SLOTS_ENTREGA,
  SLOTS_INCORPORACION,
  informesDe,
} from './pantallas-gestion.definiciones';

describe('Definiciones de pantallas de Partners', () => {
  it('consumo_when_declara_son_exactamente_los_siete_de_ot09', () => {
    expect(informesDe(PANTALLAS['consumo']).sort()).toEqual([...SLOTS_CONSUMO].sort());
  });

  it('incorporacion_when_declara_son_exactamente_los_cuatro_de_ot08', () => {
    expect(informesDe(PANTALLAS['incorporacion']).sort()).toEqual(
      [...SLOTS_INCORPORACION].sort(),
    );
  });

  it('entrega_when_declara_son_exactamente_dos_slugs_y_comparte_integracion', () => {
    expect(informesDe(PANTALLAS['entrega']).sort()).toEqual([...SLOTS_ENTREGA].sort());
    expect(PANTALLAS['entrega'].heroe.informes).toEqual(['clientes-integracion-activa']);
    expect(PANTALLAS['entrega'].lectura.informes).toEqual(['clientes-integracion-activa']);
  });

  it('las_tres_pantallas_when_se_unen_citan_exactamente_los_13_una_vez', () => {
    const citados = Object.values(PANTALLAS).flatMap((p) => informesDe(p));
    expect([...new Set(citados)].sort()).toEqual([...PUBLICADOS_UI].sort());
    expect(new Set(citados).size).toBe(13);
  });

  it('ningun_slug_de_listados_ni_alcance_geografico', () => {
    const todos = new Set(Object.values(PANTALLAS).flatMap((p) => informesDe(p)));
    expect(todos.has('credenciales')).toBeFalse();
    expect(todos.has('alcance-datos')).toBeFalse();
    expect(todos.has('alcance-geografico')).toBeFalse();
  });
});
