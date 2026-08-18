/** @marker unit */
import { routes } from '../../../app.routes';
import { NAV_LINKS } from '../../../shared/layout/nav-links';
import { CUENTAS_CLIENTES_INFORMES_ROUTES } from '../informes/cuentas-clientes-informes.routes';
import { GESTION_CUENTA_ROUTES } from '../gestion-cuenta/gestion-cuenta.routes';
import {
  gestionAccesoGuard,
  gestionCicloGuard,
  gestionIncorporacionGuard,
} from './guards/cuentas-gestion.guard';
import { CUENTAS_GESTION_ROUTES } from './cuentas-gestion.routes';

describe('cableado de gestión de Cuentas', () => {
  it('la_app_registra_gestion_aparte_de_listados_y_cuenta', () => {
    const rutas = routes.flatMap((r) => [r, ...(r.children ?? [])]);
    expect(rutas.some((r) => r.path === 'cuentas-clientes/gestion')).toBeTrue();
    expect(rutas.some((r) => r.path === 'cuentas-clientes/informes')).toBeTrue();
    expect(rutas.some((r) => r.path === 'cuentas-clientes/gestion-cuenta')).toBeTrue();
  });

  it('ciclo_e_incorporacion_usan_admin_acceso_usa_el_otro', () => {
    const porPath = Object.fromEntries(CUENTAS_GESTION_ROUTES.map((r) => [r.path, r]));
    expect(porPath['ciclo'].canActivate).toEqual([gestionCicloGuard]);
    expect(porPath['incorporacion'].canActivate).toEqual([gestionIncorporacionGuard]);
    expect(porPath['acceso'].canActivate).toEqual([gestionAccesoGuard]);
    expect(porPath['ciclo'].canActivate).not.toContain(gestionAccesoGuard);
    expect(porPath['acceso'].canActivate).not.toContain(gestionCicloGuard);
  });

  it('los_listados_y_gestion_cuenta_no_ganan_pantallas_z', () => {
    expect(CUENTAS_CLIENTES_INFORMES_ROUTES.some((r) => r.path === 'ciclo')).toBeFalse();
    expect(GESTION_CUENTA_ROUTES.some((r) => r.path === 'ciclo')).toBeFalse();
  });

  it('el_sidebar_reparte_enlaces_por_materia', () => {
    const ciclo = NAV_LINKS.find((l) => l.path === '/cuentas-clientes/gestion/ciclo');
    const incorporacion = NAV_LINKS.find(
      (l) => l.path === '/cuentas-clientes/gestion/incorporacion',
    );
    const acceso = NAV_LINKS.find((l) => l.path === '/cuentas-clientes/gestion/acceso');
    expect(ciclo?.roles).toEqual(['Administrador']);
    expect(incorporacion?.roles).toEqual(['Administrador']);
    expect(acceso?.roles).toEqual(['DirectorTecnologico', 'Administrador']);
    expect(ciclo?.roles).not.toContain('DirectorTecnologico');
  });

  it('el_enlace_de_listados_sigue_admitiendo_al_tecnologico', () => {
    const listados = NAV_LINKS.find((l) => l.path === '/cuentas-clientes/informes');
    expect(listados?.roles).toEqual(['Administrador', 'DirectorTecnologico']);
  });
});
