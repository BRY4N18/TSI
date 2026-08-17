import { EstadoZona } from './informes-compuestos.types';

/**
 * Vacío y cero no son lo mismo: un período sin filas no tiene indicador.
 * Una métrica `null` es «sin dato», nunca un 0 que dispare una alarma.
 */
export function estadoDeZona(args: {
  loading: boolean;
  error: string | null;
  data: unknown[] | null;
  metricaAusente?: boolean;
}): EstadoZona {
  if (args.loading || args.data === null) {
    return 'carga';
  }
  if (args.error) {
    return 'error';
  }
  if (args.data.length === 0) {
    return 'vacio';
  }
  if (args.metricaAusente) {
    return 'sin_dato';
  }
  return 'dato';
}
