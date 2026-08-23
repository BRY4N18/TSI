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
        path: 'cuentas-clientes/gestion',
        loadChildren: () =>
          import('./modules/cuentas-clientes/gestion/cuentas-gestion.routes').then(
            (m) => m.CUENTAS_GESTION_ROUTES,
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
        path: 'cuentas-clientes/informes',
        loadChildren: () =>
          import(
            './modules/cuentas-clientes/informes/cuentas-clientes-informes.routes'
          ).then((m) => m.CUENTAS_CLIENTES_INFORMES_ROUTES),
      },
      {
        path: 'soporte-cliente/informes',
        loadChildren: () =>
          import(
            './modules/soporte-cliente/informes/soporte-cliente-informes.routes'
          ).then((m) => m.SOPORTE_CLIENTE_INFORMES_ROUTES),
      },
      {
        path: 'soporte-cliente/gestion',
        loadChildren: () =>
          import('./modules/soporte-cliente/gestion/soporte-cliente-gestion.routes').then(
            (m) => m.SOPORTE_CLIENTE_GESTION_ROUTES,
          ),
      },
      {
        path: 'ventas-crm/informes',
        loadChildren: () =>
          import('./modules/ventas-crm/informes/ventas-crm-informes.routes').then(
            (m) => m.VENTAS_CRM_INFORMES_ROUTES,
          ),
      },
      {
        path: 'ventas-crm/gestion',
        loadChildren: () =>
          import('./modules/ventas-crm/gestion/ventas-crm-gestion.routes').then(
            (m) => m.VENTAS_CRM_GESTION_ROUTES,
          ),
      },
      {
        path: 'suscripciones/informes',
        loadChildren: () =>
          import('./modules/suscripciones/informes/suscripciones-informes.routes').then(
            (m) => m.SUSCRIPCIONES_INFORMES_ROUTES,
          ),
      },
      {
        path: 'suscripciones/gestion',
        loadChildren: () =>
          import('./modules/suscripciones/gestion/suscripciones-gestion.routes').then(
            (m) => m.SUSCRIPCIONES_GESTION_ROUTES,
          ),
      },
      {
        path: 'red-operativa/informes',
        loadChildren: () =>
          import('./modules/red-operativa/informes/red-operativa-informes.routes').then(
            (m) => m.RED_OPERATIVA_INFORMES_ROUTES,
          ),
      },
      {
        path: 'red-operativa/gestion',
        loadChildren: () =>
          import('./modules/red-operativa/gestion/red-operativa-gestion.routes').then(
            (m) => m.RED_OPERATIVA_GESTION_ROUTES,
          ),
      },
      {
        path: 'emergencias/informes-simples',
        loadChildren: () =>
          import(
            './modules/emergencias/informes/emergencias-informes-simples.routes'
          ).then((m) => m.EMERGENCIAS_INFORMES_SIMPLES_ROUTES),
      },
      {
        path: 'emergencias/gestion',
        loadChildren: () =>
          import('./modules/emergencias/gestion/emergencias-gestion.routes').then(
            (m) => m.EMERGENCIAS_GESTION_ROUTES,
          ),
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
      {
        path: 'estrategico/oe1',
        loadChildren: () =>
          import('./modules/estrategico/oe1/oe1.routes').then((m) => m.OE1_ROUTES),
      },
      {
        path: 'estrategico/oe5',
        loadChildren: () =>
          import('./modules/estrategico/oe5/oe5.routes').then((m) => m.OE5_ROUTES),
      },
      {
        path: 'estrategico/oe6',
        loadChildren: () =>
          import('./modules/estrategico/oe6/oe6.routes').then((m) => m.OE6_ROUTES),
      },
      {
        path: 'estrategico/oe3',
        loadChildren: () =>
          import('./modules/estrategico/oe3/oe3.routes').then((m) => m.OE3_ROUTES),
      },
      {
        path: 'estrategico/oe4',
        loadChildren: () =>
          import('./modules/estrategico/oe4/oe4.routes').then((m) => m.OE4_ROUTES),
      },
      {
        path: 'estrategico/oe2',
        loadChildren: () =>
          import('./modules/estrategico/oe2/oe2.routes').then((m) => m.OE2_ROUTES),
      },
      {
        path: 'partners/gestion',
        loadChildren: () =>
          import('./modules/partners/gestion/partners-gestion.routes').then(
            (m) => m.PARTNERS_GESTION_ROUTES,
          ),
      },
      {
        path: 'partners/informes',
        loadChildren: () =>
          import('./modules/partners/informes/partners-informes.routes').then(
            (m) => m.PARTNERS_INFORMES_ROUTES,
          ),
      },
      {
        path: 'partners',
        loadChildren: () =>
          import('./modules/partners/partners.routes').then((m) => m.PARTNERS_ROUTES),
      },
    ],
  },
  { path: '**', redirectTo: 'ventas-crm/planes' },
];
