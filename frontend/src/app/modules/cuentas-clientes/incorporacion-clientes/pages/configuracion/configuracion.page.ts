import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { map } from 'rxjs/operators';

import { IncorporacionClienteApiService } from '../../services/incorporacion-cliente-api.service';
import { OnboardingFacadeService } from '../../services/onboarding-facade.service';
import { ConfiguracionCuentaData } from '../../models/incorporacion-cliente.contract';

@Component({
  selector: 'app-configuracion-page',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <h1>Configuración de cuenta</h1>
    <p>Cuenta #{{ idcliente }}</p>
    <form (ngSubmit)="guardar()">
      <label>Plan de suscripción <input [(ngModel)]="plan" name="plan" required /></label>
      <label>Logo <input type="file" accept="image/*" (change)="onLogoSelected($event)" /></label>
      <button type="submit" [disabled]="enviando">Configurar cuenta</button>
    </form>
    <button type="button" class="secondary" (click)="reenviarInvitacion()" [disabled]="reenviando">
      Reenviar invitación
    </button>
    @if (mensaje) {
      <p class="ok">{{ mensaje }}</p>
    }
    @if (error) {
      <p class="err">{{ error }}</p>
    }
  `,
  styles: [
    `
      form {
        display: grid;
        gap: 0.75rem;
        max-width: 28rem;
        margin-bottom: 1rem;
      }
      .secondary {
        margin-top: 0.5rem;
      }
      .ok {
        color: #3b6d11;
      }
      .err {
        color: #b42318;
      }
    `,
  ],
})
export class ConfiguracionPage {
  private readonly api = inject(IncorporacionClienteApiService);
  private readonly facade = inject(OnboardingFacadeService);
  private readonly route = inject(ActivatedRoute);

  readonly idcliente = Number(this.route.snapshot.paramMap.get('idcliente'));
  plan = '';
  logoFile: File | null = null;
  enviando = false;
  reenviando = false;
  mensaje = '';
  error = '';

  onLogoSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.logoFile = input.files?.[0] ?? null;
  }

  guardar(): void {
    this.enviando = true;
    this.error = '';
    this.mensaje = '';

    const save$ = this.logoFile
      ? this.facade.uploadLogoAndConfigurar(this.idcliente, this.plan, this.logoFile)
      : this.api
          .configurarCuenta(this.idcliente, { plan_suscripcion: this.plan })
          .pipe(map((res) => res.data));

    save$.subscribe({
      next: (data: ConfiguracionCuentaData) => {
        this.mensaje = `Cuenta configurada. Onboarding: ${data.estado_onboarding}`;
        this.enviando = false;
      },
      error: (err) => {
        this.error = err?.error?.detail ?? 'No se pudo configurar la cuenta';
        this.enviando = false;
      },
    });
  }

  reenviarInvitacion(): void {
    this.reenviando = true;
    this.error = '';
    this.api.reenviarInvitacion(this.idcliente).subscribe({
      next: (res) => {
        this.mensaje = res.data.message;
        this.reenviando = false;
      },
      error: (err) => {
        this.error = err?.error?.detail ?? 'No se pudo reenviar la invitación';
        this.reenviando = false;
      },
    });
  }
}
