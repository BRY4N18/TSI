import { Routes } from '@angular/router';

import { adminBillingGuard } from './guards/admin-billing.guard';
import { directorEstrategiaBillingGuard } from './guards/director-estrategia-billing.guard';
import { proveedorBillingGuard } from './guards/proveedor-billing.guard';
import { suscripcionesHomeRedirect } from './guards/suscripciones-home.redirect';

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
        path: 'planes/nuevo',
        canActivate: [directorEstrategiaBillingGuard],
        loadComponent: () =>
          import('./pages/plan-form/plan-form.page').then((m) => m.PlanFormPage),
      },
      {
        path: 'planes/:idplan/editar',
        canActivate: [directorEstrategiaBillingGuard],
        loadComponent: () =>
          import('./pages/plan-form/plan-form.page').then((m) => m.PlanFormPage),
      },
      {
        path: 'aprobaciones-downgrade',
        canActivate: [adminBillingGuard],
        loadComponent: () =>
          import('./pages/aprobaciones-downgrade/aprobaciones-downgrade.page').then(
            (m) => m.AprobacionesDowngradePage,
          ),
      },
      { path: '', pathMatch: 'full', canActivate: [suscripcionesHomeRedirect] },
    ],
  },
];
