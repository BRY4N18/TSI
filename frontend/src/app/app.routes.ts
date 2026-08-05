import { Routes } from '@angular/router';

import { landingRedirectGuard } from './modules/cuentas-clientes/auth/guards/landing-redirect.guard';
import { sessionGuard } from './modules/cuentas-clientes/auth/guards/session.guard';
import { LoginPage } from './modules/cuentas-clientes/auth/pages/login.page';
import { PasswordResetPage } from './modules/cuentas-clientes/auth/pages/password-reset.page';
import { AppShellComponent } from './shared/layout/app-shell.component';

export const routes: Routes = [
  { path: '', pathMatch: 'full', canActivate: [landingRedirectGuard], children: [] },
  {
    path: 'cuentas-clientes/auth/login',
    component: LoginPage,
  },
  {
    path: 'cuentas-clientes/auth/password-reset',
    component: PasswordResetPage,
  },
  {
    path: 'cuentas-clientes/incorporacion-clientes/autorregistro',
    loadComponent: () =>
      import(
        './modules/cuentas-clientes/incorporacion-clientes/pages/autorregistro/autorregistro.page'
      ).then((m) => m.AutorregistroPage),
  },
  {
    path: 'ventas-crm/planes',
    loadComponent: () =>
      import('./modules/ventas-crm/pages/catalogo-planes/catalogo-planes.page').then(
        (m) => m.CatalogoPlanesPage,
      ),
  },
  {
    path: 'ventas-crm/registro',
    loadComponent: () =>
      import('./modules/ventas-crm/pages/registro-publico/registro-publico.page').then(
        (m) => m.RegistroPublicoPage,
      ),
  },
  {
    path: '',
    component: AppShellComponent,
    canActivate: [sessionGuard],
    children: [
      {
        // Destino de los guards de rol cuando la sesión es válida pero el rol no
        // alcanza. Vive dentro del shell para que el usuario conserve su
        // navegación; sin esta ruta el wildcard `**` lo mandaba al portal
        // público y parecía que había perdido la sesión.
        path: 'cuentas-clientes/auth/access-denied',
        loadComponent: () =>
          import('./modules/cuentas-clientes/auth/pages/access-denied.page').then(
            (m) => m.AccessDeniedPage,
          ),
      },
      {
        path: 'cuentas-clientes',
        loadComponent: () =>
          import('./modules/cuentas-clientes/home/home.page').then((m) => m.HomePage),
      },
      {
        path: 'cuentas-clientes/gestion-cuenta',
        loadChildren: () =>
          import('./modules/cuentas-clientes/gestion-cuenta/gestion-cuenta.routes').then(
            (m) => m.GESTION_CUENTA_ROUTES,
          ),
      },
      {
        path: 'cuentas-clientes/incorporacion-clientes',
        loadChildren: () =>
          import(
            './modules/cuentas-clientes/incorporacion-clientes/incorporacion-clientes.routes'
          ).then((m) => m.INCORPORACION_CLIENTES_ROUTES),
      },
      {
        path: 'evidencia-unidad',
        loadChildren: () =>
          import('./modules/evidencia-unidad/evidencia-unidad.routes').then(
            (m) => m.EVIDENCIA_UNIDAD_ROUTES,
          ),
      },
      {
        path: 'seguimiento',
        loadChildren: () =>
          import('./modules/seguimiento/seguimiento.routes').then((m) => m.SEGUIMIENTO_ROUTES),
      },
      {
        path: 'accidentes',
        loadChildren: () =>
          import('./modules/accidentes/accidentes.routes').then((m) => m.ACCIDENTES_ROUTES),
      },
      {
        path: 'emergencias',
        loadChildren: () =>
          import('./modules/emergencias/emergencias.routes').then((m) => m.EMERGENCIAS_ROUTES),
      },
      {
        path: 'despacho',
        loadChildren: () =>
          import('./modules/despacho/despacho.routes').then((m) => m.DESPACHO_ROUTES),
      },
      {
        path: 'soporte-cliente',
        loadChildren: () =>
          import('./modules/soporte-cliente/soporte-cliente.routes').then(
            (m) => m.SOPORTE_CLIENTE_ROUTES,
          ),
      },
      {
        path: 'ventas-crm',
        loadChildren: () =>
          import('./modules/ventas-crm/ventas-crm.routes').then((m) => m.VENTAS_CRM_ROUTES),
      },
      {
        path: 'red-operativa/alta-unidades',
        loadChildren: () =>
          import('./modules/red-operativa/alta-unidades/alta-unidades.routes').then(
            (m) => m.ALTA_UNIDADES_ROUTES,
          ),
      },
      {
        path: 'red-operativa/incorporacion-regional',
        loadChildren: () =>
          import(
            './modules/red-operativa/incorporacion-regional/incorporacion-regional.routes'
          ).then((m) => m.INCORPORACION_REGIONAL_ROUTES),
      },
      {
        path: 'suscripciones',
        loadChildren: () =>
          import('./modules/suscripciones/suscripciones.routes').then(
            (m) => m.SUSCRIPCIONES_ROUTES,
          ),
      },
    ],
  },
  { path: '**', redirectTo: 'ventas-crm/planes' },
];
