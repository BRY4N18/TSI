import { Routes } from '@angular/router';

import {
  oe5IngresosGuard,
  oe5PlanesGuard,
  oe5RiesgoGuard,
  oe5ServicioGuard,
} from './guards/oe5.guard';

export const OE5_ROUTES: Routes = [
  {
    path: 'servicio',
    canActivate: [oe5ServicioGuard],
    loadComponent: () => import('./pages/pantalla-z.page').then((m) => m.PantallaZPage),
  },
  {
    path: 'ingresos',
    canActivate: [oe5IngresosGuard],
    loadComponent: () => import('./pages/pantalla-z.page').then((m) => m.PantallaZPage),
  },
  {
    path: 'planes',
    canActivate: [oe5PlanesGuard],
    loadComponent: () => import('./pages/pantalla-z.page').then((m) => m.PantallaZPage),
  },
  {
    path: 'riesgo',
    canActivate: [oe5RiesgoGuard],
    loadComponent: () => import('./pages/pantalla-z.page').then((m) => m.PantallaZPage),
  },
];
