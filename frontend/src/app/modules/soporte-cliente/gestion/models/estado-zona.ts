import {
  CargaInforme,
  EnvelopeInforme,
  EstadoZona,
  MetaInforme,
  extraerDeclaraciones,
  extraerResultados,
} from './informes-compuestos.types';

/**
 * Vacío y cero no son lo mismo: un período sin filas no tiene indicador.
 * Una métrica `null` es «sin dato», nunca un 0 que dispare una alarma BSC.
 * Una fila de serie con `tickets = 0` o `creados = 0` **sí** es dato (D15).
 *
 * `meta` y `declaraciones` se conservan también en vacío: `acotado_a` tiene
 * que verse aunque no haya filas.
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

export function cargaDeEnvelope(
  env: EnvelopeInforme | { data?: unknown; meta?: MetaInforme },
  metricaAusente = false,
): CargaInforme {
  const data = extraerResultados((env as EnvelopeInforme).data ?? null);
  const declaraciones = extraerDeclaraciones((env as EnvelopeInforme).data ?? null);
  const meta: MetaInforme = env.meta ?? {};
  return {
    estado: estadoDeZona({ loading: false, error: null, data, metricaAusente }),
    error: null,
    data,
    declaraciones,
    meta,
  };
}
