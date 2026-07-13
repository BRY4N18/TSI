import {
  AfterViewInit,
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  HostListener,
  OnDestroy,
  OnInit,
  inject,
  input,
  output,
  signal,
  viewChild,
} from '@angular/core';
import { FormsModule } from '@angular/forms';

import { ConnectivityService } from '../../../../shared/connectivity/connectivity.service';
import { NotificationService } from '../../../../shared/notifications/notification.service';
import { TablerIconComponent } from '../../../../shared/ui/icon/tabler-icon.component';
import { EvidenciaApiService } from '../../services/evidencia-api.service';
import { EvidenciaOfflineStoreService } from '../../services/evidencia-offline-store.service';
import { TipoNotaCampo } from '../../services/models/evidencia-unidad.types';

const MAX_FOTO_BYTES = 10 * 1024 * 1024;
const FOCUSABLE_SELECTOR =
  'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])';

@Component({
  selector: 'app-evidencia-captura-modal',
  standalone: true,
  imports: [FormsModule, TablerIconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div
      class="fixed inset-0 z-50 grid place-items-center bg-black/60 p-4"
      (click)="cerrar.emit()"
    >
      <div
        #dialog
        role="dialog"
        aria-modal="true"
        aria-labelledby="evidencia-modal-titulo"
        tabindex="-1"
        class="grid max-h-[90vh] w-full max-w-lg grid-rows-[auto_1fr_auto] overflow-hidden rounded-xl border border-border-default bg-bg-surface shadow-md"
        (click)="$event.stopPropagation()"
        (keydown)="onKeydown($event)"
      >
        <div class="flex items-center justify-between border-b border-border-default px-6 py-4">
          <div class="flex items-center gap-2">
            <app-tabler-icon name="upload" [size]="20" />
            <h2 id="evidencia-modal-titulo" class="m-0 text-base font-semibold text-text-primary">
              Subir evidencia y notas
            </h2>
          </div>
          <button
            type="button"
            (click)="cerrar.emit()"
            aria-label="Cerrar"
            class="inline-flex h-8 w-8 items-center justify-center rounded-md text-text-secondary hover:bg-bg-page"
          >
            <app-tabler-icon name="x" [size]="18" />
          </button>
        </div>

        <div class="grid gap-6 overflow-y-auto px-6 py-5">
          @if (!connectivity.online()) {
            <div
              class="rounded-md border border-alert-warning bg-alert-warning-bg px-4 py-3 text-sm text-alert-warning"
              data-testid="offline-banner"
            >
              Sin conexión. Lo que captures se guardará localmente y se sincronizará al reconectar.
            </div>
          }

          @if (error()) {
            <p class="m-0 text-sm text-alert-critical" data-testid="error">{{ error() }}</p>
          }

          <div class="grid gap-2">
            <span class="text-xs font-medium uppercase tracking-wide text-text-secondary">
              Fotografía
            </span>

            @if (!archivoFoto) {
              <label
                class="grid cursor-pointer place-items-center gap-2 rounded-md border-2 border-dashed p-8 text-center"
                [class.border-accent-primary]="arrastrando()"
                [class.bg-bg-page]="arrastrando()"
                [class.border-border-default]="!arrastrando()"
                (dragover)="onDragOver($event)"
                (dragleave)="arrastrando.set(false)"
                (drop)="onDrop($event)"
              >
                <span class="grid h-10 w-10 place-items-center rounded-md bg-bg-page text-text-secondary">
                  <app-tabler-icon name="upload" [size]="20" />
                </span>
                <span class="text-sm font-semibold text-text-primary">Arrastra una foto aquí</span>
                <span class="text-sm text-text-secondary">o haz clic para seleccionar</span>
                <span class="text-xs text-text-secondary">JPG o PNG, máx. 10MB</span>
                <input
                  type="file"
                  accept="image/jpeg,image/png"
                  class="hidden"
                  (change)="onFotoSeleccionada($event)"
                />
              </label>
            } @else {
              <div class="flex items-center gap-3 rounded-md border border-border-default bg-bg-page p-3">
                <span class="grid h-9 w-9 shrink-0 place-items-center rounded-md bg-bg-surface text-text-secondary">
                  <app-tabler-icon name="camera" [size]="16" />
                </span>
                <div class="grid min-w-0 flex-1">
                  <span class="truncate text-sm font-medium text-text-primary">{{ archivoFoto.name }}</span>
                  <span class="text-xs text-text-secondary">{{ formatearTamano(archivoFoto.size) }}</span>
                </div>
                <button
                  type="button"
                  (click)="archivoFoto = null"
                  aria-label="Quitar foto"
                  class="inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-text-secondary hover:bg-bg-surface"
                >
                  <app-tabler-icon name="x" [size]="14" />
                </button>
              </div>
            }

            <div class="flex flex-wrap gap-3">
              <button
                type="button"
                (click)="subirFoto()"
                [disabled]="!archivoFoto || cargando()"
                class="inline-flex items-center gap-2 rounded-md bg-accent-primary px-4 py-2 text-sm font-semibold text-white [&:hover:not(:disabled)]:bg-accent-hover disabled:cursor-not-allowed disabled:opacity-50"
              >
                @if (cargando()) {
                  <app-tabler-icon name="refresh" [size]="14" />
                  Sincronizando…
                } @else {
                  Subir en línea
                }
              </button>
              <button
                type="button"
                (click)="guardarFotoOffline()"
                [disabled]="!archivoFoto || cargando()"
                class="inline-flex items-center gap-2 rounded-md border border-border-default px-4 py-2 text-sm font-medium text-text-secondary hover:bg-bg-page disabled:cursor-not-allowed disabled:opacity-50"
              >
                Guardar offline
              </button>
            </div>
          </div>

          <div class="grid gap-2">
            <span class="text-xs font-medium uppercase tracking-wide text-text-secondary">
              Nota de campo
            </span>

            <form (ngSubmit)="registrarNota()" class="grid gap-3">
              <div class="grid gap-1.5">
                <label for="tipoNota" class="text-sm font-medium text-text-secondary">Tipo</label>
                <select
                  id="tipoNota"
                  name="tipo"
                  [(ngModel)]="tipoNota"
                  required
                  class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:outline focus:outline-2 focus:outline-offset-1 focus:outline-accent-primary"
                >
                  @for (tipo of tiposNota; track tipo) {
                    <option [value]="tipo">{{ tipo }}</option>
                  }
                </select>
              </div>

              <div class="grid gap-1.5">
                <label for="textoNota" class="text-sm font-medium text-text-secondary">Nota</label>
                <textarea
                  id="textoNota"
                  name="nota"
                  rows="3"
                  [(ngModel)]="textoNota"
                  required
                  class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:outline focus:outline-2 focus:outline-offset-1 focus:outline-accent-primary"
                ></textarea>
              </div>

              <div class="flex flex-wrap gap-3">
                <button
                  type="submit"
                  [disabled]="cargando()"
                  class="inline-flex items-center gap-2 rounded-md bg-accent-primary px-4 py-2 text-sm font-semibold text-white [&:hover:not(:disabled)]:bg-accent-hover disabled:cursor-not-allowed disabled:opacity-50"
                >
                  @if (cargando()) {
                    <app-tabler-icon name="refresh" [size]="14" />
                    Sincronizando…
                  } @else {
                    Registrar en línea
                  }
                </button>
                <button
                  type="button"
                  (click)="guardarNotaOffline()"
                  [disabled]="cargando()"
                  class="inline-flex items-center gap-2 rounded-md border border-border-default px-4 py-2 text-sm font-medium text-text-secondary hover:bg-bg-page disabled:cursor-not-allowed disabled:opacity-50"
                >
                  Guardar offline
                </button>
              </div>
            </form>
          </div>
        </div>

        <div class="flex justify-end gap-3 border-t border-border-default px-6 py-4">
          <button
            type="button"
            (click)="cerrar.emit()"
            class="inline-flex items-center gap-2 rounded-md border border-border-default px-4 py-2 text-sm font-medium text-text-secondary hover:bg-bg-page"
          >
            Cerrar
          </button>
        </div>
      </div>
    </div>
  `,
})
export class EvidenciaCapturaModal implements AfterViewInit, OnInit, OnDestroy {
  private readonly evidenciaApi = inject(EvidenciaApiService);
  private readonly offlineStore = inject(EvidenciaOfflineStoreService);
  private readonly notifications = inject(NotificationService);
  readonly connectivity = inject(ConnectivityService);

  private readonly dialogRef = viewChild.required<ElementRef<HTMLElement>>('dialog');
  private elementoConFocoPrevio: HTMLElement | null = null;

  readonly idaccidente = input.required<string>();
  readonly cerrar = output<void>();
  readonly guardado = output<void>();

  readonly error = signal('');
  readonly cargando = signal(false);
  readonly arrastrando = signal(false);

  archivoFoto: File | null = null;
  textoNota = '';
  tipoNota: TipoNotaCampo = 'Observación general';
  readonly tiposNota: TipoNotaCampo[] = [
    'Observación general',
    'Declaración de testigo',
    'Daños materiales',
    'Condiciones del sitio',
  ];

  ngOnInit(): void {
    this.elementoConFocoPrevio = document.activeElement as HTMLElement | null;
  }

  ngAfterViewInit(): void {
    this.dialogRef().nativeElement.focus();
  }

  ngOnDestroy(): void {
    this.elementoConFocoPrevio?.focus();
  }

  @HostListener('document:keydown.escape')
  onEscape(): void {
    this.cerrar.emit();
  }

  onKeydown(event: Event): void {
    if (!(event instanceof KeyboardEvent) || event.key !== 'Tab') {
      return;
    }
    const focusables = Array.from(
      this.dialogRef().nativeElement.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR),
    );
    if (!focusables.length) {
      return;
    }
    const first = focusables[0];
    const last = focusables[focusables.length - 1];
    const activo = document.activeElement;

    if (event.shiftKey && activo === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && activo === last) {
      event.preventDefault();
      first.focus();
    }
  }

  formatearTamano(bytes: number): string {
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  onDragOver(event: DragEvent): void {
    event.preventDefault();
    this.arrastrando.set(true);
  }

  onDrop(event: DragEvent): void {
    event.preventDefault();
    this.arrastrando.set(false);
    const archivo = event.dataTransfer?.files?.[0];
    if (archivo) {
      this.seleccionarArchivo(archivo);
    }
  }

  onFotoSeleccionada(event: Event): void {
    const input = event.target as HTMLInputElement;
    const archivo = input.files?.[0];
    if (archivo) {
      this.seleccionarArchivo(archivo);
    }
  }

  private seleccionarArchivo(archivo: File): void {
    if (!['image/jpeg', 'image/png'].includes(archivo.type)) {
      this.error.set('Solo se permiten imágenes JPG o PNG');
      return;
    }
    if (archivo.size > MAX_FOTO_BYTES) {
      this.error.set('La foto excede el tamaño máximo de 10MB');
      return;
    }
    this.error.set('');
    this.archivoFoto = archivo;
  }

  subirFoto(): void {
    if (!this.archivoFoto) {
      return;
    }
    this.error.set('');
    this.cargando.set(true);
    this.evidenciaApi.subirFoto(this.idaccidente(), this.archivoFoto).subscribe({
      next: () => {
        this.notifications.toast('Foto subida correctamente', 'success');
        this.archivoFoto = null;
        this.cargando.set(false);
        this.guardado.emit();
      },
      error: () => {
        this.error.set('No se pudo subir la foto');
        this.notifications.alert('No se pudo subir la foto.', 'Error al subir evidencia');
        this.cargando.set(false);
      },
    });
  }

  async guardarFotoOffline(): Promise<void> {
    if (!this.archivoFoto) {
      return;
    }
    this.error.set('');
    this.cargando.set(true);
    try {
      await this.offlineStore.guardarFotoPendiente(
        this.idaccidente(),
        this.archivoFoto,
        this.archivoFoto.type,
        Date.now(),
      );
      this.notifications.toast('Foto guardada localmente para sincronización', 'success');
      this.archivoFoto = null;
      this.guardado.emit();
    } catch {
      this.error.set('No se pudo guardar la foto offline');
      this.notifications.alert('No se pudo guardar la foto offline.', 'Error al guardar');
    } finally {
      this.cargando.set(false);
    }
  }

  registrarNota(): void {
    this.error.set('');
    this.cargando.set(true);
    this.evidenciaApi
      .registrarNota(this.idaccidente(), { nota: this.textoNota, tipo: this.tipoNota })
      .subscribe({
        next: () => {
          this.notifications.toast('Nota registrada', 'success');
          this.textoNota = '';
          this.cargando.set(false);
          this.guardado.emit();
        },
        error: () => {
          this.error.set('No se pudo registrar la nota');
          this.notifications.alert('No se pudo registrar la nota.', 'Error al registrar');
          this.cargando.set(false);
        },
      });
  }

  async guardarNotaOffline(): Promise<void> {
    this.error.set('');
    this.cargando.set(true);
    try {
      await this.offlineStore.guardarNotaPendiente(
        this.idaccidente(),
        this.textoNota,
        this.tipoNota,
        Date.now(),
      );
      this.notifications.toast('Nota guardada localmente', 'success');
      this.textoNota = '';
      this.guardado.emit();
    } catch {
      this.error.set('No se pudo guardar la nota offline');
      this.notifications.alert('No se pudo guardar la nota offline.', 'Error al guardar');
    } finally {
      this.cargando.set(false);
    }
  }
}
