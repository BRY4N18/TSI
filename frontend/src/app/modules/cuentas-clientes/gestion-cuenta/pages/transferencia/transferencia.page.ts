import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';

import { CuentaClienteApiService } from '../../services/cuenta-cliente-api.service';
import { UsuarioElegible } from '../../models/cuenta-cliente.contract';

@Component({
  selector: 'app-transferencia-page',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './transferencia.page.html',
})
export class TransferenciaPage implements OnInit {
  private readonly api = inject(CuentaClienteApiService);
  private readonly route = inject(ActivatedRoute);

  usuarios: UsuarioElegible[] = [];
  selectedId: number | null = null;
  mensaje = '';
  error = '';
  readonly idcliente = Number(this.route.snapshot.paramMap.get('idcliente')) || 1;

  ngOnInit(): void {
    this.api.listUsuariosElegibles(this.idcliente).subscribe({
      next: (res) => {
        this.usuarios = res.data.usuarios;
        this.selectedId = this.usuarios[0]?.idusuario ?? null;
      },
      error: () => {
        this.error = 'No se pudieron cargar los usuarios elegibles.';
      },
    });
  }

  transferir(): void {
    if (!this.selectedId) return;
    this.api.transferirPropiedad(this.idcliente, this.selectedId).subscribe({
      next: () => {
        this.mensaje = 'Transferencia confirmada.';
        this.error = '';
      },
      error: () => {
        this.error = 'No se pudo transferir la propiedad.';
      },
    });
  }
}
