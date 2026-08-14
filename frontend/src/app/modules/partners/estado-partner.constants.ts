import type { TablerIconName } from '../../shared/ui/icon/tabler-icon.component';
import type { EstadoPartner } from './services/models/partner.types';

/**
 * Mapa único de presentación del estado derivado. Vive aquí para que ningún
 * componente decida por su cuenta cómo se ve un estado.
 *
 * El estado lo calcula el backend (§ 9) a partir de las credenciales y la
 * bitácora: la UI lo presenta y NUNCA lo edita (FR-UI-014).
 *
 * `siguiente` no es decoración: un estado sin siguiente paso deja al partner
 * sin saber qué hacer (FR-UI-015).
 */
export interface PresentacionEstado {
  readonly icono: TablerIconName;
  /** Clases Tailwind del chip, resueltas por token semántico en ambos temas. */
  readonly tono: string;
  /** Qué comunica el estado a un gestor. */
  readonly descripcion: string;
  /** Qué debe hacer el partner a continuación. */
  readonly siguiente: string;
}

const TONO_INFO = 'bg-sky-50 text-sky-800 dark:bg-sky-950 dark:text-sky-200';
const TONO_EXITO = 'bg-lime-50 text-lime-800 dark:bg-lime-950 dark:text-lime-200';
const TONO_ADVERTENCIA = 'bg-amber-50 text-amber-900 dark:bg-amber-950 dark:text-amber-200';
const TONO_CRITICO = 'bg-red-50 text-red-800 dark:bg-red-950 dark:text-red-200';

export const PRESENTACION_ESTADO: Record<EstadoPartner, PresentacionEstado> = {
  Registrado: {
    icono: 'user-plus',
    tono: TONO_INFO,
    descripcion: 'Existe, pero aún no puede operar',
    siguiente: 'Un administrador debe asignarte un plan de acceso.',
  },
  'Plan asignado': {
    icono: 'license',
    tono: TONO_INFO,
    descripcion: 'Ya tiene cupo; puede emitir credenciales de pruebas',
    siguiente: 'Ya puedes emitir tu primera credencial de pruebas.',
  },
  'Pruebas activo': {
    icono: 'flask',
    tono: TONO_EXITO,
    descripcion: 'Integrando en el entorno de pruebas',
    siguiente: 'Cuando tu integración esté lista, solicita el paso a producción.',
  },
  'Pendiente de aprobación': {
    icono: 'clock',
    tono: TONO_ADVERTENCIA,
    descripcion: 'Requiere que un Administrador la resuelva',
    siguiente: 'Tu solicitud está en revisión. Te avisaremos al correo del contacto técnico.',
  },
  'Producción activa': {
    icono: 'circle-check',
    tono: TONO_EXITO,
    descripcion: 'Operando en producción',
    siguiente: 'Tu integración está en producción. Tus credenciales de pruebas siguen activas.',
  },
  Suspendido: {
    icono: 'ban',
    tono: TONO_CRITICO,
    descripcion: 'Bloqueado: toda acción de habilitación será rechazada',
    siguiente: 'Tu acceso está suspendido. Contacta al administrador.',
  },
};

/** Los seis estados, en el orden del ciclo de vida — para filtros de la lista. */
export const ESTADOS_PARTNER: readonly EstadoPartner[] = [
  'Registrado',
  'Plan asignado',
  'Pruebas activo',
  'Pendiente de aprobación',
  'Producción activa',
  'Suspendido',
] as const;

export const ESTADO_SUSPENDIDO: EstadoPartner = 'Suspendido';
export const ESTADO_PENDIENTE_APROBACION: EstadoPartner = 'Pendiente de aprobación';
export const ESTADO_PRUEBAS_ACTIVO: EstadoPartner = 'Pruebas activo';
export const ESTADO_PRODUCCION_ACTIVA: EstadoPartner = 'Producción activa';

export function presentacionDe(estado: EstadoPartner): PresentacionEstado {
  return PRESENTACION_ESTADO[estado] ?? PRESENTACION_ESTADO.Registrado;
}
