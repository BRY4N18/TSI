import { Routes } from '@angular/router';

import {
  oe4CalidadGuard,
  oe4CoberturaGuard,
  oe4ConcentracionGuard,
  oe4ImpactoGuard,
} from './guards/oe4.guard';

export const OE4_ROUTES: Routes = [
  {
    path: 'calidad',
    canActivate: [oe4CalidadGuard],
    loadComponent: () => import('./pages/pantalla-z.page').then((m) => m.PantallaZPage),
  },
  {
    path: 'concentracion',
    canActivate: [oe4ConcentracionGuard],
    loadComponent: () => import('./pages/pantalla-z.page').then((m) => m.PantallaZPage),
  },
  {
    path: 'impacto',
    canActivate: [oe4ImpactoGuard],
    loadComponent: () => import('./pages/pantalla-z.page').then((m) => m.PantallaZPage),
  },
  {
    path: 'cobertura',
    canActivate: [oe4CoberturaGuard],
    loadComponent: () => import('./pages/pantalla-z.page').then((m) => m.PantallaZPage),
  },
];
