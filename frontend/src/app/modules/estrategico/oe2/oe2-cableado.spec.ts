/** @marker unit */
import { routes } from '../../../app.routes';
import { NAV_LINKS } from '../../../shared/layout/nav-links';
import { PARTNERS_GESTION_ROUTES } from '../../partners/gestion/partners-gestion.routes';
import { oe2DineroGuard, oe2UsoEcosistemaGuard } from './guards/oe2.guard';
import { OE2_ROUTES } from './oe2.routes';

describe('cableado OE2', () => {
  it('la_app_registra_estrategico_oe2_aparte_de_partners_gestion', () => {
    const rutas = routes.flatMap((r) => [r, ...(r.children ?? [])]);
    expect(rutas.some((r) => r.path === 'estrategico/oe2')).toBeTrue();
    expect(rutas.some((r) => r.path === 'partners/gestion')).toBeTrue();
  });

  it('las_tres_rutas_usan_el_guard_correcto', () => {
    const porPath = Object.fromEntries(OE2_ROUTES.map((r) => [r.path, r]));
    expect(porPath['uso'].canActivate).toEqual([oe2UsoEcosistemaGuard]);
    expect(porPath['ecosistema'].canActivate).toEqual([oe2UsoEcosistemaGuard]);
    expect(porPath['dinero'].canActivate).toEqual([oe2DineroGuard]);
  });

  it('partners_gestion_no_gana_pantallas_oe2', () => {
    expect(PARTNERS_GESTION_ROUTES.some((r) => r.path === 'uso')).toBeFalse();
    expect(PARTNERS_GESTION_ROUTES.some((r) => r.path === 'dinero')).toBeFalse();
  });

  it('sidebar_uso_y_ecosistema_sin_financiero_ni_partner', () => {
    for (const path of ['/estrategico/oe2/uso', '/estrategico/oe2/ecosistema']) {
      const link = NAV_LINKS.find((l) => l.path === path);
      expect(link?.roles).toEqual(['DirectorTecnologico', 'Gerente']);
      expect(link?.roles).not.toContain('PartnerIntegracion');
      expect(link?.roles).not.toContain('DirectorFinanciero');
    }
  });

  it('sidebar_dinero_incluye_financiero_y_tecnologico', () => {
    const link = NAV_LINKS.find((l) => l.path === '/estrategico/oe2/dinero');
    expect(link?.roles).toEqual(['DirectorTecnologico', 'Gerente', 'DirectorFinanciero']);
  });

  it('partners_gestion_consumo_no_cambio', () => {
    const link = NAV_LINKS.find((l) => l.path === '/partners/gestion/consumo');
    expect(link?.roles).toEqual(['DirectorTecnologico', 'Administrador']);
  });
});
