import {
  CargaInforme,
  EnvelopeInforme,
  EstadoZona,
  MetaInforme,
  extraerResultados,
} from './informes-compuestos.types';

/**
 * Vacío y cero no son lo mismo. Una cohorte con churn 0 es dato.
 * `sin_actividad_conocida = 1` también es dato, no «0 días».
 * Las notas de meta se conservan en vacío.
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
  const meta: MetaInforme = env.meta ?? {};
  return {
    estado: estadoDeZona({ loading: false, error: null, data, metricaAusente }),
    error: null,
    data,
    meta,
  };
}
