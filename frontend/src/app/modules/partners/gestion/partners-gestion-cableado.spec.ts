/** @marker unit */
import { routes } from '../../../app.routes';
import { NAV_LINKS } from '../../../shared/layout/nav-links';
import { PARTNERS_INFORMES_ROUTES } from '../informes/partners-informes.routes';
import { PARTNERS_ROUTES } from '../partners.routes';
import { partnersGestionGuard } from './guards/partners-gestion.guard';
import { PARTNERS_GESTION_ROUTES } from './partners-gestion.routes';

describe('cableado de gestión de Partners', () => {
  it('la_app_registra_gestion_aparte_de_los_listados', () => {
    const rutas = routes.flatMap((r) => [r, ...(r.children ?? [])]);
    expect(rutas.some((r) => r.path === 'partners/gestion')).toBeTrue();
    expect(rutas.some((r) => r.path === 'partners/informes')).toBeTrue();
  });

  it('las_tres_rutas_usan_el_guard_de_gestion', () => {
    const porPath = Object.fromEntries(PARTNERS_GESTION_ROUTES.map((r) => [r.path, r]));
    expect(porPath['consumo'].canActivate).toEqual([partnersGestionGuard]);
    expect(porPath['incorporacion'].canActivate).toEqual([partnersGestionGuard]);
    expect(porPath['entrega'].canActivate).toEqual([partnersGestionGuard]);
  });

  it('los_listados_y_la_consola_no_ganan_pantallas_z', () => {
    expect(PARTNERS_INFORMES_ROUTES.some((r) => r.path === 'consumo')).toBeFalse();
    expect(PARTNERS_ROUTES.some((r) => r.path === 'gestion')).toBeFalse();
    for (const ruta of PARTNERS_INFORMES_ROUTES) {
      expect(ruta.canActivate).not.toContain(partnersGestionGuard);
    }
  });

  it('el_sidebar_no_incluye_partner_ni_desarrollador_en_gestion', () => {
    for (const path of [
      '/partners/gestion/consumo',
      '/partners/gestion/incorporacion',
      '/partners/gestion/entrega',
    ]) {
      const link = NAV_LINKS.find((l) => l.path === path);
      expect(link?.roles).toEqual(['DirectorTecnologico', 'Administrador']);
      expect(link?.roles).not.toContain('PartnerIntegracion');
      expect(link?.roles).not.toContain('DesarrolladorAPIs');
    }
  });

  it('el_enlace_de_listados_no_cambio_de_roles', () => {
    const listados = NAV_LINKS.find(
      (l) => l.path === '/partners/informes' && l.label === 'Informes de partners',
    );
    expect(listados?.roles).toEqual([
      'Administrador',
      'DesarrolladorAPIs',
      'DirectorTecnologico',
    ]);
  });

  it('el_reporte_operativo_sigue_con_admin_y_desarrollador', () => {
    const reporte = NAV_LINKS.find((l) => l.path === '/partners/consola/reportes');
    expect(reporte?.roles).toEqual(['Administrador', 'DesarrolladorAPIs']);
  });
});
