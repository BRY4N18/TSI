/** Shared Tailwind class helpers for authenticated billing pages (no SCSS). */

const BADGE_BASE =
  'inline-flex min-h-6 items-center rounded-md px-2 py-0.5 text-xs font-medium';

export function billingBadge(
  kind: 'ok' | 'warn' | 'danger' | 'info' | 'neutral' = 'neutral',
): string {
  switch (kind) {
    case 'ok':
      return `${BADGE_BASE} bg-alert-success-bg text-alert-success`;
    case 'warn':
      return `${BADGE_BASE} bg-alert-warning-bg text-alert-warning`;
    case 'danger':
      return `${BADGE_BASE} bg-alert-critical-bg text-alert-critical`;
    case 'info':
      return `${BADGE_BASE} bg-alert-info-bg text-alert-info`;
    default:
      return `${BADGE_BASE} bg-border-default text-text-secondary`;
  }
}

export function billingEstadoBadge(estado?: string): string {
  switch (estado) {
    case 'Activa':
    case 'Pagada':
    case 'Aprobada':
      return billingBadge('ok');
    case 'Suspendida':
    case 'Pendiente':
      return billingBadge('warn');
    // Informativo, no error: el cobro esta detenido a proposito mientras se
    // resuelve el reclamo.
    case 'En disputa':
      return billingBadge('info');
    case 'Cancelada':
    case 'Fallida':
    case 'Rechazada':
      return billingBadge('danger');
    default:
      return billingBadge('neutral');
  }
}
