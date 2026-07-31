/** Shared Tailwind helpers for Ventas-CRM authenticated pages. */

const BADGE_BASE =
  'inline-flex min-h-6 items-center rounded-md px-2 py-0.5 text-xs font-medium';

export function crmBadge(kind: 'ok' | 'warn' | 'danger' | 'info' | 'neutral' = 'neutral'): string {
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
