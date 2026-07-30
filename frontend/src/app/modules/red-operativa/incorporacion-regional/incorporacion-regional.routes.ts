import { Routes } from '@angular/router';

import { administradorODirectorTecnologicoGuard } from './guards/director-tecnologico.guard';
import { directorTecnologicoGuard } from './guards/director-tecnologico.guard';
import { CatalogoRegionesPage } from './pages/catalogo/catalogo-regiones.page';
import { ReevaluacionPage } from './pages/reevaluacion/reevaluacion.page';
import { ValidacionPage } from './pages/validacion/validacion.page';

export const INCORPORACION_REGIONAL_ROUTES: Routes = [
  {
    path: '',
    children: [
      {
        path: 'catalogo',
        component: CatalogoRegionesPage,
        canActivate: [administradorODirectorTecnologicoGuard],
      },
      {
        path: 'validacion',
        component: ValidacionPage,
        canActivate: [administradorODirectorTecnologicoGuard],
      },
      {
        path: 'reevaluacion/:idregionoperativa',
        component: ReevaluacionPage,
        canActivate: [directorTecnologicoGuard],
      },
      { path: '', redirectTo: 'catalogo', pathMatch: 'full' },
    ],
  },
];
