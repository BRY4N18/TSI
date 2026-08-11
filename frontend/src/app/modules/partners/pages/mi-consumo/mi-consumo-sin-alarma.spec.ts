import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { ComponentFixture, TestBed } from '@angular/core/testing';

import { MiConsumoPage } from './mi-consumo.page';
import type { ConsumoPartner } from '../../services/models/monitoreo.types';

/**
 * 🎯 El test que impide «arreglar» un bug que no existe.
 *
 * Superar el cupo mensual **NO interrumpe el servicio** (RN-APM-002). El SRS
 * documentó la regla explícitamente *«para que nadie la corrija asumiendo que
 * debería bloquear»*, y el catálogo (RF-O53.2) llegó a decir lo contrario: la
 * divergencia está registrada en el spec del backend.
 *
 * Cualquiera que vea un consumo del 150 % pintado en azul va a pensar que falta
 * un estado de alarma. **No falta.** Un rojo —o un ámbar— comunicaría una
 * interrupción que no ocurre, y el partner apagaría por su cuenta una
 * integración que está funcionando.
 *
 * Si este test se pone en rojo, la respuesta correcta casi nunca es cambiar el
 * test.
 */

const PARTNER = {
  idpartner: 12,
  idcliente: 3,
  nombrepartner: 'Integradora Andina',
  planapi: 'Profesional',
  limitellamadasmes: 10000,
  limitellamadasminuto: 120,
  activo: true,
  estado: 'Producción activa',
  contacto_tecnico_nombre: 'Ana',
  contacto_tecnico_gmail: 'ana@demo.com',
  fecha_suspension: '',
  motivo_suspension: '',
  credenciales: [],
  historial: [],
};

/** Consumo MUY por encima del cupo: 15 000 de 10 000. */
const CONSUMO_AL_150: ConsumoPartner = {
  idpartner: 12,
  entorno: 'Producción',
  periodo: { desde: 1, hasta: 2 },
  llamadas: 15000,
  errores: 4,
  latencia_media_ms: 88,
  cupo_mensual: 10000,
  porcentaje_consumido: 150,
  llamadas_excedentes: 5000,
  excedente_estimado: 25,
  datos_hasta: 1_750_000_000_000,
};

/** Tokens de severidad del design-system. Ninguno vale para un excedente. */
const TOKENS_DE_SEVERIDAD = ['alert-critical', 'alert-urgent', 'alert-warning'];

/**
 * Palabras que afirmarían una interrupción que no ocurre.
 *
 * **«interrump» NO está en la lista, y es deliberado.** La primera versión lo
 * incluía y el test se puso rojo por la frase que precisamente tranquiliza al
 * partner: «tu servicio **no se interrumpe**». Una lista por subcadena no
 * distingue una afirmación de su negación. El caso afirmativo ya lo cubren
 * «cortad» y «bloquead», y la comprobación positiva del último `it` exige que
 * la frase de tranquilidad **sí** esté.
 */
const PALABRAS_PROHIBIDAS = [
  'bloquead',
  'cortad',
  'suspend',
  'límite superado',
  'limite superado',
  'excediste',
];

/** Iconos de severidad del design-system § 5. */
const ICONOS_DE_SEVERIDAD = ['alert-octagon', 'alert-triangle', 'alert-circle'];

describe('MiConsumoPage — el excedente NO es una alarma', () => {
  let fixture: ComponentFixture<MiConsumoPage>;
  let http: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MiConsumoPage],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();

    fixture = TestBed.createComponent(MiConsumoPage);
    http = TestBed.inject(HttpTestingController);

    fixture.detectChanges();
    http.expectOne('/api/v1/partners/me').flush({ data: PARTNER, meta: { pagination: null } });
    http
      .expectOne((r) => r.url === '/api/v1/partners/12/metricas')
      .flush({ data: CONSUMO_AL_150, meta: { pagination: null } });
    http
      .expectOne((r) => r.url === '/api/v1/logs-api')
      .flush({ data: [], meta: { pagination: null } });
    fixture.detectChanges();
  });

  afterEach(() => http.verify());

  function bloqueCupo(): HTMLElement {
    return fixture.nativeElement.querySelector('[data-testid="bloque-cupo"]');
  }

  function bloqueExcedente(): HTMLElement {
    return fixture.nativeElement.querySelector('[data-testid="bloque-excedente"]');
  }

  it('el escenario es realmente el de exceso (si no, el test no probaría nada)', () => {
    // Guarda contra un falso verde: si el fixture cambiara y el consumo dejara
    // de superar el cupo, los asertos de abajo pasarían sin significar nada.
    expect(bloqueCupo().textContent).toContain('150');
    expect(bloqueExcedente()).toBeTruthy();
  });

  it('🎯 el bloque de cupo no usa NINGÚN token de severidad al 150 %', () => {
    // Act
    const clases = bloqueCupo().innerHTML;

    // Assert
    for (const token of TOKENS_DE_SEVERIDAD) {
      expect(clases).not.toContain(
        token,
        `El bloque de cupo usa «${token}» con el consumo al 150 %. Superar el cupo NO ` +
          'interrumpe el servicio (RN-APM-002): pintarlo como alarma haría que el partner ' +
          'apagase una integración que funciona.',
      );
    }
  });

  it('🎯 el bloque de excedente tampoco usa tokens de severidad', () => {
    // Act
    const clases = bloqueExcedente().innerHTML;

    // Assert
    for (const token of TOKENS_DE_SEVERIDAD) {
      expect(clases).not.toContain(token);
    }
  });

  it('🎯 no aparece ninguna palabra que afirme una interrupción', () => {
    // Act
    const texto = (fixture.nativeElement.textContent ?? '').toLowerCase();

    // Assert
    for (const palabra of PALABRAS_PROHIBIDAS) {
      expect(texto).not.toContain(
        palabra,
        `Aparece «${palabra}» con el cupo excedido. El servicio no se interrumpe: ` +
          'el exceso es un coste previsto, no un fallo.',
      );
    }
  });

  it('no se usa iconografía de severidad en el bloque de cupo', () => {
    // Act
    const html = bloqueCupo().innerHTML;

    // Assert — la forma comunica tanto como el color (design-system § 5)
    for (const icono of ICONOS_DE_SEVERIDAD) {
      expect(html).not.toContain(icono);
    }
  });

  it('sí dice, en cambio, que el servicio sigue y que el exceso se factura', () => {
    // Act
    const texto = (fixture.nativeElement.textContent ?? '').toLowerCase();

    // Assert — lo que debe estar, no solo lo que no debe
    expect(texto).toContain('no se interrumpe');
    expect(texto).toContain('factura');
  });
});
