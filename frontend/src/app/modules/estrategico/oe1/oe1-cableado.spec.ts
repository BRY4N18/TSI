/** @marker unit */
import { routes } from '../../../app.routes';
import { NAV_LINKS } from '../../../shared/layout/nav-links';
import { PARTNERS_GESTION_ROUTES } from '../../partners/gestion/partners-gestion.routes';
import { SUSCRIPCIONES_ROUTES } from '../../suscripciones/suscripciones.routes';
import { VENTAS_CRM_ROUTES } from '../../ventas-crm/ventas-crm.routes';
import { OE2_ROUTES } from '../oe2/oe2.routes';
import {
  oe1CaptacionGuard,
  oe1CarteraGuard,
  oe1CicloGuard,
  oe1IngresoGuard,
} from './guards/oe1.guard';
import { OE1_ROUTES } from './oe1.routes';

describe('cableado OE1', () => {
  it('la_app_registra_estrategico_oe1_aparte_de_oe2_y_tactico', () => {
    const rutas = routes.flatMap((r) => [r, ...(r.children ?? [])]);
    expect(rutas.some((r) => r.path === 'estrategico/oe1')).toBeTrue();
    expect(rutas.some((r) => r.path === 'estrategico/oe2')).toBeTrue();
    expect(rutas.some((r) => r.path === 'suscripciones')).toBeTrue();
  });

  it('las_cuatro_rutas_usan_el_guard_correcto', () => {
    const porPath = Object.fromEntries(OE1_ROUTES.map((r) => [r.path, r]));
    expect(porPath['ingreso'].canActivate).toEqual([oe1IngresoGuard]);
    expect(porPath['cartera'].canActivate).toEqual([oe1CarteraGuard]);
    expect(porPath['captacion'].canActivate).toEqual([oe1CaptacionGuard]);
    expect(porPath['ciclo'].canActivate).toEqual([oe1CicloGuard]);
  });

  it('oe2_y_tactico_no_ganan_pantallas_oe1', () => {
    expect(OE2_ROUTES.some((r) => r.path === 'ingreso')).toBeFalse();
    expect(PARTNERS_GESTION_ROUTES.some((r) => r.path === 'ingreso')).toBeFalse();
    expect(SUSCRIPCIONES_ROUTES.some((r) => r.path === 'ingreso')).toBeFalse();
    expect(VENTAS_CRM_ROUTES.some((r) => r.path === 'captacion')).toBeFalse();
  });

  it('sidebar_roles_partidos_sin_partner', () => {
    const ingreso = NAV_LINKS.find((l) => l.path === '/estrategico/oe1/ingreso');
    expect(ingreso?.roles).toEqual(['DirectorFinanciero', 'Gerente']);
    const cartera = NAV_LINKS.find((l) => l.path === '/estrategico/oe1/cartera');
    expect(cartera?.roles).toEqual(['DirectorEstrategia', 'Gerente']);
    const captacion = NAV_LINKS.find((l) => l.path === '/estrategico/oe1/captacion');
    expect(captacion?.roles).toEqual(['DirectorMarketing', 'Gerente']);
    const ciclo = NAV_LINKS.find((l) => l.path === '/estrategico/oe1/ciclo');
    expect(ciclo?.roles).toEqual(['Gerente']);
    for (const path of [
      '/estrategico/oe1/ingreso',
      '/estrategico/oe1/cartera',
      '/estrategico/oe1/captacion',
      '/estrategico/oe1/ciclo',
    ]) {
      const link = NAV_LINKS.find((l) => l.path === path);
      expect(link?.roles).not.toContain('PartnerIntegracion');
      expect(link?.roles).not.toContain('Administrador');
      expect(link?.group).toBe('Estratégico');
    }
  });

  it('oe2_sidebar_no_cambio', () => {
    const uso = NAV_LINKS.find((l) => l.path === '/estrategico/oe2/uso');
    expect(uso?.roles).toEqual(['DirectorTecnologico', 'Gerente']);
  });
});
