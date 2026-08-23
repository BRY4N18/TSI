/** @marker unit */
import { routes } from '../../../app.routes';
import { NAV_LINKS } from '../../../shared/layout/nav-links';
import { RED_OPERATIVA_INFORMES_ROUTES } from '../informes/red-operativa-informes.routes';
import { informesFlotaGuard } from '../informes/guards/informes-red-operativa.guard';
import { RED_OPERATIVA_GESTION_ROUTES } from './red-operativa-gestion.routes';
import {
  gestionCrecimientoGuard,
  gestionValidacionGuard,
} from './guards/red-operativa-gestion.guard';

describe('cableado de gestión de Red Operativa', () => {
  it('la_app_registra_gestion_aparte_de_los_listados', () => {
    const rutas = routes.flatMap((r) => [r, ...(r.children ?? [])]);
    expect(rutas.some((r) => r.path === 'red-operativa/gestion')).toBeTrue();
    expect(rutas.some((r) => r.path === 'red-operativa/informes')).toBeTrue();
  });

  it('flota_y_mercados_usan_crecimiento_validacion_usa_el_otro', () => {
    const porPath = Object.fromEntries(
      RED_OPERATIVA_GESTION_ROUTES.map((r) => [r.path, r]),
    );
    expect(porPath['flota'].canActivate).toEqual([gestionCrecimientoGuard]);
    expect(porPath['mercados'].canActivate).toEqual([gestionCrecimientoGuard]);
    expect(porPath['validacion'].canActivate).toEqual([gestionValidacionGuard]);
    expect(porPath['flota'].canActivate).not.toContain(gestionValidacionGuard);
    expect(porPath['validacion'].canActivate).not.toContain(gestionCrecimientoGuard);
  });

  it('los_listados_siguen_con_sus_guards_y_no_ganan_pantallas_z', () => {
    expect(RED_OPERATIVA_INFORMES_ROUTES.some((r) => r.path === 'flota')).toBeFalse();
    expect(RED_OPERATIVA_INFORMES_ROUTES[0].canActivate).toContain(informesFlotaGuard);
    for (const ruta of RED_OPERATIVA_INFORMES_ROUTES) {
      expect(ruta.canActivate).not.toContain(gestionCrecimientoGuard);
      expect(ruta.canActivate).not.toContain(gestionValidacionGuard);
    }
  });

  it('el_sidebar_reparte_enlaces_por_materia', () => {
    const flota = NAV_LINKS.find((l) => l.path === '/red-operativa/gestion/flota');
    const mercados = NAV_LINKS.find((l) => l.path === '/red-operativa/gestion/mercados');
    const validacion = NAV_LINKS.find((l) => l.path === '/red-operativa/gestion/validacion');
        // ⚠️ Sin `Administrador`: la gestión es de la autoridad del departamento.
    expect(flota?.roles).toEqual(['DirectorExpansion']);
    expect(mercados?.roles).toEqual(['DirectorExpansion']);
    expect(validacion?.roles).toEqual(['DirectorTecnologico']);
    expect(flota?.roles).not.toContain('DirectorTecnologico');
    expect(validacion?.roles).not.toContain('DirectorExpansion');
  });

  it('el_enlace_de_listados_no_cambio_de_roles', () => {
    const listados = NAV_LINKS.find((l) => l.path === '/red-operativa/informes');
    expect(listados?.roles).toEqual([
      'Administrador',
      'DirectorExpansion',
      'DirectorTecnologico',
      'Cliente',
      'Proveedor',
    ]);
  });
});
