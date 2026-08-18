import { Routes } from '@angular/router';

import { soporteGestionGuard } from './guards/soporte-gestion.guard';

export const SOPORTE_CLIENTE_GESTION_ROUTES: Routes = [
  {
    path: 'cumplimiento',
    canActivate: [soporteGestionGuard],
    loadComponent: () =>
      import('./pages/pantalla-z.page').then((m) => m.PantallaZPage),
  },
  {
    path: 'cola',
    canActivate: [soporteGestionGuard],
    loadComponent: () =>
      import('./pages/pantalla-z.page').then((m) => m.PantallaZPage),
  },
  {
    path: 'tendencias',
    canActivate: [soporteGestionGuard],
    loadComponent: () =>
      import('./pages/pantalla-z.page').then((m) => m.PantallaZPage),
  },
];
