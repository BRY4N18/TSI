/**
 * Clases Tailwind canónicas para tablas operativas (design-system § tablas /
 * patrón lista-accidentes). Reutilizar en módulos fuera de Accidentes.
 */
export const LIST_TABLE_CLASS =
  'hidden w-full border-collapse overflow-hidden rounded-lg border border-border-default md:table';

export const LIST_TABLE_TH_CLASS =
  'border-b border-border-default px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-text-primary';

export const LIST_TABLE_TH_RIGHT_CLASS =
  'border-b border-border-default px-4 py-3 text-right text-xs font-medium uppercase tracking-wide text-text-primary';

export const LIST_TABLE_TD_CLASS = 'px-4 py-3 text-sm text-text-secondary';

export const LIST_TABLE_TD_PRIMARY_CLASS = 'px-4 py-3 text-sm font-semibold text-text-primary';

export const LIST_ROW_CLASS = 'border-b border-border-default bg-bg-page even:bg-bg-surface';

export const LIST_ACTION_ICON_BTN_CLASS =
  'inline-flex h-11 w-11 items-center justify-center rounded-md text-text-secondary hover:bg-bg-page hover:text-text-primary';

export const LIST_MOBILE_CARD_CLASS =
  'rounded-lg border border-border-default bg-bg-surface p-4';

export const LIST_FILTER_CONTROL_CLASS =
  'w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:outline focus:outline-2 focus:outline-offset-1 focus:outline-accent-primary';

export const LIST_PAGE_SHELL_CLASS = 'mx-auto max-w-6xl p-8';
