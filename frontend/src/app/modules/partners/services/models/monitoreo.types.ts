/**
 * Tipos y traducciones del monitoreo de API (#08).
 *
 * Aquí vive **toda** la interpretación de lo que el backend devuelve como
 * ausencia de dato. Si esa traducción se repartiera por las plantillas, el
 * primero que se olvidara imprimiría un `0` donde el backend dijo `null` — y
 * `0 %` afirma algo falso: que el partner no consumió nada.
 */

// --- Respuestas del backend ------------------------------------------------

export interface ConsumoPartner {
  idpartner: number;
  entorno: string;
  periodo: { desde: number; hasta: number };
  llamadas: number;
  errores: number;
  latencia_media_ms: number;
  cupo_mensual: number;
  /** `null` cuando el cupo vale el centinela: no hay contra qué comparar. */
  porcentaje_consumido: number | null;
  llamadas_excedentes: number;
  /** `null` cuando el plan no tiene tarifa configurada. */
  excedente_estimado: number | null;
  /** Último instante consultable: la ingesta va 5-15 s por detrás. */
  datos_hasta: number;
}

export interface LogLlamada {
  idlogllamadaapi: number;
  idpartner: number;
  endpoint: string;
  metodohttp: string;
  codigohttp: number;
  latenciams: number;
  iporigen: number;
  fechallamada: number;
}

export interface ReporteMensual {
  idpartner: number;
  entorno: string;
  periodo: string;
  llamadas: number;
  errores: number;
  latencia_media_ms: number;
}

export type TipoExcepcion = 'reintentos_agotados' | 'no_tarificable';

export interface ExcepcionFacturacion {
  tipo: TipoExcepcion;
  idpartner: number;
  nombrepartner: string;
  periodo: string;
  /** Solo en `reintentos_agotados`: en el otro caso **no hay factura**. */
  id_factura: string | null;
  importe: number | null;
  intentos: number | null;
  ultimo_resultado: string;
}

// --- Centinelas: la traducción única ---------------------------------------

/** `Dim_Partner.limitellamadasmes` sin cupo asignado (0 sería válido). */
export const SIN_CUPO = -1;

export interface ValorOpcional {
  /** `null` significa «no hay dato», nunca «vale cero». */
  valor: number | null;
  /** Por qué no hay dato. Vacío cuando sí lo hay. */
  leyenda: string;
}

export const LEYENDA_SIN_CUPO = 'No aplica — sin cupo configurado';
export const LEYENDA_SIN_TARIFA = 'No aplica — sin tarifa configurada';
export const LEYENDA_SIN_BASE = 'Sin base de comparación';

/**
 * Envuelve un número que puede faltar.
 *
 * **`null` y `0` no colapsan jamás.** El backend devuelve `null` a propósito
 * (su propio comentario dice que «inventar un 0 % sería peor que decir *no
 * aplica*»), y esta capa lo respeta en vez de rellenarlo.
 */
export function opcional(valor: number | null | undefined, leyenda: string): ValorOpcional {
  return valor === null || valor === undefined
    ? { valor: null, leyenda }
    : { valor, leyenda: '' };
}

/** Porcentaje de cupo consumido, o «no aplica» si no hay cupo contra el que medir. */
export function porcentajeCupo(consumo: ConsumoPartner): ValorOpcional {
  return opcional(consumo.porcentaje_consumido, LEYENDA_SIN_CUPO);
}

/** Importe del excedente, o «no aplica» si el plan no tiene tarifa. */
export function importeExcedente(consumo: ConsumoPartner): ValorOpcional {
  return opcional(consumo.excedente_estimado, LEYENDA_SIN_TARIFA);
}

/** Texto listo para pintar: el número formateado, o su leyenda. */
export function textoPorcentaje(v: ValorOpcional): string {
  return v.valor === null ? v.leyenda : `${v.valor.toFixed(1)} %`;
}

export function textoImporte(v: ValorOpcional): string {
  return v.valor === null
    ? v.leyenda
    : v.valor.toLocaleString('es-EC', { style: 'currency', currency: 'USD' });
}

// --- Estado del cupo -------------------------------------------------------

export type EstadoCupo = 'sin-cupo' | 'holgado' | 'cerca' | 'excedido';

/**
 * En qué punto de su cupo está el partner.
 *
 * **Ninguno de los cuatro estados es de alarma**, ni siquiera `excedido`.
 * Superar el cupo NO interrumpe el servicio (RN-APM-002): es un coste previsto,
 * y el SRS documentó la regla «para que nadie la corrija asumiendo que debería
 * bloquear». El token visual lo fija `TONO_CUPO`, que es el mismo para los
 * cuatro a propósito.
 */
export function estadoCupo(consumo: ConsumoPartner): EstadoCupo {
  const pct = consumo.porcentaje_consumido;
  if (pct === null) {
    return 'sin-cupo';
  }
  if (pct >= 100) {
    return 'excedido';
  }
  return pct >= 80 ? 'cerca' : 'holgado';
}

