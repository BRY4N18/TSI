import { Injectable, inject } from '@angular/core';
import { Observable, switchMap } from 'rxjs';

import {
  CompletarEtapaData,
  DatosEtapaPerfil,
  DatosEtapaPreferencias,
  EtapaOnboarding,
  OnboardingProgresoData,
} from '../models/incorporacion-cliente.contract';
import { IncorporacionClienteApiService } from './incorporacion-cliente-api.service';

@Injectable({ providedIn: 'root' })
export class OnboardingFacadeService {
  private readonly api = inject(IncorporacionClienteApiService);

  loadProgreso(idcliente: number): Observable<OnboardingProgresoData> {
    return this.api.getOnboardingProgreso(idcliente).pipe(switchMap((res) => [res.data]));
  }

  completarCambioPassword(idcliente: number): Observable<CompletarEtapaData> {
    return this.api
      .completarEtapa(idcliente, { etapa: 'cambio_password' })
      .pipe(switchMap((res) => [res.data]));
  }

  completarPerfil(
    idcliente: number,
    datos: DatosEtapaPerfil,
  ): Observable<CompletarEtapaData> {
    return this.api
      .completarEtapa(idcliente, { etapa: 'perfil_corporativo', datos_etapa: datos })
      .pipe(switchMap((res) => [res.data]));
  }

  /** Obtiene URL firmada y completa perfil corporativo con logo_url (cliente). */
  uploadLogoAndCompletarPerfil(
    idcliente: number,
    datos: DatosEtapaPerfil,
    file: File,
  ): Observable<CompletarEtapaData> {
    return this.api.createLogoUploadUrl(idcliente, file.type, file.name).pipe(
      switchMap((upload) =>
        this.completarPerfil(idcliente, {
          ...datos,
          logo_url: upload.data.logo_url,
        }),
      ),
    );
  }

  completarPreferencias(
    idcliente: number,
    datos: DatosEtapaPreferencias,
  ): Observable<CompletarEtapaData> {
    return this.api
      .completarEtapa(idcliente, { etapa: 'preferencias', datos_etapa: datos })
      .pipe(switchMap((res) => [res.data]));
  }

  etapaLabel(etapa: EtapaOnboarding | null): string {
    switch (etapa) {
      case 'cambio_password':
        return 'Cambio de contraseña';
      case 'perfil_corporativo':
        return 'Perfil corporativo';
      case 'preferencias':
        return 'Preferencias';
      default:
        return 'Completado';
    }
  }
}
