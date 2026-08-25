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
        path: 'planes/:idplan',
        canActivate: [directorEstrategiaBillingGuard],
        loadComponent: () =>
          import('./pages/plan-detalle/plan-detalle.page').then((m) => m.PlanDetallePage),
      },
      {
        path: 'aprobaciones-downgrade',
        canActivate: [adminBillingGuard],
        loadComponent: () =>
          import('./pages/aprobaciones-downgrade/aprobaciones-downgrade.page').then(
            (m) => m.AprobacionesDowngradePage,
          ),
      },
      // `children: []` no es decorativo: una ruta solo con `canActivate` no tiene
      // nada que renderizar y Angular la rechaza entera con NG04014, tumbando la
      // configuracion de TODO el modulo (no solo esta ruta). El guard redirige
      // devolviendo un UrlTree, asi que el array vacio es suficiente.
      { path: '', pathMatch: 'full', canActivate: [suscripcionesHomeRedirect], children: [] },
    ],
  },
];
