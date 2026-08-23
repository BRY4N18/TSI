import { Routes } from '@angular/router';

import {
  oe1CaptacionGuard,
  oe1CarteraGuard,
  oe1CicloGuard,
  oe1IngresoGuard,
} from './guards/oe1.guard';

export const OE1_ROUTES: Routes = [
  {
    path: 'ingreso',
    canActivate: [oe1IngresoGuard],
    loadComponent: () => import('./pages/pantalla-z.page').then((m) => m.PantallaZPage),
  },
  {
    path: 'cartera',
    canActivate: [oe1CarteraGuard],
    loadComponent: () => import('./pages/pantalla-z.page').then((m) => m.PantallaZPage),
  },
  {
    path: 'captacion',
    canActivate: [oe1CaptacionGuard],
    loadComponent: () => import('./pages/pantalla-z.page').then((m) => m.PantallaZPage),
  },
  {
    path: 'ciclo',
    canActivate: [oe1CicloGuard],
    loadComponent: () => import('./pages/pantalla-z.page').then((m) => m.PantallaZPage),
  },
];
