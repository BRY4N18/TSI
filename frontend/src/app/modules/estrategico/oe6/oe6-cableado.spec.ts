/** @marker unit */
import { routes } from '../../../app.routes';
import { NAV_LINKS } from '../../../shared/layout/nav-links';
import { OE5_ROUTES } from '../oe5/oe5.routes';
import { oe6Guard } from './guards/oe6.guard';
import { OE6_ROUTES } from './oe6.routes';

describe('cableado OE6', () => {
  it('la_app_registra_estrategico_oe6_aparte_de_oe5', () => {
    const rutas = routes.flatMap((r) => [r, ...(r.children ?? [])]);
    expect(rutas.some((r) => r.path === 'estrategico/oe6')).toBeTrue();
    expect(rutas.some((r) => r.path === 'estrategico/oe5')).toBeTrue();
  });

  it('las_cuatro_rutas_usan_el_mismo_guard', () => {
    const porPath = Object.fromEntries(OE6_ROUTES.map((r) => [r.path, r]));
    expect(porPath['llegada'].canActivate).toEqual([oe6Guard]);
    expect(porPath['diagnostico'].canActivate).toEqual([oe6Guard]);
    expect(porPath['ejecucion'].canActivate).toEqual([oe6Guard]);
    expect(porPath['personas'].canActivate).toEqual([oe6Guard]);
  });

  it('oe5_no_gana_pantallas_oe6', () => {
    expect(OE5_ROUTES.some((r) => r.path === 'llegada')).toBeFalse();
  });

  it('sidebar_mismos_roles_sin_partner', () => {
    for (const path of [
      '/estrategico/oe6/llegada',
      '/estrategico/oe6/diagnostico',
      '/estrategico/oe6/ejecucion',
      '/estrategico/oe6/personas',
    ]) {
      const link = NAV_LINKS.find((l) => l.path === path);
      expect(link?.roles).toEqual(['DirectorOperaciones', 'Gerente']);
      expect(link?.roles).not.toContain('PartnerIntegracion');
      expect(link?.roles).not.toContain('DirectorFinanciero');
      expect(link?.group).toBe('Estratégico');
    }
  });

  it('oe5_sidebar_no_cambio', () => {
    const servicio = NAV_LINKS.find((l) => l.path === '/estrategico/oe5/servicio');
    expect(servicio?.roles).toEqual(['GerenteExitoCliente', 'Gerente']);
  });
});
