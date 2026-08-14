import { ChangeDetectorRef, Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';

import {
  PreferenciasOperativas,
  PreferenciasOperativasFormComponent,
  PreferenciasSerializadas,
  deserializarPreferencias,
} from '../../../shared/preferencias-operativas-form.component';
import { CuentaClienteApiService } from '../../services/cuenta-cliente-api.service';
import { PreferenciasData } from '../../models/cuenta-cliente.contract';

@Component({
  selector: 'app-preferencias-page',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, PreferenciasOperativasFormComponent],
  templateUrl: './preferencias.page.html',
})
export class PreferenciasPage implements OnInit {
  private readonly api = inject(CuentaClienteApiService);
  private readonly route = inject(ActivatedRoute);
  // El shell de la aplicación es OnPush: sin marcar la vista, nada de lo que
  // llega por HTTP se repinta. Ver §9 del design-system.
  private readonly cdr = inject(ChangeDetectorRef);

  preferencias: PreferenciasData | null = null;
  /**
   * Las cuatro dimensiones del SRS §3.2.3. Esta pantalla solo dejaba editar el
   * teléfono y el canal — este último como texto libre —, así que los umbrales,
   * las zonas y los destinatarios no se podían cambiar desde ninguna parte.
   */
  prefsForm: PreferenciasOperativas = deserializarPreferencias(null);
  razonSocial = '';
  mensaje = '';
  error = '';
  readonly idcliente = Number(this.route.snapshot.paramMap.get('idcliente')) || 1;

  ngOnInit(): void {
    this.api.getPreferencias(this.idcliente).subscribe({
      next: (res) => {
        this.cdr.markForCheck();
        this.preferencias = res.data;
        this.prefsForm = deserializarPreferencias(res.data);
      },
      error: () => {
        this.cdr.markForCheck();
        this.error = 'No se pudieron cargar las preferencias.';
      },
    });

    // El encabezado nombra la cuenta, no su identificador (§8 del design-system).
    this.api.getPerfil(this.idcliente).subscribe({
      next: (res) => {
        this.razonSocial = res.data.razon_social ?? '';
        this.cdr.markForCheck();
      },
      error: () => undefined,
    });
  }

  guardar(serializadas: PreferenciasSerializadas): void {
    this.api.patchPreferencias(this.idcliente, serializadas).subscribe({
      next: () => {
        this.cdr.markForCheck();
        this.mensaje = 'Preferencias guardadas.';
        this.error = '';
      },
      error: (err) => {
        this.cdr.markForCheck();
        this.error = err?.error?.detail ?? 'No se pudieron guardar las preferencias.';
      },
    });
  }
}
