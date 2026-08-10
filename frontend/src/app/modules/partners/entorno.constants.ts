import type { TablerIconName } from '../../shared/ui/icon/tabler-icon.component';
import type { Entorno } from './services/models/partner.types';

/**
 * Presentación de los entornos (RN-PON-008, FR-UI-016).
 *
 * Pruebas y producción COEXISTEN, y confundirlos al rotar o revocar sería un
 * error caro. Por eso la distinción no puede depender del color: cada entorno
 * lleva ícono y etiqueta propios, y las credenciales se agrupan bajo
 * encabezados separados. Si al desactivar el color dejan de distinguirse, el
 * diseño está mal (SC-006).
 */
export interface PresentacionEntorno {
  readonly etiqueta: string;
  readonly icono: TablerIconName;
  readonly tono: string;
  /** Nota de vigencia mostrada junto al encabezado del grupo. */
  readonly notaVigencia: string;
}

export const ENTORNO_SANDBOX: Entorno = 'Sandbox';
export const ENTORNO_PRODUCCION: Entorno = 'Producción';

export const PRESENTACION_ENTORNO: Record<Entorno, PresentacionEntorno> = {
  Sandbox: {
    etiqueta: 'Pruebas',
    icono: 'flask',
    tono: 'bg-sky-50 text-sky-800 dark:bg-sky-950 dark:text-sky-200',
    notaVigencia: 'Vigencia limitada; te avisamos antes de que venza.',
  },
  Producción: {
    etiqueta: 'Producción',
    icono: 'bolt',
    tono: 'bg-lime-50 text-lime-800 dark:bg-lime-950 dark:text-lime-200',
    notaVigencia: 'Las credenciales de producción no expiran.',
  },
};

/** Orden de los grupos: pruebas primero, que es por donde se empieza. */
export const ENTORNOS: readonly Entorno[] = [ENTORNO_SANDBOX, ENTORNO_PRODUCCION] as const;

export function presentacionEntorno(entorno: Entorno): PresentacionEntorno {
  return PRESENTACION_ENTORNO[entorno] ?? PRESENTACION_ENTORNO.Sandbox;
}
