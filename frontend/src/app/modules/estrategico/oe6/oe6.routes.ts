import { Routes } from '@angular/router';

import { oe6Guard } from './guards/oe6.guard';

export const OE6_ROUTES: Routes = [
  {
    path: 'llegada',
    canActivate: [oe6Guard],
    loadComponent: () => import('./pages/pantalla-z.page').then((m) => m.PantallaZPage),
  },
  {
    path: 'diagnostico',
    canActivate: [oe6Guard],
    loadComponent: () => import('./pages/pantalla-z.page').then((m) => m.PantallaZPage),
  },
  {
    path: 'ejecucion',
    canActivate: [oe6Guard],
    loadComponent: () => import('./pages/pantalla-z.page').then((m) => m.PantallaZPage),
  },
  {
    path: 'personas',
    canActivate: [oe6Guard],
    loadComponent: () => import('./pages/pantalla-z.page').then((m) => m.PantallaZPage),
  },
];
