import { ChangeDetectorRef, Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';

import { NotificationService } from '../../../../../shared/notifications/notification.service';
import { TablerIconComponent } from '../../../../../shared/ui/icon/tabler-icon.component';
import {
  DatosEtapaPerfil,
  DatosEtapaPreferencias,
  EtapaOnboarding,
  OnboardingProgresoData,
} from '../../models/incorporacion-cliente.contract';
import { CuentaClienteApiService } from '../../../gestion-cuenta/services/cuenta-cliente-api.service';
import {
  PreferenciasOperativas,
  PreferenciasOperativasFormComponent,
  PreferenciasSerializadas,
  deserializarPreferencias,
} from '../../../shared/preferencias-operativas-form.component';
import { IncorporacionClienteApiService } from '../../services/incorporacion-cliente-api.service';
import { OnboardingFacadeService } from '../../services/onboarding-facade.service';

@Component({
  selector: 'app-onboarding-wizard-page',
  standalone: true,
  imports: [CommonModule, FormsModule, TablerIconComponent, PreferenciasOperativasFormComponent],
  templateUrl: './onboarding-wizard.page.html',
})
export class OnboardingWizardPage implements OnInit {
  readonly facade = inject(OnboardingFacadeService);
  private readonly api = inject(IncorporacionClienteApiService);
  private readonly cuentaApi = inject(CuentaClienteApiService);
  private readonly notifications = inject(NotificationService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  // El shell de la aplicación es OnPush: sin marcar la vista, nada de lo que
  // llega por HTTP se repinta. Ver §9 del design-system.
  private readonly cdr = inject(ChangeDetectorRef);

  readonly idcliente = Number(this.route.snapshot.paramMap.get('idcliente'));
  readonly etapas: EtapaOnboarding[] = ['cambio_password', 'perfil_corporativo', 'preferencias'];

  progreso: OnboardingProgresoData | null = null;
  perfil: DatosEtapaPerfil = { razon_social: '', nombre: '' };
  preferencias: DatosEtapaPreferencias = { canales_notificacion: 'email', telefono_sms: '' };
  /** Las cuatro dimensiones del SRS §3.2.2, no solo el canal. */
  prefsForm: PreferenciasOperativas = deserializarPreferencias(null);
  logoFile: File | null = null;
  reenviando = false;

  ngOnInit(): void {
    this.cargarProgreso();
    this.precargarPerfil();
  }

  /**
   * El perfil llega con lo que la cuenta ya declaró al darse de alta. Antes el
   * formulario salía vacío y obligaba a reescribir la razón social y el nombre
   * comercial, contra el principio del SRS de no volver a digitar lo capturado.
   */
  private precargarPerfil(): void {
    this.cuentaApi.getPerfil(this.idcliente).subscribe({
      next: (res) => {
        this.perfil = {
          razon_social: res.data.razon_social ?? '',
          nombre: res.data.nombre ?? '',
        };
        this.cdr.markForCheck();
      },
      // Sin perfil precargado el formulario sigue siendo usable: se escribe a mano.
      error: () => undefined,
    });
  }

  cargarProgreso(): void {
    this.facade.loadProgreso(this.idcliente).subscribe({
      next: (data) => {
        this.cdr.markForCheck();
        this.progreso = data;
      },
      error: (err) => {
        this.cdr.markForCheck();
        this.notifications.toast(
          err?.error?.detail ?? 'No se pudo cargar el progreso',
          'critical',
        );
      },
    });
  }

  reenviarInvitacion(): void {
    this.reenviando = true;
    this.api.reenviarInvitacion(this.idcliente).subscribe({
      next: () => {
        this.cdr.markForCheck();
        this.reenviando = false;
        this.notifications.toast('Invitación reenviada.', 'info');
      },
      error: (err) => {
        this.cdr.markForCheck();
        this.reenviando = false;
        this.notifications.toast(
          err?.error?.detail ?? 'No se pudo reenviar la invitación',
          'critical',
        );
      },
    });
  }

  onLogoSeleccionado(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.logoFile = input.files?.[0] ?? null;
  }

  completarCambioPassword(): void {
    this.facade.completarCambioPassword(this.idcliente).subscribe({
      next: (data) => {
        this.cdr.markForCheck();
        this.progreso = data.progreso;
        this.notifications.toast('Etapa de contraseña completada.', 'success');
      },
      error: (err) => {
        this.cdr.markForCheck();
        this.notifications.toast(
          err?.error?.detail ?? 'No se pudo completar la etapa',
          'critical',
        );
      },
    });
  }

  completarPerfil(): void {
    const request$ = this.logoFile
      ? this.facade.uploadLogoAndCompletarPerfil(this.idcliente, this.perfil, this.logoFile)
      : this.facade.completarPerfil(this.idcliente, this.perfil);

    request$.subscribe({
      next: (data) => {
        this.cdr.markForCheck();
        this.progreso = data.progreso;
        this.logoFile = null;
        this.notifications.toast('Perfil corporativo guardado.', 'success');
      },
      error: (err) => {
        this.cdr.markForCheck();
        this.notifications.toast(
          err?.error?.detail ?? 'No se pudo completar el perfil',
          'critical',
        );
      },
    });
  }

  completarPreferencias(serializadas: PreferenciasSerializadas): void {
    this.facade.completarPreferencias(this.idcliente, serializadas).subscribe({
      next: (data) => {
        this.cdr.markForCheck();
        this.progreso = data.progreso;
        this.notifications.toast('Onboarding finalizado.', 'success');
      },
      error: (err) => {
        this.cdr.markForCheck();
        this.notifications.toast(
          err?.error?.detail ?? 'No se pudo completar preferencias',
          'critical',
        );
      },
    });
  }

  irAGestion(): void {
    this.router.navigate(['/cuentas-clientes/gestion-cuenta', this.idcliente, 'perfil']);
  }
}
