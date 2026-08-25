/**
 * Clases Tailwind canónicas para tablas operativas (design-system § tablas /
 * patrón lista-accidentes). Reutilizar en módulos fuera de Accidentes.
 */
export const LIST_TABLE_CLASS =
  'hidden w-full border-collapse overflow-hidden rounded-md border border-border-default md:table';

export const LIST_TABLE_TH_CLASS =
  'tsi-display border-b-2 border-accent-primary px-4 py-3 text-left text-xs uppercase tracking-widest text-text-primary';

export const LIST_TABLE_TH_RIGHT_CLASS =
  'tsi-display border-b-2 border-accent-primary px-4 py-3 text-right text-xs uppercase tracking-widest text-text-primary';

export const LIST_TABLE_TD_CLASS = 'px-4 py-3 text-sm text-text-secondary';

export const LIST_TABLE_TD_PRIMARY_CLASS = 'px-4 py-3 text-sm font-semibold text-text-primary';

export const LIST_ROW_CLASS = 'border-b border-border-default bg-bg-page even:bg-bg-surface';

export const LIST_ACTION_ICON_BTN_CLASS =
  'inline-flex h-11 w-11 items-center justify-center rounded-md text-text-secondary hover:bg-bg-page hover:text-text-primary';

export const LIST_MOBILE_CARD_CLASS =
  'rounded-md border border-border-default bg-bg-surface p-4';

/**
 * Habia una sola constante para los controles de filtro, aplicada tanto a
 * `<input>` como a `<select>`. Las clases canonicas de §5 no son
 * intercambiables — `.tsi-select` aporta `appearance: none` y el chevron por
 * tema — asi que se separan. `LIST_FILTER_CONTROL_CLASS` se mantiene como
 * alias del input para no romper importaciones existentes.
 */
export const LIST_FILTER_INPUT_CLASS = 'tsi-input w-full';

export const LIST_FILTER_SELECT_CLASS = 'tsi-select w-full min-w-0';

export const LIST_FILTER_CONTROL_CLASS = LIST_FILTER_INPUT_CLASS;

export const LIST_PAGE_SHELL_CLASS = 'mx-auto max-w-6xl p-8';
