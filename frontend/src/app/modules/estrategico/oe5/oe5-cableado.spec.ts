/** @marker unit */
import { routes } from '../../../app.routes';
import { NAV_LINKS } from '../../../shared/layout/nav-links';
import { OE1_ROUTES } from '../oe1/oe1.routes';
import { OE2_ROUTES } from '../oe2/oe2.routes';
import {
  oe5IngresosGuard,
  oe5PlanesGuard,
  oe5RiesgoGuard,
  oe5ServicioGuard,
} from './guards/oe5.guard';
import { OE5_ROUTES } from './oe5.routes';

describe('cableado OE5', () => {
  it('la_app_registra_estrategico_oe5_aparte_de_oe1_y_oe2', () => {
    const rutas = routes.flatMap((r) => [r, ...(r.children ?? [])]);
    expect(rutas.some((r) => r.path === 'estrategico/oe5')).toBeTrue();
    expect(rutas.some((r) => r.path === 'estrategico/oe1')).toBeTrue();
    expect(rutas.some((r) => r.path === 'estrategico/oe2')).toBeTrue();
  });

  it('las_cuatro_rutas_usan_el_guard_correcto', () => {
    const porPath = Object.fromEntries(OE5_ROUTES.map((r) => [r.path, r]));
    expect(porPath['servicio'].canActivate).toEqual([oe5ServicioGuard]);
    expect(porPath['ingresos'].canActivate).toEqual([oe5IngresosGuard]);
    expect(porPath['planes'].canActivate).toEqual([oe5PlanesGuard]);
    expect(porPath['riesgo'].canActivate).toEqual([oe5RiesgoGuard]);
  });

  it('oe1_y_oe2_no_ganan_pantallas_oe5', () => {
    expect(OE1_ROUTES.some((r) => r.path === 'servicio')).toBeFalse();
    expect(OE2_ROUTES.some((r) => r.path === 'riesgo')).toBeFalse();
  });

  it('sidebar_roles_partidos_sin_partner', () => {
    const servicio = NAV_LINKS.find((l) => l.path === '/estrategico/oe5/servicio');
    expect(servicio?.roles).toEqual(['GerenteExitoCliente', 'Gerente']);
    const ingresos = NAV_LINKS.find((l) => l.path === '/estrategico/oe5/ingresos');
    expect(ingresos?.roles).toEqual(['DirectorFinanciero', 'Gerente']);
    const planes = NAV_LINKS.find((l) => l.path === '/estrategico/oe5/planes');
    expect(planes?.roles).toEqual(['DirectorEstrategia', 'Gerente']);
    const riesgo = NAV_LINKS.find((l) => l.path === '/estrategico/oe5/riesgo');
    expect(riesgo?.roles).toEqual(['Gerente']);
    for (const path of [
      '/estrategico/oe5/servicio',
      '/estrategico/oe5/ingresos',
      '/estrategico/oe5/planes',
      '/estrategico/oe5/riesgo',
    ]) {
      const link = NAV_LINKS.find((l) => l.path === path);
      expect(link?.roles).not.toContain('PartnerIntegracion');
      expect(link?.roles).not.toContain('Administrador');
      expect(link?.group).toBe('Estratégico');
    }
  });

  it('oe1_sidebar_no_cambio', () => {
    const ingreso = NAV_LINKS.find((l) => l.path === '/estrategico/oe1/ingreso');
    expect(ingreso?.roles).toEqual(['DirectorFinanciero', 'Gerente']);
  });
});
