import {
  CargaInforme,
  EnvelopeInforme,
  EstadoZona,
  MetaInforme,
  extraerFilas,
} from './informes-oe4.types';

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
  const data = extraerFilas((env as EnvelopeInforme).data ?? null);
  const meta: MetaInforme = env.meta ?? {};
  return {
    estado: estadoDeZona({ loading: false, error: null, data, metricaAusente }),
    error: null,
    data,
    meta,
  };
}
