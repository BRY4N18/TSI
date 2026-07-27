import { Routes } from '@angular/router';

import { adminBillingGuard } from './guards/admin-billing.guard';
import { proveedorBillingGuard } from './guards/proveedor-billing.guard';

export const SUSCRIPCIONES_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./pages/billing-shell/billing-shell.page').then((m) => m.BillingShellPage),
    children: [
      {
        path: 'mi-suscripcion',
        canActivate: [proveedorBillingGuard],
        loadComponent: () =>
          import('./pages/mi-suscripcion/mi-suscripcion.page').then((m) => m.MiSuscripcionPage),
      },
      {
        path: 'metodos-pago',
        canActivate: [proveedorBillingGuard],
        loadComponent: () =>
          import('./pages/metodos-pago/metodos-pago.page').then((m) => m.MetodosPagoPage),
      },
      {
        path: 'historial-facturas',
        canActivate: [proveedorBillingGuard],
        loadComponent: () =>
          import('./pages/historial-facturas/historial-facturas.page').then(
            (m) => m.HistorialFacturasPage,
          ),
      },
      {
        path: 'cambio-plan',
        canActivate: [proveedorBillingGuard],
        loadComponent: () =>
          import('./pages/cambio-plan/cambio-plan.page').then((m) => m.CambioPlanPage),
      },
      {
        path: 'catalogo-planes',
        loadComponent: () =>
          import('./pages/catalogo-planes/catalogo-planes.page').then((m) => m.CatalogoPlanesPage),
      },
      {
        path: 'aprobaciones-downgrade',
        canActivate: [adminBillingGuard],
        loadComponent: () =>
          import('./pages/aprobaciones-downgrade/aprobaciones-downgrade.page').then(
            (m) => m.AprobacionesDowngradePage,
          ),
      },
      { path: '', pathMatch: 'full', redirectTo: 'mi-suscripcion' },
    ],
  },
];
