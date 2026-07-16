import { ChangeDetectionStrategy, Component, Input } from '@angular/core';

/**
 * Subconjunto de íconos Tabler (outline, 24x24) usados hoy por el sidebar.
 * Los paths vienen de node_modules/@tabler/icons/icons/outline/*.svg — se
 * inlinean aquí (en vez de cargar el .svg en runtime) para no depender de
 * red ni de configuración extra de build para assets SVG.
 */
export type TablerIconName =
  | 'dashboard'
  | 'car-crash'
  | 'list'
  | 'radio'
  | 'map'
  | 'history'
  | 'camera'
  | 'settings'
  | 'logout'
  | 'menu'
  | 'search'
  | 'bell'
  | 'map-pin'
  | 'eye'
  | 'alert-octagon'
  | 'alert-triangle'
  | 'alert-circle'
  | 'circle-check'
  | 'info-circle'
  | 'refresh'
  | 'arrow-left'
  | 'upload'
  | 'x'
  | 'chevron-left'
  | 'chevron-right'
  | 'sun'
  | 'moon'
  | 'focus-2';

const ICON_PATHS: Record<TablerIconName, string[]> = {
  dashboard: [
    'M10 13a2 2 0 1 0 4 0a2 2 0 1 0 -4 0',
    'M13.45 11.55l2.05 -2.05',
    'M6.4 20a9 9 0 1 1 11.2 0l-11.2 0',
  ],
  'car-crash': [
    'M8 17a2 2 0 1 0 4 0a2 2 0 1 0 -4 0',
    'M7 6l4 5h1a2 2 0 0 1 2 2v4h-2m-4 0h-5m0 -6h8m-6 0v-5m2 0h-4',
    'M14 8v-2',
    'M19 12h2',
    'M17.5 15.5l1.5 1.5',
    'M17.5 8.5l1.5 -1.5',
  ],
  list: [
    'M9 6l11 0',
    'M9 12l11 0',
    'M9 18l11 0',
    'M5 6l0 .01',
    'M5 12l0 .01',
    'M5 18l0 .01',
  ],
  radio: [
    'M14 3l-9.371 3.749a1 1 0 0 0 -.629 .928v11.323a1 1 0 0 0 1 1h14a1 1 0 0 0 1 -1v-11a1 1 0 0 0 -1 -1h-14.5',
    'M4 12h16',
    'M7 12v-2',
    'M17 16v.01',
    'M13 16v.01',
  ],
  map: ['M3 7l6 -3l6 3l6 -3v13l-6 3l-6 -3l-6 3v-13', 'M9 4v13', 'M15 7v13'],
  history: ['M12 8l0 4l2 2', 'M3.05 11a9 9 0 1 1 .5 4m-.5 5v-5h5'],
  camera: [
    'M5 7h1a2 2 0 0 0 2 -2a1 1 0 0 1 1 -1h6a1 1 0 0 1 1 1a2 2 0 0 0 2 2h1a2 2 0 0 1 2 2v9a2 2 0 0 1 -2 2h-14a2 2 0 0 1 -2 -2v-9a2 2 0 0 1 2 -2',
    'M9 13a3 3 0 1 0 6 0a3 3 0 0 0 -6 0',
  ],
  settings: [
    'M10.325 4.317c.426 -1.756 2.924 -1.756 3.35 0a1.724 1.724 0 0 0 2.573 1.066c1.543 -.94 3.31 .826 2.37 2.37a1.724 1.724 0 0 0 1.065 2.572c1.756 .426 1.756 2.924 0 3.35a1.724 1.724 0 0 0 -1.066 2.573c.94 1.543 -.826 3.31 -2.37 2.37a1.724 1.724 0 0 0 -2.572 1.065c-.426 1.756 -2.924 1.756 -3.35 0a1.724 1.724 0 0 0 -2.573 -1.066c-1.543 .94 -3.31 -.826 -2.37 -2.37a1.724 1.724 0 0 0 -1.065 -2.572c-1.756 -.426 -1.756 -2.924 0 -3.35a1.724 1.724 0 0 0 1.066 -2.573c-.94 -1.543 .826 -3.31 2.37 -2.37c1 .608 2.296 .07 2.572 -1.065',
    'M9 12a3 3 0 1 0 6 0a3 3 0 0 0 -6 0',
  ],
  logout: [
    'M14 8v-2a2 2 0 0 0 -2 -2h-7a2 2 0 0 0 -2 2v12a2 2 0 0 0 2 2h7a2 2 0 0 0 2 -2v-2',
    'M9 12h12l-3 -3',
    'M18 15l3 -3',
  ],
  menu: ['M4 6l16 0', 'M4 12l16 0', 'M4 18l16 0'],
  search: ['M3 10a7 7 0 1 0 14 0a7 7 0 1 0 -14 0', 'M21 21l-6 -6'],
  bell: [
    'M10 5a2 2 0 1 1 4 0a7 7 0 0 1 4 6v3a4 4 0 0 0 2 3h-16a4 4 0 0 0 2 -3v-3a7 7 0 0 1 4 -6',
    'M9 17v1a3 3 0 0 0 6 0v-1',
  ],
  'map-pin': [
    'M9 11a3 3 0 1 0 6 0a3 3 0 0 0 -6 0',
    'M17.657 16.657l-4.243 4.243a2 2 0 0 1 -2.827 0l-4.244 -4.243a8 8 0 1 1 11.314 0',
  ],
  eye: [
    'M10 12a2 2 0 1 0 4 0a2 2 0 0 0 -4 0',
    'M21 12c-2.4 4 -5.4 6 -9 6c-3.6 0 -6.6 -2 -9 -6c2.4 -4 5.4 -6 9 -6c3.6 0 6.6 2 9 6',
  ],
  'alert-octagon': [
    'M12.802 2.165l5.575 2.389c.48 .206 .863 .589 1.07 1.07l2.388 5.574c.22 .512 .22 1.092 0 1.604l-2.389 5.575c-.206 .48 -.589 .863 -1.07 1.07l-5.574 2.388c-.512 .22 -1.092 .22 -1.604 0l-5.575 -2.389a2.036 2.036 0 0 1 -1.07 -1.07l-2.388 -5.574a2.036 2.036 0 0 1 0 -1.604l2.389 -5.575c.206 -.48 .589 -.863 1.07 -1.07l5.574 -2.388a2.036 2.036 0 0 1 1.604 0',
    'M12 8v4',
    'M12 16h.01',
  ],
  'alert-triangle': [
    'M12 9v4',
    'M10.363 3.591l-8.106 13.534a1.914 1.914 0 0 0 1.636 2.871h16.214a1.914 1.914 0 0 0 1.636 -2.87l-8.106 -13.536a1.914 1.914 0 0 0 -3.274 0',
    'M12 16h.01',
  ],
  'alert-circle': ['M3 12a9 9 0 1 0 18 0a9 9 0 0 0 -18 0', 'M12 8v4', 'M12 16h.01'],
  'circle-check': ['M3 12a9 9 0 1 0 18 0a9 9 0 1 0 -18 0', 'M9 12l2 2l4 -4'],
  'info-circle': ['M3 12a9 9 0 1 0 18 0a9 9 0 0 0 -18 0', 'M12 9h.01', 'M11 12h1v4h1'],
  refresh: ['M20 11a8.1 8.1 0 0 0 -15.5 -2m-.5 -4v4h4', 'M4 13a8.1 8.1 0 0 0 15.5 2m.5 4v-4h-4'],
  'arrow-left': ['M5 12l14 0', 'M5 12l6 6', 'M5 12l6 -6'],
  upload: ['M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2 -2v-2', 'M7 9l5 -5l5 5', 'M12 4l0 12'],
  x: ['M18 6l-12 12', 'M6 6l12 12'],
  'chevron-left': ['M15 6l-6 6l6 6'],
  'chevron-right': ['M9 6l6 6l-6 6'],
  sun: [
    'M12 12m-4 0a4 4 0 1 0 8 0a4 4 0 1 0 -8 0',
    'M3 12h1m8 -9v1m8 8h1m-9 8v1',
    'M5.6 5.6l.7 .7m12.1 -.7l-.7 .7m0 11.4l.7 .7m-12.1 -.7l-.7 .7',
  ],
  moon: ['M12 3c.132 0 .263 0 .393 0a7.5 7.5 0 0 0 7.92 12.446a9 9 0 1 1 -8.313 -12.454z'],
  'focus-2': [
    'M4 8v-2a2 2 0 0 1 2 -2h2',
    'M4 16v2a2 2 0 0 0 2 2h2',
    'M16 4h2a2 2 0 0 1 2 2v2',
    'M16 20h2a2 2 0 0 0 2 -2v-2',
    'M12 9a3 3 0 1 0 0 6a3 3 0 0 0 0 -6',
  ],
};

/** Paths crudos de un ícono — para reutilizar el mismo lenguaje visual fuera de Angular (ej. marcadores de Leaflet). */
export function tablerIconPaths(name: TablerIconName): string[] {
  return ICON_PATHS[name] ?? [];
}

@Component({
  selector: 'app-tabler-icon',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <svg
      [attr.width]="size"
      [attr.height]="size"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="2"
      stroke-linecap="round"
      stroke-linejoin="round"
      aria-hidden="true"
    >
      @for (path of paths; track path) {
        <path [attr.d]="path" />
      }
    </svg>
  `,
  styles: [
    `
      :host {
        display: inline-flex;
        line-height: 0;
      }
    `,
  ],
})
export class TablerIconComponent {
  @Input({ required: true }) name!: TablerIconName;
  @Input() size = 24;

  get paths(): string[] {
    return ICON_PATHS[this.name] ?? [];
  }
}
