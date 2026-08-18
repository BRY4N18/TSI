import { Routes } from '@angular/router';

import { partnersGestionGuard } from './guards/partners-gestion.guard';

export const PARTNERS_GESTION_ROUTES: Routes = [
  {
    path: 'consumo',
    canActivate: [partnersGestionGuard],
    loadComponent: () => import('./pages/pantalla-z.page').then((m) => m.PantallaZPage),
  },
  {
    path: 'incorporacion',
    canActivate: [partnersGestionGuard],
    loadComponent: () => import('./pages/pantalla-z.page').then((m) => m.PantallaZPage),
  },
  {
    path: 'entrega',
    canActivate: [partnersGestionGuard],
    loadComponent: () => import('./pages/pantalla-z.page').then((m) => m.PantallaZPage),
  },
];
