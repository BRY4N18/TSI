import {
  NUNCA_EXPIRA,
  SIN_CUPO,
  SIN_PLAN,
  TEXTO_NO_EXPIRA,
  TEXTO_SIN_CUPO,
  TEXTO_SIN_PLAN,
  TEXTO_SIN_RETIRO,
  diasParaVencer,
  estaSuspendido,
  estaVencida,
  formatearCupo,
  formatearFechaRetiro,
  formatearPlan,
  formatearVigencia,
  noExpiraNunca,
  tieneSpecPublicada,
} from './centinelas';

/**
 * Los centinelas de Pinot cruzan hasta la UI. Cada test de aquí corresponde a
 * un defecto visible concreto que se produciría al renderizarlos crudos.
 */
describe('centinelas', () => {
  describe('formatearPlan', () => {
    it('traduce el centinela de "sin plan" en vez de mostrar una cadena vacía', () => {
      expect(formatearPlan(SIN_PLAN)).toBe(TEXTO_SIN_PLAN);
    });

    it('deja pasar un plan real sin tocarlo', () => {
      expect(formatearPlan('Profesional')).toBe('Profesional');
    });
  });

  describe('formatearCupo', () => {
    it('traduce -1 en vez de mostrar un cupo negativo', () => {
      expect(formatearCupo(SIN_CUPO)).toBe(TEXTO_SIN_CUPO);
    });

    it('respeta el cupo 0, que es un valor válido y distinto de "sin asignar"', () => {
      expect(formatearCupo(0)).not.toBe(TEXTO_SIN_CUPO);
    });

    it('formatea un cupo real con separador de miles', () => {
      expect(formatearCupo(10000)).toContain('10');
    });
  });

  describe('vigencia', () => {
    it('reconoce el centinela de producción', () => {
      expect(noExpiraNunca(NUNCA_EXPIRA)).toBeTrue();
    });

    it('muestra "No expira" en vez de una fecha del año 9999', () => {
      expect(formatearVigencia(NUNCA_EXPIRA)).toBe(TEXTO_NO_EXPIRA);
      expect(formatearVigencia(NUNCA_EXPIRA)).not.toContain('9999');
    });

    it('formatea como fecha una vigencia real', () => {
      const dentroDeUnMes = Date.now() + 30 * 86_400_000;
      expect(formatearVigencia(dentroDeUnMes)).not.toBe(TEXTO_NO_EXPIRA);
    });
  });

  describe('estaVencida — cálculo perezoso (fail-safe)', () => {
    it('considera vencida una credencial pasada aunque el job no haya corrido', () => {
      expect(estaVencida({ fecha_expiracion: 1000 }, 2000)).toBeTrue();
    });

    it('NUNCA considera vencida una credencial de producción', () => {
      expect(estaVencida({ fecha_expiracion: NUNCA_EXPIRA }, Date.now())).toBeFalse();
    });

    it('no considera vencida una credencial todavía vigente', () => {
      expect(estaVencida({ fecha_expiracion: 5000 }, 2000)).toBeFalse();
    });
  });

  describe('diasParaVencer', () => {
    it('devuelve null para producción, no un número absurdo de días', () => {
      expect(diasParaVencer(NUNCA_EXPIRA)).toBeNull();
    });

    it('cuenta los días restantes de una credencial de pruebas', () => {
      const ahora = 1_000_000_000_000;
      expect(diasParaVencer(ahora + 10 * 86_400_000, ahora)).toBe(10);
    });
  });

  describe('formatearFechaRetiro', () => {
    it('traduce el centinela 0 en vez de mostrar 01/01/1970', () => {
      expect(formatearFechaRetiro(0)).toBe(TEXTO_SIN_RETIRO);
      expect(formatearFechaRetiro(0)).not.toContain('1970');
    });

    it('formatea una fecha de retiro real', () => {
      expect(formatearFechaRetiro(1_800_000_000_000)).not.toBe(TEXTO_SIN_RETIRO);
    });
  });

  describe('tieneSpecPublicada', () => {
    it('evita renderizar un enlace roto cuando no hay documento', () => {
      expect(tieneSpecPublicada('')).toBeFalse();
    });

    it('reconoce una URL publicada', () => {
      expect(tieneSpecPublicada('https://docs.tsi.local/despacho/v1')).toBeTrue();
    });
  });

  describe('estaSuspendido', () => {
    it('detecta al partner suspendido para no ofrecerle acciones de habilitación', () => {
      expect(estaSuspendido({ activo: false })).toBeTrue();
      expect(estaSuspendido({ activo: true })).toBeFalse();
    });
  });
});
