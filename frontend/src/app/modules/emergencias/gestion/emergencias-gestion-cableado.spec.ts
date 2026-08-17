/** @marker unit */
import { routes } from '../../../app.routes';
import { NAV_LINKS } from '../../../shared/layout/nav-links';
import { EMERGENCIAS_ROUTES } from '../emergencias.routes';
import { EMERGENCIAS_GESTION_ROUTES } from './emergencias-gestion.routes';
import { emergenciasGestionGuard } from './guards/emergencias-gestion.guard';
import { emergenciasInformesGuard } from '../guards/emergencias-informes.guard';

describe('cableado de gestión de Emergencias', () => {
  it('la_app_registra_emergencias_gestion_aparte_de_los_workpanels', () => {
    const rutas = routes.flatMap((r) => [r, ...(r.children ?? [])]);
    expect(rutas.some((r) => r.path === 'emergencias/gestion')).toBeTrue();
    expect(rutas.some((r) => r.path === 'emergencias')).toBeTrue();
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

  it('los_workpanels_siguen_con_el_guard_de_operador', () => {
    for (const ruta of EMERGENCIAS_ROUTES) {
      expect(ruta.canActivate).toContain(emergenciasInformesGuard);
      expect(ruta.canActivate).not.toContain(emergenciasGestionGuard);
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

  it('los_enlaces_de_workpanel_no_cambiaron_de_rol', () => {
    const workpanels = NAV_LINKS.filter((l) =>
      ['/emergencias/informes/registro', '/emergencias/informes/despacho', '/emergencias/informes/seguimiento'].includes(
        l.path,
      ),
    );
    expect(workpanels.length).toBe(3);
    for (const link of workpanels) {
      expect(link.roles).toEqual(['Operador', 'Administrador']);
    }
  });
});
