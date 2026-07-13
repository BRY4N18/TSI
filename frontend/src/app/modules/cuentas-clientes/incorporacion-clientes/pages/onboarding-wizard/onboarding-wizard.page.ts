import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';

import {
  DatosEtapaPerfil,
  DatosEtapaPreferencias,
  EtapaOnboarding,
  OnboardingProgresoData,
} from '../../models/incorporacion-cliente.contract';
import { OnboardingFacadeService } from '../../services/onboarding-facade.service';

@Component({
  selector: 'app-onboarding-wizard-page',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <h1>Onboarding digital</h1>
    <p>Cuenta #{{ idcliente }}</p>
    @if (progreso) {
      <p>Estado: {{ progreso.estado_onboarding }} — Etapa: {{ facade.etapaLabel(progreso.etapa_actual) }}</p>
      <ul>
        @for (e of etapas; track e) {
          <li [class.done]="progreso.etapas_completadas.includes(e)">{{ facade.etapaLabel(e) }}</li>
        }
      </ul>

      @switch (progreso.etapa_actual) {
        @case ('cambio_password') {
          <p>Confirme que ya cambió su contraseña temporal.</p>
          <button type="button" (click)="completarCambioPassword()">Continuar</button>
        }
        @case ('perfil_corporativo') {
          <form (ngSubmit)="completarPerfil()">
            <label>Razón social <input [(ngModel)]="perfil.razon_social" name="razon_social" /></label>
            <label>Nombre <input [(ngModel)]="perfil.nombre" name="nombre" /></label>
            <button type="submit">Guardar perfil</button>
          </form>
        }
        @case ('preferencias') {
          <form (ngSubmit)="completarPreferencias()">
            <label>Canales
              <select [(ngModel)]="preferencias.canales_notificacion" name="canales">
                <option value="email">Email</option>
                <option value="sms">SMS</option>
                <option value="ambos">Ambos</option>
              </select>
            </label>
            <label>Teléfono SMS <input [(ngModel)]="preferencias.telefono_sms" name="telefono" /></label>
            <button type="submit">Finalizar onboarding</button>
          </form>
        }
        @default {
          <p>Onboarding completado.</p>
          <button type="button" (click)="irAGestion()">Ir a gestión de cuenta</button>
        }
      }
    }
    @if (error) {
      <p class="err">{{ error }}</p>
    }
  `,
  styles: [
    `
      ul {
        list-style: none;
        padding: 0;
        display: grid;
        gap: 0.25rem;
      }
      .done {
        color: #3b6d11;
      }
      form {
        display: grid;
        gap: 0.75rem;
        max-width: 28rem;
      }
      .err {
        color: #b42318;
      }
    `,
  ],
})
export class OnboardingWizardPage implements OnInit {
  readonly facade = inject(OnboardingFacadeService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  readonly idcliente = Number(this.route.snapshot.paramMap.get('idcliente'));
  readonly etapas: EtapaOnboarding[] = ['cambio_password', 'perfil_corporativo', 'preferencias'];

  progreso: OnboardingProgresoData | null = null;
  perfil: DatosEtapaPerfil = { razon_social: '', nombre: '' };
  preferencias: DatosEtapaPreferencias = { canales_notificacion: 'email', telefono_sms: '' };
  error = '';

  ngOnInit(): void {
    this.cargarProgreso();
  }

  cargarProgreso(): void {
    this.facade.loadProgreso(this.idcliente).subscribe({
      next: (data) => {
        this.progreso = data;
      },
      error: (err) => {
        this.error = err?.error?.detail ?? 'No se pudo cargar el progreso';
      },
    });
  }

  completarCambioPassword(): void {
    this.facade.completarCambioPassword(this.idcliente).subscribe({
      next: (data) => {
        this.progreso = data.progreso;
      },
      error: (err) => {
        this.error = err?.error?.detail ?? 'No se pudo completar la etapa';
      },
    });
  }

  completarPerfil(): void {
    this.facade.completarPerfil(this.idcliente, this.perfil).subscribe({
      next: (data) => {
        this.progreso = data.progreso;
      },
      error: (err) => {
        this.error = err?.error?.detail ?? 'No se pudo completar el perfil';
      },
    });
  }

  completarPreferencias(): void {
    this.facade.completarPreferencias(this.idcliente, this.preferencias).subscribe({
      next: (data) => {
        this.progreso = data.progreso;
      },
      error: (err) => {
        this.error = err?.error?.detail ?? 'No se pudo completar preferencias';
      },
    });
  }

  irAGestion(): void {
    this.router.navigate(['/cuentas-clientes/gestion-cuenta', this.idcliente, 'perfil']);
  }
}
