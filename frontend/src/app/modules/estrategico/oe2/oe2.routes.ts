import { Routes } from '@angular/router';

import { oe2DineroGuard, oe2UsoEcosistemaGuard } from './guards/oe2.guard';

export const OE2_ROUTES: Routes = [
  {
    path: 'uso',
    canActivate: [oe2UsoEcosistemaGuard],
    loadComponent: () => import('./pages/pantalla-z.page').then((m) => m.PantallaZPage),
  },
  {
    path: 'dinero',
    canActivate: [oe2DineroGuard],
    loadComponent: () => import('./pages/pantalla-z.page').then((m) => m.PantallaZPage),
  },
  {
    path: 'ecosistema',
    canActivate: [oe2UsoEcosistemaGuard],
    loadComponent: () => import('./pages/pantalla-z.page').then((m) => m.PantallaZPage),
  },
];
