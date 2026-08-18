import { Routes } from '@angular/router';

import {
  gestionAccesoGuard,
  gestionCicloGuard,
  gestionIncorporacionGuard,
} from './guards/cuentas-gestion.guard';

export const CUENTAS_GESTION_ROUTES: Routes = [
  {
    path: 'ciclo',
    canActivate: [gestionCicloGuard],
    loadComponent: () => import('./pages/pantalla-z.page').then((m) => m.PantallaZPage),
  },
  {
    path: 'incorporacion',
    canActivate: [gestionIncorporacionGuard],
    loadComponent: () => import('./pages/pantalla-z.page').then((m) => m.PantallaZPage),
  },
  {
    path: 'acceso',
    canActivate: [gestionAccesoGuard],
    loadComponent: () => import('./pages/pantalla-z.page').then((m) => m.PantallaZPage),
  },
];
