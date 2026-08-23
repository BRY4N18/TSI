/** @marker unit */
import { routes } from '../../../app.routes';
import { NAV_LINKS } from '../../../shared/layout/nav-links';
import { agenteSoporteGuard } from '../guards/agente-soporte.guard';
import { SOPORTE_CLIENTE_INFORMES_ROUTES } from '../informes/soporte-cliente-informes.routes';
import { SOPORTE_CLIENTE_ROUTES } from '../soporte-cliente.routes';
import { soporteGestionGuard } from './guards/soporte-gestion.guard';
import { SOPORTE_CLIENTE_GESTION_ROUTES } from './soporte-cliente-gestion.routes';

// ⚠️ Sin `Administrador`: la gestión es de la autoridad del departamento.
const ROLES_GESTION = ['GerenteExitoCliente', 'Soporte'];

describe('cableado de gestión de Soporte al Cliente', () => {
  it('la_app_registra_gestion_aparte_de_los_listados', () => {
    const rutas = routes.flatMap((r) => [r, ...(r.children ?? [])]);
    expect(rutas.some((r) => r.path === 'soporte-cliente/gestion')).toBeTrue();
    expect(rutas.some((r) => r.path === 'soporte-cliente/informes')).toBeTrue();
  });

  it('las_tres_rutas_de_gestion_usan_el_guard_de_compuestos', () => {
    expect(SOPORTE_CLIENTE_GESTION_ROUTES.map((r) => r.path)).toEqual([
      'cumplimiento',
      'cola',
      'tendencias',
    ]);
    for (const ruta of SOPORTE_CLIENTE_GESTION_ROUTES) {
      expect(ruta.canActivate).toEqual([soporteGestionGuard]);
    }
  });

  it('los_listados_siguen_con_sus_guards_y_no_ganan_pantallas_z', () => {
    expect(SOPORTE_CLIENTE_INFORMES_ROUTES.some((r) => r.path === 'cumplimiento')).toBeFalse();
    expect(SOPORTE_CLIENTE_INFORMES_ROUTES.some((r) => r.path === 'cola')).toBeFalse();
    expect(SOPORTE_CLIENTE_INFORMES_ROUTES.some((r) => r.path === 'tendencias')).toBeFalse();
    for (const ruta of SOPORTE_CLIENTE_INFORMES_ROUTES) {
      expect(ruta.canActivate).not.toContain(soporteGestionGuard);
    }
  });

  it('el_dashboard_operativo_sigue_con_el_guard_de_cola', () => {
    const dashboard = SOPORTE_CLIENTE_ROUTES.find((r) => r.path === 'dashboard');
    expect(dashboard?.canActivate).toEqual([agenteSoporteGuard]);
  });

  it('el_sidebar_reparte_enlaces_sin_cliente_ni_dev', () => {
    const paths = [
      '/soporte-cliente/gestion/cumplimiento',
      '/soporte-cliente/gestion/cola',
      '/soporte-cliente/gestion/tendencias',
    ];
    for (const path of paths) {
      const link = NAV_LINKS.find((l) => l.path === path);
      expect(link?.roles).toEqual(ROLES_GESTION);
      expect(link?.roles).not.toContain('Cliente');
      expect(link?.roles).not.toContain('DesarrolladorAPIs');
      expect(link?.group).toBe('Soporte');
    }
  });

  it('el_enlace_de_listados_sigue_admitiendo_cliente', () => {
    const listados = NAV_LINKS.find((l) => l.path === '/soporte-cliente/informes');
    expect(listados?.roles).toContain('Cliente');
  });

  it('el_dashboard_operativo_sigue_con_los_roles_de_cola', () => {
    const dashboard = NAV_LINKS.find((l) => l.path === '/soporte-cliente/dashboard');
    expect(dashboard?.roles).toEqual(['Soporte', 'DesarrolladorAPIs', 'DirectorTecnologico']);
  });
});
