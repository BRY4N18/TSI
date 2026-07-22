import { Routes } from '@angular/router';

import { administradorODirectorTecnologicoGuard } from './guards/director-tecnologico.guard';
import { directorTecnologicoGuard } from './guards/director-tecnologico.guard';
import { ReevaluacionPage } from './pages/reevaluacion/reevaluacion.page';
import { ValidacionPage } from './pages/validacion/validacion.page';

export const INCORPORACION_REGIONAL_ROUTES: Routes = [
  {
    path: '',
    children: [
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
      { path: '', redirectTo: 'validacion', pathMatch: 'full' },
    ],
  },
];
