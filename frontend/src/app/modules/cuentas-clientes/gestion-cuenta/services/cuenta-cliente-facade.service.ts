import { Injectable, inject } from '@angular/core';
import { Observable, switchMap } from 'rxjs';

import { PerfilUpdatedData } from '../models/cuenta-cliente.contract';
import { CuentaClienteApiService } from './cuenta-cliente-api.service';

@Injectable({ providedIn: 'root' })
export class CuentaClienteFacadeService {
  private readonly api = inject(CuentaClienteApiService);

  uploadLogoAndUpdatePerfil(
    idcliente: number,
    file: File,
  ): Observable<PerfilUpdatedData> {
    return this.api
      .createLogoUploadUrl(idcliente, file.type, file.name)
      .pipe(
        switchMap((response) =>
          this.api
            .patchPerfil(idcliente, { logo_url: response.data.logo_url })
            .pipe(switchMap((patch) => [patch.data])),
        ),
      );
  }
}
