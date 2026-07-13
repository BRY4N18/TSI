import { Injectable, inject } from '@angular/core';
import { Observable, switchMap } from 'rxjs';

import {
  CompletarEtapaData,
  ConfiguracionCuentaData,
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
    return this.api.getOnboardingProgreso(idcliente).pipe(
      switchMap((res) => [res.data]),
    );
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

  completarPreferencias(
    idcliente: number,
    datos: DatosEtapaPreferencias,
  ): Observable<CompletarEtapaData> {
    return this.api
      .completarEtapa(idcliente, { etapa: 'preferencias', datos_etapa: datos })
      .pipe(switchMap((res) => [res.data]));
  }

  uploadLogoAndConfigurar(
    idcliente: number,
    plan: string,
    file: File,
  ): Observable<ConfiguracionCuentaData> {
    return this.api.createLogoUploadUrl(idcliente, file.type, file.name).pipe(
      switchMap((upload) =>
        this.api
          .configurarCuenta(idcliente, {
            plan_suscripcion: plan,
            logo_url: upload.data.logo_url,
          })
          .pipe(switchMap((res) => [res.data])),
      ),
    );
  }

  etapaLabel(etapa: EtapaOnboarding | null): string {
    const labels: Record<EtapaOnboarding, string> = {
      cambio_password: 'Cambio de contraseña',
      perfil_corporativo: 'Perfil corporativo',
      preferencias: 'Preferencias operativas',
    };
    return etapa ? labels[etapa] : 'Completado';
  }
}
