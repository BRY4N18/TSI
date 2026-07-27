import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { MetodoPago, TipoMetodoPago } from '../../services/models/suscripciones.types';
import { MetodoPagoApiService } from '../../services/metodo-pago-api.service';
import { billingBadge } from '../../billing-ui';

@Component({
  selector: 'app-metodos-pago',
  standalone: true,
  imports: [CommonModule, FormsModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './metodos-pago.page.html',
})
export class MetodosPagoPage implements OnInit {
  private readonly api = inject(MetodoPagoApiService);

  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly items = signal<MetodoPago[]>([]);
  readonly message = signal<string | null>(null);
  readonly busy = signal(false);

  tipo: TipoMetodoPago = 'tarjeta';
  numero = '';
  fechaexpiracion = '';

  badgeOk(): string {
    return billingBadge('ok');
  }

  badgeNeutral(): string {
    return billingBadge('neutral');
  }

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    this.loading.set(true);
    this.error.set(null);
    this.api.listar().subscribe({
      next: (res) => {
        this.items.set(res.data ?? []);
        this.loading.set(false);
      },
      error: (err) => {
        this.error.set(err?.error?.detail ?? 'Error al listar métodos de pago.');
        this.loading.set(false);
      },
    });
  }

  registrar(): void {
    this.busy.set(true);
    this.message.set(null);
    this.api
      .registrar(
        {
          tipo: this.tipo,
          datos_pasarela: {
            numero: this.numero,
            fechaexpiracion: this.fechaexpiracion || undefined,
          },
        },
        crypto.randomUUID(),
      )
      .subscribe({
        next: () => {
          this.message.set('Método registrado. El PAN no se almacena; solo token y últimos dígitos.');
          this.numero = '';
          this.fechaexpiracion = '';
          this.busy.set(false);
          this.cargar();
        },
        error: (err) => {
          this.message.set(err?.error?.detail ?? 'No se pudo registrar el método.');
          this.busy.set(false);
        },
      });
  }
}
