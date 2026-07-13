import { ChangeDetectionStrategy, Component, EventEmitter, Input, OnChanges, Output } from '@angular/core';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-duplicado-fusion-dialog',
  standalone: true,
  imports: [FormsModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="fixed inset-0 z-40 grid place-items-center bg-black/40 p-4">
      <dialog
        open
        class="w-full max-w-md rounded-lg border border-border-default bg-bg-surface p-6 shadow-xl"
      >
        <h2 class="m-0 mb-2 text-lg font-semibold text-text-primary">Posible duplicado</h2>
        <p class="m-0 mb-4 text-sm text-text-secondary">
          Se detectó un reporte similar. Confirme la fusión (CU-O41) o cancele para registrar el
          caso como independiente.
        </p>
        <label for="idPrincipal" class="mb-1.5 block text-sm font-medium text-text-secondary">
          ID del caso padre (más antiguo sugerido)
        </label>
        <input
          id="idPrincipal"
          class="mb-4 w-full rounded-md border border-border-default px-3.5 py-2.5 text-text-primary focus:outline focus:outline-2 focus:outline-offset-1 focus:outline-accent-primary"
          [(ngModel)]="idPrincipal"
          name="idPrincipal"
        />
        <div class="flex justify-end gap-3">
          <button
            type="button"
            class="rounded-md border border-border-default px-4 py-2 text-sm font-medium text-text-primary hover:bg-bg-page"
            (click)="cancelar.emit()"
          >
            Cancelar
          </button>
          <button
            type="button"
            class="rounded-md bg-accent-primary px-4 py-2 text-sm font-semibold text-white [&:hover:not(:disabled)]:bg-accent-hover"
            (click)="confirmar.emit(idPrincipal)"
          >
            Fusionar
          </button>
        </div>
      </dialog>
    </div>
  `,
})
export class DuplicadoFusionDialog implements OnChanges {
  @Input() idPrincipalSugerido = '';
  @Output() confirmar = new EventEmitter<string>();
  @Output() cancelar = new EventEmitter<void>();

  idPrincipal = '';

  ngOnChanges(): void {
    this.idPrincipal = this.idPrincipalSugerido;
  }
}
