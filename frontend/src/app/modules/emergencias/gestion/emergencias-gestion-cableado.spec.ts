/** @marker unit */
import { routes } from '../../../app.routes';
import { NAV_LINKS } from '../../../shared/layout/nav-links';
import { EMERGENCIAS_GESTION_ROUTES } from './emergencias-gestion.routes';
import { emergenciasGestionGuard } from './guards/emergencias-gestion.guard';

describe('cableado de gestión de Emergencias', () => {
  it('la_app_registra_emergencias_gestion', () => {
    const rutas = routes.flatMap((r) => [r, ...(r.children ?? [])]);
    expect(rutas.some((r) => r.path === 'emergencias/gestion')).toBeTrue();
  });

  it('los_workpanels_agregados_ya_no_estan_registrados', () => {
    // Los tres informes agregados (registro, despacho, seguimiento) se
    // retiraron el 2026-08-19: leían Pinot directamente y quedaron sustituidos
    // por los listados de casos y las pantallas de gestión. Se comprueba que la
    // ruta no vuelva por descuido, porque su guard y sus vistas ya no existen.
    const rutas = routes.flatMap((r) => [r, ...(r.children ?? [])]);
    expect(rutas.some((r) => r.path === 'emergencias')).toBeFalse();
  });

  it('las_tres_rutas_de_gestion_usan_el_guard_del_director', () => {
    expect(EMERGENCIAS_GESTION_ROUTES.map((r) => r.path)).toEqual([
      'calidad',
      'despacho',
      'cierre',
    ]);
    for (const ruta of EMERGENCIAS_GESTION_ROUTES) {
      expect(ruta.canActivate).toContain(emergenciasGestionGuard);
    }
  });

  it('el_operador_no_ve_los_enlaces_de_gestion', () => {
    const gestion = NAV_LINKS.filter((l) => l.path.startsWith('/emergencias/gestion'));
    expect(gestion.length).toBe(3);
    for (const link of gestion) {
      expect(link.roles).not.toContain('Operador');
      expect(link.roles).toContain('DirectorOperaciones');
    }
  });

  it('los_tres_workpanels_retirados_no_vuelven_al_sidebar', () => {
    // ⚠️ Esta prueba cambió de sentido, no se borró. Vigilaba que los tres
    // workpanels agregados de Emergencias conservaran sus roles; los tres se
    // **retiraron** el 2026-08-22 por estar mal planteados, y lo que vale la
    // pena vigilar ahora es que nadie los reintroduzca sin querer.
    const retirados = NAV_LINKS.filter((l) =>
      [
        '/emergencias/informes/registro',
        '/emergencias/informes/despacho',
        '/emergencias/informes/seguimiento',
      ].includes(l.path),
    );

    expect(retirados).toEqual([]);
  });
});
