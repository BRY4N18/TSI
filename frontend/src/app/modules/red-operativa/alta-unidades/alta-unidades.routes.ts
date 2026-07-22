import { Routes } from '@angular/router';

import { administradorRedOperativaGuard } from './guards/administrador-red-operativa.guard';
import { operadorDisponibilidadGuard } from './guards/operador-disponibilidad.guard';
import { BajaPage } from './pages/baja/baja.page';
import { CatalogoPage } from './pages/catalogo/catalogo.page';
import { DisponibilidadExternaPage } from './pages/disponibilidad-externa/disponibilidad-externa.page';
import { EdicionPage } from './pages/edicion/edicion.page';

export const ALTA_UNIDADES_ROUTES: Routes = [
  {
    path: '',
    children: [
      {
        path: 'catalogo',
        component: CatalogoPage,
        canActivate: [administradorRedOperativaGuard],
      },
      {
        path: 'editar/:idunidademergencia',
        component: EdicionPage,
        canActivate: [administradorRedOperativaGuard],
      },
      {
        path: 'baja/:idunidademergencia',
        component: BajaPage,
        canActivate: [administradorRedOperativaGuard],
      },
      {
        path: 'disponibilidad-externa',
        component: DisponibilidadExternaPage,
        canActivate: [operadorDisponibilidadGuard],
      },
      { path: '', redirectTo: 'catalogo', pathMatch: 'full' },
    ],
  },
];
