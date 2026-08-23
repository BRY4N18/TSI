/** @marker unit */
import { routes } from '../../../app.routes';
import { NAV_LINKS } from '../../../shared/layout/nav-links';
import { informesFinanzasGuard } from '../informes/guards/informes-suscripciones.guard';
import { SUSCRIPCIONES_INFORMES_ROUTES } from '../informes/suscripciones-informes.routes';
import {
  gestionCatalogoGuard,
  gestionFinanzasGuard,
} from './guards/suscripciones-gestion.guard';
import { SUSCRIPCIONES_GESTION_ROUTES } from './suscripciones-gestion.routes';

describe('cableado de gestión de Suscripciones', () => {
  it('la_app_registra_gestion_aparte_de_los_listados', () => {
    const rutas = routes.flatMap((r) => [r, ...(r.children ?? [])]);
    expect(rutas.some((r) => r.path === 'suscripciones/gestion')).toBeTrue();
    expect(rutas.some((r) => r.path === 'suscripciones/informes')).toBeTrue();
  });

  it('cobro_y_movimientos_usan_finanzas_catalogo_usa_el_otro', () => {
    const porPath = Object.fromEntries(SUSCRIPCIONES_GESTION_ROUTES.map((r) => [r.path, r]));
    expect(porPath['cobro'].canActivate).toEqual([gestionFinanzasGuard]);
    expect(porPath['movimientos'].canActivate).toEqual([gestionFinanzasGuard]);
    expect(porPath['catalogo'].canActivate).toEqual([gestionCatalogoGuard]);
    expect(porPath['cobro'].canActivate).not.toContain(gestionCatalogoGuard);
    expect(porPath['catalogo'].canActivate).not.toContain(gestionFinanzasGuard);
  });

  it('los_listados_siguen_con_sus_guards_y_no_ganan_pantallas_z', () => {
    expect(SUSCRIPCIONES_INFORMES_ROUTES.some((r) => r.path === 'cobro')).toBeFalse();
    expect(SUSCRIPCIONES_INFORMES_ROUTES.some((r) => r.canActivate?.includes(informesFinanzasGuard))).toBeTrue();
    for (const ruta of SUSCRIPCIONES_INFORMES_ROUTES) {
      expect(ruta.canActivate).not.toContain(gestionFinanzasGuard);
      expect(ruta.canActivate).not.toContain(gestionCatalogoGuard);
    }
  });

  it('el_sidebar_reparte_enlaces_por_materia', () => {
    const cobro = NAV_LINKS.find((l) => l.path === '/suscripciones/gestion/cobro');
    const movimientos = NAV_LINKS.find((l) => l.path === '/suscripciones/gestion/movimientos');
    const catalogo = NAV_LINKS.find((l) => l.path === '/suscripciones/gestion/catalogo');
        // ⚠️ Sin `Administrador`: la gestión es de la autoridad del departamento.
    expect(cobro?.roles).toEqual(['DirectorFinanciero']);
    expect(movimientos?.roles).toEqual(['DirectorFinanciero']);
    expect(catalogo?.roles).toEqual(['DirectorEstrategia']);
    expect(cobro?.roles).not.toContain('DirectorEstrategia');
    expect(catalogo?.roles).not.toContain('DirectorFinanciero');
  });

  it('el_enlace_de_listados_no_cambio_de_roles', () => {
    const listados = NAV_LINKS.find((l) => l.path === '/suscripciones/informes');
    expect(listados?.roles).toEqual([
      'Administrador',
      'DirectorEstrategia',
      'DirectorFinanciero',
      'Cliente',
      'Proveedor',
    ]);
  });
});
