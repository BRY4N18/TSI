import {
  CargaInforme,
  EnvelopeInforme,
  EstadoZona,
  MetaInforme,
} from './informes-compuestos.types';

/**
 * Vacío y cero no son lo mismo: un período sin filas no tiene indicador.
 * Una métrica `null` es «sin dato», nunca un 0 que dispare una alarma.
 *
 * `meta` se conserva también en vacío: `mes` y `nota_periodo` tienen que verse
 * cuando MRR/NRR resolvieron el mes y no hay filas.
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
  const data = Array.isArray(env.data) ? (env.data as Record<string, unknown>[]) : [];
  const meta: MetaInforme = env.meta ?? {};
  return {
    estado: estadoDeZona({ loading: false, error: null, data, metricaAusente }),
    error: null,
    data,
    meta,
  };
}
