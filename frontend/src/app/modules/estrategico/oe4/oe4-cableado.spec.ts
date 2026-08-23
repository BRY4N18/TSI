/** @marker unit */
import { routes } from '../../../app.routes';
import { NAV_LINKS } from '../../../shared/layout/nav-links';
import { OE3_ROUTES } from '../oe3/oe3.routes';
import {
  oe4CalidadGuard,
  oe4CoberturaGuard,
  oe4ConcentracionGuard,
  oe4ImpactoGuard,
} from './guards/oe4.guard';
import { OE4_ROUTES } from './oe4.routes';

describe('cableado OE4', () => {
  it('la_app_registra_estrategico_oe4_aparte_de_oe3', () => {
    const rutas = routes.flatMap((r) => [r, ...(r.children ?? [])]);
    expect(rutas.some((r) => r.path === 'estrategico/oe4')).toBeTrue();
    expect(rutas.some((r) => r.path === 'estrategico/oe3')).toBeTrue();
  });

  it('las_cuatro_rutas_usan_el_guard_correcto', () => {
    const porPath = Object.fromEntries(OE4_ROUTES.map((r) => [r.path, r]));
    expect(porPath['calidad'].canActivate).toEqual([oe4CalidadGuard]);
    expect(porPath['concentracion'].canActivate).toEqual([oe4ConcentracionGuard]);
    expect(porPath['impacto'].canActivate).toEqual([oe4ImpactoGuard]);
    expect(porPath['cobertura'].canActivate).toEqual([oe4CoberturaGuard]);
  });

  it('oe3_no_gana_pantallas_oe4', () => {
    expect(OE3_ROUTES.some((r) => r.path === 'concentracion')).toBeFalse();
  });

  it('sidebar_roles_partidos', () => {
    const calidad = NAV_LINKS.find((l) => l.path === '/estrategico/oe4/calidad');
    const conc = NAV_LINKS.find((l) => l.path === '/estrategico/oe4/concentracion');
    const impacto = NAV_LINKS.find((l) => l.path === '/estrategico/oe4/impacto');
    const cob = NAV_LINKS.find((l) => l.path === '/estrategico/oe4/cobertura');
    expect(calidad?.roles).toEqual(['DirectorDatos', 'DirectorOperaciones', 'Gerente']);
    expect(conc?.roles).toEqual(['DirectorDatos', 'Gerente']);
    expect(impacto?.roles).toEqual(['DirectorDatos', 'DirectorOperaciones', 'Gerente']);
    expect(cob?.roles).toEqual(['DirectorDatos', 'Gerente']);
    expect(conc?.roles).not.toContain('DirectorOperaciones');
    expect(calidad?.group).toBe('Estratégico');
  });
});