/**
 * El MISMO tono para los cuatro estados. No es un descuido.
 *
 * Un rojo —o incluso un ámbar— en `excedido` comunicaría una interrupción que
 * no ocurre, y el partner apagaría por su cuenta una integración que funciona.
 * Ver el tie-breaker de `plan.md` y la lista de prohibiciones de
 * `panel-consumo-partner.ui-contract.md`.
 */
export const TONO_CUPO = 'bg-alert-info-bg text-alert-info';

export const COPY_CUPO: Record<EstadoCupo, string> = {
  'sin-cupo': 'Sin cupo configurado',
  holgado: '',
  cerca: 'Te acercas a tu cupo mensual',
  excedido: 'Tu servicio no se interrumpe: el excedente se factura al cierre del período',
};

/**
 * El mismo copy para un partner **suspendido**.
 *
 * «Tu servicio no se interrumpe» es cierto **del cupo** —superarlo no corta
 * nada (RN-APM-002)— pero junto al banner de suspensión se lee como una
 * contradicción: el acceso sí está cortado, por otro motivo. Se detectó
 * mirando la pantalla real con el partner suspendido; ningún test lo veía
 * porque los dos bloques se probaban por separado.
 *
 * La regla de fondo no cambia: el excedente **sigue siendo un coste, no una
 * sanción**, y lo que se retira es la frase que ya no es cierta en ese
 * contexto, no el encuadre de facturación.
 */
export const COPY_CUPO_SUSPENDIDO: Record<EstadoCupo, string> = {
  ...COPY_CUPO,
  excedido: 'El excedente de este período se factura igualmente al cierre',
};

// --- Clasificación del código HTTP -----------------------------------------

export type ClaseCodigo = 'exito' | 'ritmo' | 'cliente' | 'plataforma';

/**
 * Qué clase de cosa es un código HTTP **desde el punto de vista del partner**.
 *
 * El `429` se separa del resto de 4xx a propósito: no es una petición mal
 * formada, es el ritmo siendo regulado. Agruparlos haría que el partner
 * revisara un cliente que está correcto. Además el 429 **no cuenta como
 * consumo facturable** (§ 15 D2 del backend).
 */
export function claseCodigo(codigo: number): ClaseCodigo {
  if (codigo === 429) {
    return 'ritmo';
  }
  if (codigo >= 500) {
    return 'plataforma';
  }
  if (codigo >= 400) {
    return 'cliente';
  }
  return 'exito';
}

export const ETIQUETA_CODIGO: Record<ClaseCodigo, string> = {
  exito: 'Correcta',
  ritmo: 'Límite de ritmo',
  cliente: 'Revisar la petición',
  plataforma: 'Error de plataforma',
};

/**
 * Tono del badge por clase.
 *
 * `alert-critical` solo para `plataforma`, que **sí** es un fallo nuestro. El
 * `429` va en tono informativo porque no es culpa de nadie.
 */
export const TONO_CODIGO: Record<ClaseCodigo, string> = {
  exito: 'bg-alert-success-bg text-alert-success',
  ritmo: 'bg-alert-info-bg text-alert-info',
  cliente: 'bg-alert-warning-bg text-alert-warning',
  plataforma: 'bg-alert-critical-bg text-alert-critical',
};

/** El 429 no se atendió, así que no se factura. Se dice en la fila. */
export function cuentaComoConsumo(codigo: number): boolean {
  return claseCodigo(codigo) !== 'ritmo';
}

// --- Formateo --------------------------------------------------------------

/**
 * `Fact_LogLlamadaAPI.iporigen` es un **INT** en el esquema de Pinot.
 * Sin convertir, la consola mostraría un número de nueve cifras sin sentido.
 *
 * Ojo con el signo: el INT de Pinot es de **32 bits con signo**, y cualquier
 * IP a partir de `128.0.0.0` supera 2³¹−1, así que se almacena **negativa**.
 * `192.168.1.1` (3 232 235 777) vuelve como `-1062731519`. Rechazar los
 * negativos —como hacía la primera versión— dejaba sin IP a la mayoría de las
 * llamadas reales, incluidas todas las de red privada. Se detectó mirando la
 * consola en la app real, donde la columna mostraba «—».
 *
 * Los desplazamientos sin signo (`>>>`) reconstruyen los cuatro octetos
 * correctamente tanto si el valor llegó positivo como si llegó envuelto.
 */
export function formatearIp(entero: number): string {
  if (!Number.isFinite(entero)) {
    return '—';
  }
  return [24, 16, 8, 0].map((b) => (entero >>> b) & 255).join('.');
}

export function formatearInstante(ms: number): string {
  return new Date(ms).toLocaleString('es-EC');
}

/** Variación entre dos períodos; `null` si no hay base contra la que comparar. */
export function variacionPorcentual(actual: number, comparado: number): ValorOpcional {
  if (comparado <= 0) {
    // Dividir por cero daría Infinity, y un «+100 %» sería inventado.
    return { valor: null, leyenda: LEYENDA_SIN_BASE };
  }
  return { valor: ((actual - comparado) / comparado) * 100, leyenda: '' };
}
