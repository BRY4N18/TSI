import { ChangeDetectionStrategy, Component, OnDestroy, inject, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';

import { TablerIconComponent } from '../../../../shared/ui/icon/tabler-icon.component';
import { LIST_PAGE_SHELL_CLASS } from '../../../../shared/ui/list-states/list-table.styles';
import { presentacionEntorno } from '../../entorno.constants';
import type { CredencialEmitida } from '../../services/models/partner.types';

/** Clave del estado de navegación por el que viaja la credencial recién emitida. */
export const ESTADO_CREDENCIAL_EMITIDA = 'credencialEmitida';

/**
 * Entrega del secreto — el punto de mayor riesgo de error de usuario del módulo.
 *
 * RN-PON-005 hace el secreto IRRECUPERABLE: solo se muestra aquí, una vez. De
 * ahí cada decisión de esta pantalla:
 *
 * - **Página dedicada, no modal.** Un modal se cierra con Esc o con un click
 *   fuera, y el secreto se perdería sin que el usuario lo hubiera guardado.
 * - **Sin parámetros de ruta.** La credencial llega por estado de navegación en
 *   memoria: una URL se comparte, entra en el historial y aparece en logs de
 *   proxy (FR-UI-021).
 * - **La salida está deshabilitada** hasta que el usuario confirma que lo
 *   guardó (FR-UI-020).
 * - **Al recargar no hay estado**, y eso se explica en vez de romper la
 *   pantalla (FR-UI-022): es el escenario en que el usuario YA perdió el
 *   secreto y lo que necesita es saber cómo recuperarse.
 *
 * El valor vive solo en memoria de este componente y se descarta al salir.
 */
@Component({
  selector: 'app-secreto-emitido',
  standalone: true,
  imports: [RouterLink, TablerIconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <section [class]="shellClass">
      @if (credencial(); as c) {
        <p class="m-0 text-xs font-medium uppercase tracking-wide text-text-secondary">
          Credencial emitida
        </p>
        <h1 class="mb-2 mt-1 text-2xl font-bold text-text-primary">{{ c.nombre_credencial }}</h1>
        <span
          class="inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-xs font-medium"
          [class]="entorno(c).tono"
        >
          <app-tabler-icon [name]="entorno(c).icono" [size]="14" />
          {{ entorno(c).etiqueta }}
        </span>

        <!-- El aviso va ANTES del valor: cuando el usuario lo lee, todavía
             está a tiempo de prepararse para guardarlo. -->
        <div
          class="mt-6 rounded-lg border border-alert-media bg-alert-media-bg p-4"
          data-testid="aviso-irreversible"
          role="alert"
        >
          <p class="m-0 flex items-start gap-2 text-sm font-medium text-alert-media">
            <app-tabler-icon name="alert-triangle" [size]="18" />
            <span>
              Este secreto se muestra <strong>una sola vez</strong>. No podremos volver a
              mostrártelo: guárdalo ahora en un lugar seguro.
            </span>
          </p>
        </div>

        <div class="mt-4 grid gap-4">
          <div class="rounded-lg border border-border-default bg-bg-surface p-4">
            <p class="m-0 mb-2 text-xs font-medium uppercase tracking-wide text-text-secondary">
              Client ID
            </p>
            <div class="flex flex-wrap items-center gap-3">
              <code class="font-mono text-sm text-text-primary" data-testid="valor-client-id">{{
                c.client_id
              }}</code>
              <button
                type="button"
                data-testid="btn-copiar-id"
                class="inline-flex items-center gap-1.5 rounded-md border border-border-default px-3 py-1.5 text-xs font-medium text-text-secondary hover:text-text-primary"
                (click)="copiar(c.client_id, 'id')"
              >
                <app-tabler-icon name="copy" [size]="14" />
                {{ copiado() === 'id' ? 'Copiado' : 'Copiar' }}
              </button>
            </div>
          </div>

          <div class="rounded-lg border border-border-default bg-bg-surface p-4">
            <p class="m-0 mb-2 text-xs font-medium uppercase tracking-wide text-text-secondary">
              Client secret
            </p>
            <div class="flex flex-wrap items-center gap-3">
              <code
                class="break-all font-mono text-sm text-text-primary"
                data-testid="valor-client-secret"
                >{{ c.client_secret }}</code
              >
              <button
                type="button"
                data-testid="btn-copiar-secreto"
                class="inline-flex items-center gap-1.5 rounded-md border border-accent-primary px-3 py-1.5 text-xs font-medium text-accent-primary hover:bg-bg-page"
                (click)="copiar(c.client_secret, 'secreto')"
              >
                <app-tabler-icon name="copy" [size]="14" />
                {{ copiado() === 'secreto' ? 'Copiado' : 'Copiar' }}
              </button>
            </div>
          </div>
        </div>

        <label
          class="mt-6 flex cursor-pointer items-start gap-3 text-sm text-text-primary"
          for="confirmacion"
        >
          <input
            id="confirmacion"
            type="checkbox"
            data-testid="check-guardado"
            class="mt-0.5 h-5 w-5"
            [checked]="confirmado()"
            (change)="alternarConfirmacion()"
          />
          <span>He guardado el secreto en un lugar seguro.</span>
        </label>

        <div class="mt-6">
          <button
            type="button"
            data-testid="btn-continuar"
            class="rounded-lg bg-accent-primary px-5 py-2.5 text-sm font-medium text-white disabled:opacity-50"
            [disabled]="!confirmado()"
            (click)="continuar()"
          >
            Continuar a mi integración
          </button>
        </div>
      } @else {
        <!-- Sin estado de navegación: el usuario recargó o llegó por la URL.
             Ya perdió el secreto, así que lo que necesita es saber cómo
             recuperarse, no una pantalla rota. -->
        <p class="m-0 text-xs font-medium uppercase tracking-wide text-text-secondary">
          Credencial emitida
        </p>
        <h1 class="mb-3 mt-1 text-2xl font-bold text-text-primary">
          El secreto ya no está disponible
        </h1>
        <div
          class="rounded-lg border border-border-default bg-bg-surface p-6"
          data-testid="secreto-no-disponible"
        >
          <p class="m-0 text-sm text-text-secondary">
            Por seguridad, el secreto solo se muestra una vez, en el momento de emitirlo, y no
            queda guardado en ningún sitio desde el que podamos recuperarlo.
          </p>
          <p class="mt-3 text-sm text-text-secondary">
            Si no alcanzaste a guardarlo, emite una credencial nueva desde tu integración:
            <strong>hacerlo no interrumpe las credenciales que ya tienes</strong>.
          </p>
          <a
            routerLink="/partners/portal"
            data-testid="link-volver-integracion"
            class="mt-4 inline-flex items-center gap-2 rounded-lg bg-accent-primary px-5 py-2.5 text-sm font-medium text-white"
          >
            <app-tabler-icon name="arrow-left" [size]="16" />
            Volver a mi integración
          </a>
        </div>
      }
    </section>
  `,
})
export class SecretoEmitidoPage implements OnDestroy {
  private readonly router = inject(Router);

  /** Vive SOLO en memoria. Nunca se persiste ni se refleja en la URL. */
  readonly credencial = signal<CredencialEmitida | null>(null);
  readonly confirmado = signal(false);
  readonly copiado = signal<'id' | 'secreto' | null>(null);

  readonly shellClass = LIST_PAGE_SHELL_CLASS;

  constructor() {
    const estado =
      this.router.getCurrentNavigation()?.extras?.state ??
      (typeof history !== 'undefined' ? history.state : null);
    const recibida = (estado ?? {})[ESTADO_CREDENCIAL_EMITIDA] as CredencialEmitida | undefined;
    if (recibida?.client_secret) {
      this.credencial.set(recibida);
    }
    // Se limpia el estado del historial para que una recarga —o el botón
    // «atrás»— no vuelva a exponer el secreto.
    this.limpiarHistorial();
  }

  entorno(c: CredencialEmitida) {
    return presentacionEntorno(c.entorno);
  }

  alternarConfirmacion(): void {
    this.confirmado.update((v) => !v);
  }

  copiar(valor: string, cual: 'id' | 'secreto'): void {
    void navigator.clipboard?.writeText(valor);
    this.copiado.set(cual);
  }

  continuar(): void {
    if (!this.confirmado()) {
      return;
    }
    void this.router.navigate(['/partners/portal']);
  }

  /** Al salir, el valor desaparece con el componente. */
  ngOnDestroy(): void {
    this.credencial.set(null);
  }

  private limpiarHistorial(): void {
    try {
      history.replaceState({}, '');
    } catch {
      // Sin acceso al historial el secreto sigue sin persistirse en ningún
      // almacenamiento; no es motivo para romper la pantalla.
    }
  }
}
