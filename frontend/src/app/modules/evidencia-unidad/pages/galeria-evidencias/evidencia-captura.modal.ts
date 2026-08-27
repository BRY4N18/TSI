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
            <h2 id="evidencia-modal-titulo" class="tsi-display m-0 text-base font-semibold text-text-primary">
              Subir evidencia y notas
            </h2>
          </div>
          <button
            type="button"
            (click)="cerrar.emit()"
            aria-label="Cerrar"
            class="tsi-hit-target inline-flex h-8 w-8 items-center justify-center rounded-md text-text-secondary hover:bg-bg-page"
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
                <!-- Miniatura real del archivo elegido: el ícono genérico no
                     dejaba comprobar que la foto seleccionada era la correcta
                     (hallazgo #11). -->
                <img
                  [src]="previewFoto()"
                  alt="Vista previa de la evidencia seleccionada"
                  data-testid="preview-foto"
                  class="h-14 w-14 shrink-0 rounded-md border border-border-default object-cover"
                />
                <div class="grid min-w-0 flex-1">
                  <span class="truncate text-sm font-medium text-text-primary">{{ archivoFoto.name }}</span>
                  <span class="text-xs text-text-secondary">{{ formatearTamano(archivoFoto.size) }}</span>
                </div>
                <button
                  type="button"
                  (click)="quitarFoto()"
                  aria-label="Quitar foto"
                  class="tsi-hit-target inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-text-secondary hover:bg-bg-surface"
                >
                  <app-tabler-icon name="x" [size]="14" />
                </button>
              </div>
            }
          </div>

          <div class="grid gap-2">
            <span class="text-xs font-medium uppercase tracking-wide text-text-secondary">
              Nota de campo
            </span>

            <div class="grid gap-3">
              <div class="grid gap-1.5">
                <label for="tipoNota" class="text-sm font-medium text-text-secondary">Tipo</label>
                <select
                  id="tipoNota"
                  name="tipo"
                  [(ngModel)]="tipoNota"
                  required
                  class="tsi-select w-full min-w-0"
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
                  class="tsi-textarea w-full"
                  placeholder="Escribe el detalle"
                ></textarea>
              </div>
            </div>
          </div>
        </div>

        <!--
          Un solo botón para todo el cuadro de diálogo.

          Antes había cuatro: "Subir en línea"/"Guardar offline" para la foto y
          "Registrar en línea"/"Guardar offline" para la nota, cada par enviando
          solo su mitad. Quien adjuntaba la foto y escribía la nota perdía la
          nota (hallazgos #10 y, en su forma real, la aclaración de la revisión:
          "se sube solo uno a la vez"). Además obligaba a la unidad a decidir el
          modo de transporte, algo que el sistema ya sabe por sí mismo.
        -->
        <div class="grid gap-3 border-t border-border-default px-6 py-4">
          @if (hayAlgoQueGuardar()) {
            <p class="m-0 text-xs text-text-secondary" data-testid="resumen-envio">
              Se guardará: {{ resumenPendiente() }}.
            </p>
          }
          <div class="flex justify-end gap-3">
            <button
              type="button"
              (click)="cerrar.emit()"
              [disabled]="cargando()"
              class="tsi-btn tsi-btn-secondary"
            >
              Cerrar
            </button>
            <button
              type="button"
              data-testid="btn-guardar-evidencia"
              (click)="guardarTodo()"
              [disabled]="!hayAlgoQueGuardar() || cargando()"
              class="tsi-btn tsi-btn-primary"
            >
              @if (cargando()) {
                <app-tabler-icon name="refresh" [size]="14" />
                Guardando…
              } @else if (!connectivity.online()) {
                Guardar para sincronizar
              } @else {
                Guardar evidencia
              }
            </button>
          </div>
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
  /** objectURL de la miniatura; se revoca al reemplazarla y al destruir. */
  readonly previewFoto = signal('');

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
    const preview = this.previewFoto();
    if (preview) {
      URL.revokeObjectURL(preview);
    }
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
    this.regenerarPreview(archivo);
  }

  // ── Miniatura ──────────────────────────────────────────────────────────────

  private regenerarPreview(archivo: File | null): void {
    // Cada objectURL reservado hay que devolverlo: sin el revoke, elegir varias
    // fotos seguidas iba dejando blobs colgados en memoria.
    const anterior = this.previewFoto();
    if (anterior) {
      URL.revokeObjectURL(anterior);
    }
    this.previewFoto.set(archivo ? URL.createObjectURL(archivo) : '');
  }

  quitarFoto(): void {
    this.archivoFoto = null;
    this.regenerarPreview(null);
  }

  // ── Envío único ────────────────────────────────────────────────────────────

  hayAlgoQueGuardar(): boolean {
    return this.archivoFoto !== null || this.textoNota.trim().length > 0;
  }

  resumenPendiente(): string {
    const partes: string[] = [];
    if (this.archivoFoto) {
      partes.push('1 fotografía');
    }
    if (this.textoNota.trim()) {
      partes.push(`nota de campo (${this.tipoNota})`);
    }
    return partes.join(' y ');
  }

  /**
   * Guarda **todo** lo que haya en el cuadro de diálogo: la foto y la nota, en
   * una sola acción.
   *
   * Foto y nota son dos endpoints distintos y siguen siéndolo; lo que cambia es
   * que ya no dependen de dos botones separados. Si falla una de las dos, se
   * conserva **solo la que falló** para que la unidad reintente sin volver a
   * escribir lo que ya se guardó.
   *
   * El modo de transporte no lo elige la unidad: sin conexión va a la cola
   * local, y una subida que falla por red también cae a la cola en vez de
   * perderse.
   */
  async guardarTodo(): Promise<void> {
    if (!this.hayAlgoQueGuardar()) {
      return;
    }
    this.error.set('');
    this.cargando.set(true);

    const fallos: string[] = [];
    const guardados: string[] = [];
    let quedaOffline = false;

    if (this.archivoFoto) {
      const resultado = await this.persistirFoto(this.archivoFoto);
      if (resultado === 'error') {
        fallos.push('la fotografía');
      } else {
        guardados.push('fotografía');
        quedaOffline ||= resultado === 'offline';
        this.quitarFoto();
      }
    }

    if (this.textoNota.trim()) {
      const resultado = await this.persistirNota(this.textoNota.trim(), this.tipoNota);
      if (resultado === 'error') {
        fallos.push('la nota de campo');
      } else {
        guardados.push('nota de campo');
        quedaOffline ||= resultado === 'offline';
        this.textoNota = '';
      }
    }

    this.cargando.set(false);

    if (fallos.length) {
      const detalle = `No se pudo guardar ${fallos.join(' ni ')}. Vuelve a intentarlo.`;
      this.error.set(detalle);
      this.notifications.alert(detalle, 'Error al guardar evidencia');
    }
    if (guardados.length) {
      this.notifications.toast(
        quedaOffline
          ? `Guardado localmente (${guardados.join(' y ')}); se sincronizará al reconectar`
          : `Evidencia guardada (${guardados.join(' y ')})`,
        'success',
      );
      this.guardado.emit();
    }
  }

  private async persistirFoto(archivo: File): Promise<'online' | 'offline' | 'error'> {
    if (this.connectivity.online()) {
      const subido = await this.intentarSubirFoto(archivo);
      if (subido) {
        return 'online';
      }
      // Falló la red con el navegador creyéndose en línea: no se pierde, se
      // encola.
    }
    try {
      await this.offlineStore.guardarFotoPendiente(
        this.idaccidente(),
        archivo,
        archivo.type,
        Date.now(),
      );
      return 'offline';
    } catch {
      return 'error';
    }
  }

  private intentarSubirFoto(archivo: File): Promise<boolean> {
    return new Promise((resolve) => {
      this.evidenciaApi.subirFoto(this.idaccidente(), archivo).subscribe({
        next: () => resolve(true),
        error: () => resolve(false),
      });
    });
  }

  private async persistirNota(
    nota: string,
    tipo: TipoNotaCampo,
  ): Promise<'online' | 'offline' | 'error'> {
    if (this.connectivity.online()) {
      const registrada = await this.intentarRegistrarNota(nota, tipo);
      if (registrada) {
        return 'online';
      }
    }
    try {
      await this.offlineStore.guardarNotaPendiente(this.idaccidente(), nota, tipo, Date.now());
      return 'offline';
    } catch {
      return 'error';
    }
  }

  private intentarRegistrarNota(nota: string, tipo: TipoNotaCampo): Promise<boolean> {
    return new Promise((resolve) => {
      this.evidenciaApi.registrarNota(this.idaccidente(), { nota, tipo }).subscribe({
        next: () => resolve(true),
        error: () => resolve(false),
      });
    });
  }
}
