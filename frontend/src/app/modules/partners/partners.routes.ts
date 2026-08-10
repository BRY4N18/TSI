import { Routes } from '@angular/router';

import { administradorPromocionGuard } from './guards/administrador-promocion.guard';
import { gestorPartnersGuard } from './guards/gestor-partners.guard';
import { partnerIntegracionGuard } from './guards/partner-integracion.guard';

/**
 * Dos superficies con actores de departamentos distintos (design-system § 5):
 * la consola no se fusiona con el portal ni comparte sidebar.
 *
 * No existe ruta `:idpartner/editar`: el backend no expone PATCH de ficha, así
 * que aplica la variante Ver-only del design-system (FR-UI-003).
 */
export const PARTNERS_ROUTES: Routes = [
  // --- Consola (Administrador · Desarrollador de APIs) ---
  {
    path: 'consola',
    canActivate: [gestorPartnersGuard],
    loadComponent: () =>
      import('./pages/lista-partners/lista-partners.page').then((m) => m.ListaPartnersPage),
  },
  {
    path: 'consola/nuevo',
    canActivate: [gestorPartnersGuard],
    loadComponent: () =>
      import('./pages/detalle-partner/detalle-partner.page').then((m) => m.DetallePartnerPage),
    data: { modo: 'crear' },
  },
  {
    path: 'consola/solicitudes',
    canActivate: [gestorPartnersGuard],
    loadComponent: () =>
      import('./pages/cola-solicitudes/cola-solicitudes.page').then((m) => m.ColaSolicitudesPage),
  },
  {
    // Solo Administrador: si el Desarrollador de APIs llega por URL, se le
    // deniega aquí y no en el submit (FR-UI-011).
    path: 'consola/solicitudes/:idpartner/resolver',
    canActivate: [administradorPromocionGuard],
    loadComponent: () =>
      import('./pages/cola-solicitudes/cola-solicitudes.page').then((m) => m.ColaSolicitudesPage),
    data: { resolver: true },
  },
  {
    path: 'consola/:idpartner',
    canActivate: [gestorPartnersGuard],
    loadComponent: () =>
      import('./pages/detalle-partner/detalle-partner.page').then((m) => m.DetallePartnerPage),
    data: { modo: 'ver' },
  },

  // --- Portal del partner ---
  {
    path: 'portal',
    canActivate: [partnerIntegracionGuard],
    loadComponent: () =>
      import('./pages/mi-integracion/mi-integracion.page').then((m) => m.MiIntegracionPage),
  },
  {
    // Sin parámetros de ruta a propósito: el secreto viaja por estado de
    // navegación en memoria, nunca por la URL (FR-UI-021).
    path: 'portal/credencial-emitida',
    canActivate: [partnerIntegracionGuard],
    loadComponent: () =>
      import('./pages/secreto-emitido/secreto-emitido.page').then((m) => m.SecretoEmitidoPage),
  },
  {
    path: 'portal/contrato',
    canActivate: [partnerIntegracionGuard],
    loadComponent: () =>
      import('./pages/contrato-integracion/contrato-integracion.page').then(
        (m) => m.ContratoIntegracionPage,
      ),
  },

  { path: '', pathMatch: 'full', redirectTo: 'consola' },
];
