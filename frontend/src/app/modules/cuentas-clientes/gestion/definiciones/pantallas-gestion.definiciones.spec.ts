/** @marker unit */
import {
  PANTALLAS,
  PUBLICADOS_UI,
  SLOTS_ACCESO,
  SLOTS_CICLO,
  SLOTS_INCORPORACION,
  informesDe,
} from './pantallas-gestion.definiciones';

describe('Definiciones de pantallas de Cuentas', () => {
  it('ciclo_when_declara_materia_son_los_cuatro_de_ot17', () => {
    expect(PANTALLAS['ciclo'].materia).toBe('ciclo');
    expect(informesDe(PANTALLAS['ciclo']).sort()).toEqual([...SLOTS_CICLO].sort());
  });

  it('incorporacion_when_declara_son_exactamente_los_tres_de_ot04', () => {
    expect(PANTALLAS['incorporacion'].materia).toBe('incorporacion');
    expect(informesDe(PANTALLAS['incorporacion']).sort()).toEqual(
      [...SLOTS_INCORPORACION].sort(),
    );
  });

  it('acceso_when_declara_comparte_concurrencia_en_heroe_visual_y_apoyo', () => {
    expect(PANTALLAS['acceso'].materia).toBe('acceso');
    expect(informesDe(PANTALLAS['acceso']).sort()).toEqual([...SLOTS_ACCESO].sort());
    expect(PANTALLAS['acceso'].heroe.informes).toEqual(['concurrencia-sesiones']);
    expect(PANTALLAS['acceso'].visual.informes).toEqual(['concurrencia-sesiones']);
    // ⚠️ Acceso **no tiene zona de lectura**: `roles-incompatibles` se retiró el
    // 2026-08-23 porque no podía devolver una fila —los pares de roles llegaban
    // por parámetro y ninguna pantalla los enviaba—. Rellenarla con
    // `concurrencia-sesiones` por cuarta vez sería relleno, no información.
    expect(PANTALLAS['acceso'].lectura).toBeUndefined();
  });

  it('las_tres_pantallas_when_se_unen_citan_exactamente_los_8_una_vez', () => {
    const citados = Object.values(PANTALLAS).flatMap((p) => informesDe(p));
    expect([...new Set(citados)].sort()).toEqual([...PUBLICADOS_UI].sort());
    expect(new Set(citados).size).toBe(8);
  });

  it('ningun_slug_de_listados_when_se_revisa', () => {
    const todos = new Set(Object.values(PANTALLAS).flatMap((p) => informesDe(p)));
    expect(todos.has('accesos-tecnicos')).toBeFalse();
    expect(todos.has('cuentas')).toBeFalse();
    expect(todos.has('sesiones')).toBeFalse();
  });
});
