/** @marker unit */
import { routes } from '../../../app.routes';
import { NAV_LINKS } from '../../../shared/layout/nav-links';
import { informesVentasGuard } from '../informes/guards/informes-ventas-crm.guard';
import { VENTAS_CRM_INFORMES_ROUTES } from '../informes/ventas-crm-informes.routes';
import { ventasCrmGestionGuard } from './guards/ventas-crm-gestion.guard';
import { VENTAS_CRM_GESTION_ROUTES } from './ventas-crm-gestion.routes';

// ⚠️ Sin `Administrador`: la gestión es de la autoridad del departamento.
const ROLES_GESTION = ['DirectorMarketing', 'GerenteVentas'];

describe('cableado de gestión de Ventas y CRM', () => {
  it('la_app_registra_gestion_aparte_de_los_listados', () => {
    const rutas = routes.flatMap((r) => [r, ...(r.children ?? [])]);
    expect(rutas.some((r) => r.path === 'ventas-crm/gestion')).toBeTrue();
    expect(rutas.some((r) => r.path === 'ventas-crm/informes')).toBeTrue();
  });

  it('las_tres_rutas_de_gestion_usan_el_guard_de_compuestos', () => {
    expect(VENTAS_CRM_GESTION_ROUTES.map((r) => r.path)).toEqual([
      'embudo',
      'captacion',
      'nutricion',
    ]);
    for (const ruta of VENTAS_CRM_GESTION_ROUTES) {
      expect(ruta.canActivate).toEqual([ventasCrmGestionGuard]);
    }
  });

  it('los_listados_siguen_con_sus_guards_y_no_ganan_pantallas_z', () => {
    expect(VENTAS_CRM_INFORMES_ROUTES.some((r) => r.path === 'embudo')).toBeFalse();
    expect(VENTAS_CRM_INFORMES_ROUTES.some((r) => r.path === 'captacion')).toBeFalse();
    expect(VENTAS_CRM_INFORMES_ROUTES.some((r) => r.path === 'nutricion')).toBeFalse();
    expect(VENTAS_CRM_INFORMES_ROUTES[0].canActivate).toContain(informesVentasGuard);
    for (const ruta of VENTAS_CRM_INFORMES_ROUTES) {
      expect(ruta.canActivate).not.toContain(ventasCrmGestionGuard);
    }
  });

  it('el_sidebar_reparte_enlaces_sin_cuentas_publicas', () => {
    const paths = [
      '/ventas-crm/gestion/embudo',
      '/ventas-crm/gestion/captacion',
      '/ventas-crm/gestion/nutricion',
    ];
    for (const path of paths) {
      const link = NAV_LINKS.find((l) => l.path === path);
      expect(link?.roles).toEqual(ROLES_GESTION);
      expect(link?.roles).not.toContain('GerenteCuentasPublicas');
      expect(link?.group).toBe('Ventas CRM');
    }
  });

  it('el_enlace_de_listados_sigue_admitiendo_cuentas_publicas', () => {
    const listados = NAV_LINKS.find((l) => l.path === '/ventas-crm/informes');
    expect(listados?.roles).toEqual([
      'Administrador',
      'DirectorMarketing',
      'GerenteVentas',
      'GerenteCuentasPublicas',
    ]);
  });
});
