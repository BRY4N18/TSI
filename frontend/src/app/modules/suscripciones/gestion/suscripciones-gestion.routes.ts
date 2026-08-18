import { Routes } from '@angular/router';

import {
  gestionCatalogoGuard,
  gestionFinanzasGuard,
} from './guards/suscripciones-gestion.guard';

export const SUSCRIPCIONES_GESTION_ROUTES: Routes = [
  {
    path: 'cobro',
    canActivate: [gestionFinanzasGuard],
    loadComponent: () => import('./pages/pantalla-z.page').then((m) => m.PantallaZPage),
  },
  {
    path: 'movimientos',
    canActivate: [gestionFinanzasGuard],
    loadComponent: () => import('./pages/pantalla-z.page').then((m) => m.PantallaZPage),
  },
  {
    path: 'catalogo',
    canActivate: [gestionCatalogoGuard],
    loadComponent: () => import('./pages/pantalla-z.page').then((m) => m.PantallaZPage),
  },
];
