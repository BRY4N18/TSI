import { Routes } from '@angular/router';

import {
  oe3CalidadGuard,
  oe3CapacidadGuard,
  oe3LatenciaGuard,
  oe3RespaldoGuard,
} from './guards/oe3.guard';

export const OE3_ROUTES: Routes = [
  {
    path: 'latencia',
    canActivate: [oe3LatenciaGuard],
    loadComponent: () => import('./pages/pantalla-z.page').then((m) => m.PantallaZPage),
  },
  {
    path: 'calidad',
    canActivate: [oe3CalidadGuard],
    loadComponent: () => import('./pages/pantalla-z.page').then((m) => m.PantallaZPage),
  },
  {
    path: 'capacidad',
    canActivate: [oe3CapacidadGuard],
    loadComponent: () => import('./pages/pantalla-z.page').then((m) => m.PantallaZPage),
  },
  {
    path: 'respaldo',
    canActivate: [oe3RespaldoGuard],
    loadComponent: () => import('./pages/pantalla-z.page').then((m) => m.PantallaZPage),
  },
];
