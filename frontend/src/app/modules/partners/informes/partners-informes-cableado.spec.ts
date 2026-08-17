/** @marker unit */
import { routes } from '../../../app.routes';
import { NAV_LINKS } from '../../../shared/layout/nav-links';
import { PARTNERS_ROUTES } from '../partners.routes';
import { PARTNERS_INFORMES_ROUTES } from './partners-informes.routes';
import { informesAccesoGuard, informesContratoGuard } from './guards/informes-partners.guard';

describe('cableado de informes de Partners y API', () => {
  it('la_app_registra_informes_antes_que_el_modulo_operativo', () => {
    const rutas = routes.flatMap((r) => [r, ...(r.children ?? [])]);
    const paths = rutas.map((r) => r.path);
    expect(paths).toContain('partners/informes');
    expect(paths).toContain('partners');
    expect(paths.indexOf('partners/informes')).toBeLessThan(paths.indexOf('partners'));
  });

  it('contrato_usa_su_guard_acceso_e_indice_el_amplio', () => {
    const porPath = Object.fromEntries(PARTNERS_INFORMES_ROUTES.map((r) => [r.path, r]));
    expect(porPath[''].canActivate).toEqual([informesAccesoGuard]);
    expect(porPath[':informe'].canActivate).toEqual([informesAccesoGuard]);
    expect(porPath['versiones-contrato'].canActivate).toEqual([informesContratoGuard]);
    expect(porPath['alcance-datos'].canActivate).toEqual([informesContratoGuard]);
    expect(porPath['versiones-contrato'].canActivate).not.toContain(informesAccesoGuard);
  });

  it('el_modulo_operativo_no_gana_hijos_de_informes_ni_cambia_el_redirect', () => {
    expect(PARTNERS_ROUTES.some((r) => r.path === 'informes')).toBeFalse();
    expect(PARTNERS_ROUTES.some((r) => (r.path ?? '').includes('informes'))).toBeFalse();
    const raiz = PARTNERS_ROUTES.find((r) => r.path === '' || r.redirectTo);
    expect(raiz?.redirectTo).toBe('consola');
  });

  it('el_sidebar_tiene_dos_entradas_misma_ruta_roles_disjuntos', () => {
    const items = NAV_LINKS.filter((l) => l.path === '/partners/informes');
    expect(items.length).toBe(2);
    const gestores = items.find((l) => l.label === 'Informes de partners');
    const partner = items.find((l) => l.label === 'Estado de mi acceso');
    expect(gestores?.roles).toEqual(['Administrador', 'DesarrolladorAPIs', 'DirectorTecnologico']);
    expect(partner?.roles).toEqual(['PartnerIntegracion']);
    expect(gestores?.roles).not.toContain('PartnerIntegracion');
    expect(partner?.roles).not.toContain('Administrador');
  });

  it('consola_portal_y_logs_no_cambiaron_de_roles', () => {
    expect(NAV_LINKS.find((l) => l.path === '/partners/consola')?.roles).toEqual([
      'Administrador',
      'DesarrolladorAPIs',
    ]);
    expect(NAV_LINKS.find((l) => l.path === '/partners/portal')?.roles).toEqual([
      'PartnerIntegracion',
    ]);
    expect(NAV_LINKS.find((l) => l.path === '/partners/consola/logs')?.roles).toEqual([
      'Administrador',
      'DesarrolladorAPIs',
    ]);
  });
});
