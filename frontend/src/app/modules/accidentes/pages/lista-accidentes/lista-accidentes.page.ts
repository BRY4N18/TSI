import { DatePipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { debounceTime } from 'rxjs';

import { TablerIconComponent } from '../../../../shared/ui/icon/tabler-icon.component';
import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';
import { AccidenteApiService } from '../../services/accidente-api.service';
import {
  AccidenteListItem,
  CatalogoItem,
  EstadoAccidente,
  UbicacionLegible,
} from '../../services/models/accidente.types';
import { UbicacionCatalogoApiService } from '../../services/ubicacion-catalogo-api.service';
import { SEVERIDAD_INFO, SeveridadInfo } from '../../severidad.constants';
import { ESTADOS, EstadoInfo, estadoInfo as estadoInfoOf } from '../../estado.constants';

@Component({
  selector: 'app-lista-accidentes',
  standalone: true,
  imports: [RouterLink, ReactiveFormsModule, TablerIconComponent, DatePipe],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './lista-accidentes.page.html',
})
export class ListaAccidentesPage implements OnInit {
  private readonly api = inject(AccidenteApiService);
  private readonly ubicacionCatalogo = inject(UbicacionCatalogoApiService);
  private readonly fb = inject(FormBuilder);
  private readonly authApi = inject(AuthApiService);

  puedeRegistrar(): boolean {
    return this.authApi.hasAnyRole(['Operador', 'Administrador']);
  }

  readonly severidadOptions = Object.entries(SEVERIDAD_INFO).map(([value, info]) => ({
    value: Number(value),
    label: info.label,
  }));
  readonly estados = ESTADOS;

  readonly paises = signal<CatalogoItem[]>([]);
  readonly estadosRegion = signal<CatalogoItem[]>([]);

  readonly accidentes = signal<AccidenteListItem[]>([]);
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);

  readonly filtros = this.fb.group({
    idpais: [null as number | null],
    idestadoregion: [null as number | null],
    idseveridad: [null as number | null],
    estado: [null as EstadoAccidente | null],
    fechaDesde: [''],
    fechaHasta: [''],
    activo: [true],
  });

  ngOnInit(): void {
    this.cargar();
    this.ubicacionCatalogo.listarPaises().subscribe((paises) => this.paises.set(paises));

    this.filtros.controls.idpais.valueChanges.subscribe((idpais) => {
      this.filtros.controls.idestadoregion.setValue(null, { emitEvent: false });
      this.estadosRegion.set([]);
      if (idpais) {
        this.ubicacionCatalogo.listarEstados(idpais).subscribe((estados) => this.estadosRegion.set(estados));
      }
    });

    this.filtros.valueChanges.pipe(debounceTime(300)).subscribe(() => this.cargar());
  }

  severidadInfo(idseveridad: number): SeveridadInfo {
    return (
      SEVERIDAD_INFO[idseveridad] ?? {
        value: idseveridad,
        label: `Sev. ${idseveridad}`,
        icon: 'info-circle',
        tone: 'success',
      }
    );
  }

  estadoInfo(estado: EstadoAccidente | null | undefined): EstadoInfo {
    return estadoInfoOf(estado);
  }

  ubicacionLabel(ubicacion: UbicacionLegible | null | undefined): string {
    if (!ubicacion) {
      return '—';
    }
    return [ubicacion.calle, ubicacion.ciudad].filter(Boolean).join(', ') || '—';
  }

  cargar(): void {
    const raw = this.filtros.getRawValue();
    this.loading.set(true);
    this.error.set(null);

    this.api
      .listar({
        idseveridad: raw.idseveridad ?? undefined,
        estado: raw.estado ?? undefined,
        activo: raw.activo ?? undefined,
        fechaDesde: raw.fechaDesde ? new Date(raw.fechaDesde).getTime() : undefined,
        fechaHasta: raw.fechaHasta ? new Date(raw.fechaHasta).getTime() : undefined,
        idestadoregion: raw.idestadoregion ?? undefined,
      })
      .subscribe({
        next: (res) => {
          this.accidentes.set(res.data);
          this.loading.set(false);
        },
        error: () => {
          this.error.set('No se pudo cargar la lista de accidentes.');
          this.loading.set(false);
        },
      });
  }
}
