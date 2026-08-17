import { Routes } from '@angular/router';

import { emergenciasGestionGuard } from './guards/emergencias-gestion.guard';

export const EMERGENCIAS_GESTION_ROUTES: Routes = [
  {
    path: 'calidad',
    canActivate: [emergenciasGestionGuard],
    loadComponent: () =>
      import('./pages/pantalla-z.page').then((m) => m.PantallaZPage),
  },
  {
    path: 'despacho',
    canActivate: [emergenciasGestionGuard],
    loadComponent: () =>
      import('./pages/pantalla-z.page').then((m) => m.PantallaZPage),
  },
  {
    path: 'cierre',
    canActivate: [emergenciasGestionGuard],
    loadComponent: () =>
      import('./pages/pantalla-z.page').then((m) => m.PantallaZPage),
  },
];
