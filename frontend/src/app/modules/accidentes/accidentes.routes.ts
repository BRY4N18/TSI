import { Routes } from '@angular/router';

import { accidentesLecturaGuard } from './guards/accidentes-lectura.guard';
import { operadorEmergenciasGuard } from './guards/operador-emergencias.guard';

export const ACCIDENTES_ROUTES: Routes = [
  {
    path: 'lista',
    canActivate: [accidentesLecturaGuard],
    loadComponent: () =>
      import('./pages/lista-accidentes/lista-accidentes.page').then((m) => m.ListaAccidentesPage),
  },
  {
    path: 'registro',
    canActivate: [operadorEmergenciasGuard],
    loadComponent: () =>
      import('./pages/registro-accidente/registro-accidente.page').then(
        (m) => m.RegistroAccidentePage,
      ),
  },
  {
    path: ':idaccidente',
    canActivate: [accidentesLecturaGuard],
    loadComponent: () =>
      import('./pages/detalle-accidente/detalle-accidente.page').then(
        (m) => m.DetalleAccidentePage,
      ),
  },
  { path: '', pathMatch: 'full', redirectTo: 'lista' },
];
