import {
  LEYENDA_SIN_BASE,
  LEYENDA_SIN_CUPO,
  LEYENDA_SIN_TARIFA,
  TONO_CUPO,
  claseCodigo,
  cuentaComoConsumo,
  estadoCupo,
  formatearIp,
  importeExcedente,
  opcional,
  porcentajeCupo,
  textoImporte,
  textoPorcentaje,
  variacionPorcentual,
} from './monitoreo.types';
import type { ConsumoPartner } from './monitoreo.types';

function consumo(parcial: Partial<ConsumoPartner> = {}): ConsumoPartner {
  return {
    idpartner: 1,
    entorno: 'Producción',
    periodo: { desde: 0, hasta: 0 },
    llamadas: 100,
    errores: 0,
    latencia_media_ms: 90,
    cupo_mensual: 1000,
    porcentaje_consumido: 10,
    llamadas_excedentes: 0,
    excedente_estimado: 0,
    datos_hasta: 0,
    ...parcial,
  };
}

describe('monitoreo.types — centinelas', () => {
  it('null y 0 NO colapsan al mismo valor', () => {
    // Arrange / Act
    const ausente = opcional(null, LEYENDA_SIN_CUPO);
    const cero = opcional(0, LEYENDA_SIN_CUPO);

    // Assert — un 0 % dice «no consumiste»; null dice «no hay con qué comparar»
    expect(ausente.valor).toBeNull();
    expect(cero.valor).toBe(0);
    expect(ausente.leyenda).toBe(LEYENDA_SIN_CUPO);
    expect(cero.leyenda).toBe('');
  });

  it('un porcentaje ausente se rinde como «No aplica», nunca como 0 %', () => {
    // Act
    const texto = textoPorcentaje(porcentajeCupo(consumo({ porcentaje_consumido: null })));

    // Assert
    expect(texto).toBe(LEYENDA_SIN_CUPO);
    expect(texto).not.toContain('0');
  });

  it('un porcentaje de 0 sí se rinde como 0 %', () => {
    // Act / Assert
    expect(textoPorcentaje(porcentajeCupo(consumo({ porcentaje_consumido: 0 })))).toBe('0.0 %');
  });

  it('un excedente sin tarifa NO se rinde como 0,00', () => {
    // Act
    const texto = textoImporte(importeExcedente(consumo({ excedente_estimado: null })));

    // Assert
    expect(texto).toBe(LEYENDA_SIN_TARIFA);
  });
});

describe('monitoreo.types — estado del cupo', () => {
  it('clasifica los cuatro estados', () => {
    expect(estadoCupo(consumo({ porcentaje_consumido: null }))).toBe('sin-cupo');
    expect(estadoCupo(consumo({ porcentaje_consumido: 42 }))).toBe('holgado');
    expect(estadoCupo(consumo({ porcentaje_consumido: 85 }))).toBe('cerca');
    expect(estadoCupo(consumo({ porcentaje_consumido: 150 }))).toBe('excedido');
  });

  it('🎯 el tono NO es de severidad en ningún estado, ni al 150 %', () => {
    // Superar el cupo no interrumpe el servicio (RN-APM-002). Un rojo aquí haría
    // que el partner apagase una integración que funciona.
    expect(TONO_CUPO).not.toContain('critical');
    expect(TONO_CUPO).not.toContain('warning');
    expect(TONO_CUPO).not.toContain('urgent');
    expect(TONO_CUPO).toContain('info');
  });
});

describe('monitoreo.types — clasificación del código HTTP', () => {
  it('clasifica cada rango', () => {
    expect(claseCodigo(200)).toBe('exito');
    expect(claseCodigo(403)).toBe('cliente');
    expect(claseCodigo(500)).toBe('plataforma');
  });

  it('🎯 el 429 es su propia clase, no un 4xx más', () => {
    // Agruparlo con los 4xx haría que el partner revisara un cliente correcto:
    // no es una petición mal formada, es el ritmo siendo regulado.
    expect(claseCodigo(429)).toBe('ritmo');
    expect(claseCodigo(429)).not.toBe('cliente');
  });

  it('el 429 no cuenta como consumo facturable', () => {
    expect(cuentaComoConsumo(429)).toBeFalse();
    expect(cuentaComoConsumo(403)).toBeTrue();
    expect(cuentaComoConsumo(200)).toBeTrue();
  });
});

describe('monitoreo.types — formateo', () => {
  it('convierte la IP entera del esquema a notación con puntos', () => {
    // 3232235777 = 192.168.1.1 — sin convertir sería un número sin sentido.
    expect(formatearIp(3232235777)).toBe('192.168.1.1');
  });

  it('🎯 decodifica la IP que Pinot devuelve NEGATIVA por desbordamiento', () => {
    // El INT de Pinot es de 32 bits con signo: toda IP desde 128.0.0.0 supera
    // 2³¹−1 y vuelve envuelta. 192.168.1.1 llega como -1062731519. Rechazar los
    // negativos dejaba sin IP a casi todas las llamadas reales.
    expect(formatearIp(-1062731519)).toBe('192.168.1.1');
    expect(formatearIp(-1)).toBe('255.255.255.255');
  });

  it('las IP bajas siguen funcionando', () => {
    // 10.0.0.1 cabe en el rango positivo: no debe romperse al arreglar el otro.
    expect(formatearIp(167772161)).toBe('10.0.0.1');
  });

  it('la variación contra un período de 0 llamadas no es Infinity', () => {
    // Act
    const v = variacionPorcentual(500, 0);

    // Assert
    expect(v.valor).toBeNull();
    expect(v.leyenda).toBe(LEYENDA_SIN_BASE);
  });

  it('calcula la variación cuando hay base', () => {
    expect(variacionPorcentual(150, 100).valor).toBe(50);
  });
});
