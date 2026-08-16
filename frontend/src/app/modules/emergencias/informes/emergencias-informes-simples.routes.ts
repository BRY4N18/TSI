/**
 * Rutas de los informes tácticos **simples** de Emergencias.
 *
 * Cuelgan de `/emergencias/informes-simples` y no de `/emergencias/informes`
 * porque ese prefijo ya lo ocupan los **workpanels de los informes agregados**,
 * que son otro módulo con otros roles. Fusionarlos mezclaría el acceso a dos
 * cosas que el catálogo separa.
 *
 * ⚠️ `casos` va **antes** de la ruta genérica y con el guard permisivo: es el
 * único que un Cliente puede ver. Con la genérica primero, Angular aplicaría el
 * guard interno y lo dejaría fuera de lo único a lo que sí accede. Como su
 * `path` es literal, el identificador viaja por `data`.
 */

import { Routes } from '@angular/router';

import { INFORME_CASOS } from './definiciones/informes-emergencias.definiciones';
import {
  informesCasosGuard,
  informesEmergenciasInternoGuard,
} from './guards/informes-emergencias-simples.guard';

export const EMERGENCIAS_INFORMES_SIMPLES_ROUTES: Routes = [
  {
    path: '',
    canActivate: [informesCasosGuard],
    loadComponent: () =>
      import('./pages/indice/indice-informes.page').then(
        (m) => m.IndiceInformesEmergenciasPage,
      ),
  },
  {
    path: INFORME_CASOS,
    canActivate: [informesCasosGuard],
    loadComponent: () =>
      import('./pages/informe/informe.page').then((m) => m.InformeEmergenciasPage),
    data: { informe: INFORME_CASOS },
  },
  {
    path: ':informe',
    canActivate: [informesEmergenciasInternoGuard],
    loadComponent: () =>
      import('./pages/informe/informe.page').then((m) => m.InformeEmergenciasPage),
  },
];
