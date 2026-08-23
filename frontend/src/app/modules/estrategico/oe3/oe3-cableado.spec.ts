/** @marker unit */
import { routes } from '../../../app.routes';
import { NAV_LINKS } from '../../../shared/layout/nav-links';
import { OE6_ROUTES } from '../oe6/oe6.routes';
import {
  oe3CalidadGuard,
  oe3CapacidadGuard,
  oe3LatenciaGuard,
  oe3RespaldoGuard,
} from './guards/oe3.guard';
import { OE3_ROUTES } from './oe3.routes';

describe('cableado OE3', () => {
  it('la_app_registra_estrategico_oe3_aparte_de_oe6', () => {
    const rutas = routes.flatMap((r) => [r, ...(r.children ?? [])]);
    expect(rutas.some((r) => r.path === 'estrategico/oe3')).toBeTrue();
    expect(rutas.some((r) => r.path === 'estrategico/oe6')).toBeTrue();
  });

  it('las_cuatro_rutas_usan_el_guard_correcto', () => {
    const porPath = Object.fromEntries(OE3_ROUTES.map((r) => [r.path, r]));
    expect(porPath['latencia'].canActivate).toEqual([oe3LatenciaGuard]);
    expect(porPath['calidad'].canActivate).toEqual([oe3CalidadGuard]);
    expect(porPath['capacidad'].canActivate).toEqual([oe3CapacidadGuard]);
    expect(porPath['respaldo'].canActivate).toEqual([oe3RespaldoGuard]);
  });

  it('oe6_no_gana_pantallas_oe3', () => {
    expect(OE6_ROUTES.some((r) => r.path === 'latencia')).toBeFalse();
    expect(OE6_ROUTES.some((r) => r.path === 'capacidad')).toBeFalse();
  });

  it('sidebar_roles_partidos_sin_tecnologico_ni_partner', () => {
    const latencia = NAV_LINKS.find((l) => l.path === '/estrategico/oe3/latencia');
    const calidad = NAV_LINKS.find((l) => l.path === '/estrategico/oe3/calidad');
    const capacidad = NAV_LINKS.find((l) => l.path === '/estrategico/oe3/capacidad');
    const respaldo = NAV_LINKS.find((l) => l.path === '/estrategico/oe3/respaldo');
    expect(latencia?.roles).toEqual(['DirectorOperaciones', 'Gerente']);
    expect(calidad?.roles).toEqual(['DirectorOperaciones', 'Gerente']);
    expect(capacidad?.roles).toEqual(['DirectorExpansion', 'DirectorOperaciones', 'Gerente']);
    expect(respaldo?.roles).toEqual(['DirectorExpansion', 'Gerente']);
    expect(respaldo?.roles).not.toContain('DirectorOperaciones');
    expect(latencia?.roles).not.toContain('DirectorTecnologico');
    expect(latencia?.roles).not.toContain('PartnerIntegracion');
    expect(latencia?.group).toBe('Estratégico');
  });

  it('oe6_sidebar_no_cambio', () => {
    const llegada = NAV_LINKS.find((l) => l.path === '/estrategico/oe6/llegada');
    expect(llegada?.roles).toEqual(['DirectorOperaciones', 'Gerente']);
  });
});
