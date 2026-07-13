import { Routes } from '@angular/router';

import { sessionGuard } from './modules/cuentas-clientes/auth/guards/session.guard';
import { LoginPage } from './modules/cuentas-clientes/auth/pages/login.page';
import { PasswordResetPage } from './modules/cuentas-clientes/auth/pages/password-reset.page';
import { AppShellComponent } from './shared/layout/app-shell.component';

export const routes: Routes = [
  { path: '', redirectTo: 'cuentas-clientes/auth/login', pathMatch: 'full' },
  {
    path: 'cuentas-clientes/auth/login',
    component: LoginPage,
  },
  {
    path: 'cuentas-clientes/auth/password-reset',
    component: PasswordResetPage,
  },
  {
    path: '',
    component: AppShellComponent,
    canActivate: [sessionGuard],
    children: [
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
        path: 'despacho',
        loadChildren: () =>
          import('./modules/despacho/despacho.routes').then((m) => m.DESPACHO_ROUTES),
      },
    ],
  },
  { path: '**', redirectTo: 'cuentas-clientes/auth/login' },
];
