import { Routes } from '@angular/router';

import {
  gestionCrecimientoGuard,
  gestionValidacionGuard,
} from './guards/red-operativa-gestion.guard';

export const RED_OPERATIVA_GESTION_ROUTES: Routes = [
  {
    path: 'flota',
    canActivate: [gestionCrecimientoGuard],
    loadComponent: () =>
      import('./pages/pantalla-z.page').then((m) => m.PantallaZPage),
  },
  {
    path: 'mercados',
    canActivate: [gestionCrecimientoGuard],
    loadComponent: () =>
      import('./pages/pantalla-z.page').then((m) => m.PantallaZPage),
  },
  {
    path: 'validacion',
    canActivate: [gestionValidacionGuard],
    loadComponent: () =>
      import('./pages/pantalla-z.page').then((m) => m.PantallaZPage),
  },
];
