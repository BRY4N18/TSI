/** @marker unit */
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Router, provideRouter } from '@angular/router';
import { of, throwError } from 'rxjs';

import { PartnerApiService } from '../../services/partner-api.service';
import { NUNCA_EXPIRA } from '../../services/models/centinelas';
import type {
  CredencialItem,
  Entorno,
  PartnerDetalle,
} from '../../services/models/partner.types';
import { ConfirmDialogService } from '../../../../shared/notifications/confirm-dialog.service';
import { MiIntegracionPage } from './mi-integracion.page';

function credencial(over: Partial<CredencialItem> = {}): CredencialItem {
  return {
    idcredencial: 1,
    nombre_credencial: 'pruebas',
    entorno: 'Sandbox' as Entorno,
    activo: true,
    fecha_creacion: 1,
    fecha_expiracion: Date.now() + 30 * 86_400_000,
    ...over,
  };
}

function detalle(over: Partial<PartnerDetalle> = {}): PartnerDetalle {
  return {
    idpartner: 7,
    idcliente: 100,
    nombrepartner: 'Aseguradora Norte',
    planapi: 'Profesional',
    limitellamadasmes: 10000,
    limitellamadasminuto: 120,
    activo: true,
    estado: 'Pruebas activo',
    contacto_tecnico_nombre: 'Ana',
    contacto_tecnico_gmail: 'ana@norte.com',
    fecha_suspension: '',
    motivo_suspension: '',
    credenciales: [credencial()],
    historial: [],
    ...over,
  };
}

const sobre = <T,>(data: T) => ({ data, meta: { pagination: null } });

describe('MiIntegracionPage', () => {
  let api: jasmine.SpyObj<PartnerApiService>;
  let fixture: ComponentFixture<MiIntegracionPage>;

  function montar(): void {
    TestBed.configureTestingModule({
      imports: [MiIntegracionPage],
      providers: [provideRouter([]), { provide: PartnerApiService, useValue: api }],
    });
    fixture = TestBed.createComponent(MiIntegracionPage);
    fixture.detectChanges();
  }

  const html = () => fixture.nativeElement as HTMLElement;

  beforeEach(() => {
    api = jasmine.createSpyObj<PartnerApiService>('PartnerApiService', [
      'miPartner',
      'emitirCredencial',
      'solicitarProduccion',
      'revocarCredencial',
      'estadoAcceso',
    ]);
    api.miPartner.and.returnValue(of(sobre(detalle())) as never);
  });

  describe('resolución del partner propio (FR-UI-013, BE-DELTA-01)', () => {
    it('carga la integración sin pedir ningún identificador al usuario', () => {
      // Act
      montar();

      // Assert
      expect(api.miPartner).toHaveBeenCalled();
      expect(html().textContent).not.toContain('idpartner');
    });

    it('explica el caso de usuario sin perfil de partner', () => {
      // Arrange
      api.miPartner.and.returnValue(
        throwError(() => ({ error: { code: 'sin_partner' } })) as never,
      );

      // Act
      montar();

      // Assert
      expect(html().textContent).toContain('no tiene un perfil de partner');
    });
  });

  describe('estado y «qué sigue» (FR-UI-014, FR-UI-015)', () => {
    it('muestra el badge del estado derivado', () => {
      // Act
      montar();

      // Assert
      expect(html().querySelector('[data-testid="badge-estado"]')?.textContent).toContain(
        'Pruebas activo',
      );
    });

    it('acompaña cada estado con su siguiente paso', () => {
      // Act
      montar();

      // Assert
      expect(html().querySelector('[data-testid="que-sigue"]')?.textContent?.trim()).toBeTruthy();
    });

    it('no ofrece ningún control que edite el estado', () => {
      // Act
      montar();

      // Assert
      expect(html().querySelector('select[name="estado"]')).toBeNull();
    });
  });

  describe('agrupación por entorno (FR-UI-016, RN-PON-008)', () => {
    it('agrupa bajo encabezados separados, no en una tabla plana', () => {
      // Arrange
      api.miPartner.and.returnValue(
        of(
          sobre(
            detalle({
              estado: 'Producción activa',
              credenciales: [
                credencial({ idcredencial: 1 }),
                credencial({
                  idcredencial: 2,
                  entorno: 'Producción',
                  nombre_credencial: 'prod',
                  fecha_expiracion: NUNCA_EXPIRA,
                }),
              ],
            }),
          ),
        ) as never,
      );

      // Act
      montar();

      // Assert
      expect(html().querySelector('[data-testid="grupo-Sandbox"]')).toBeTruthy();
      expect(html().querySelector('[data-testid="grupo-Producción"]')).toBeTruthy();
    });

    it('la distinción NO depende del color: hay ícono y etiqueta de texto', () => {
      // Si al quitar el color dejan de distinguirse, el diseño está mal (SC-006).
      // Act
      montar();

      // Assert
      const grupo = html().querySelector('[data-testid="grupo-Sandbox"]');
      expect(grupo?.textContent).toContain('Pruebas');
      expect(grupo?.querySelector('app-tabler-icon')).toBeTruthy();
    });

    it('oculta el grupo de producción mientras el partner no fue promovido', () => {
      // Act
      montar();

      // Assert
      expect(html().querySelector('[data-testid="grupo-Producción"]')).toBeNull();
    });

    it('muestra «No expira» para producción, nunca una fecha del 9999', () => {
      // Arrange
      api.miPartner.and.returnValue(
        of(
          sobre(
            detalle({
              estado: 'Producción activa',
              credenciales: [
                credencial({
                  idcredencial: 9,
                  entorno: 'Producción',
                  fecha_expiracion: NUNCA_EXPIRA,
                }),
              ],
            }),
          ),
        ) as never,
      );

      // Act
      montar();

      // Assert
      expect(html().querySelector('[data-testid="vigencia-9"]')?.textContent).toContain(
        'No expira',
      );
      expect(html().textContent).not.toContain('9999');
    });
  });

  describe('emisión sin plan (FR-UI-019)', () => {
    it('sustituye el CTA por el copy explicativo', () => {
      // Arrange — el centinela '' significa «sin plan»
      api.miPartner.and.returnValue(
        of(sobre(detalle({ planapi: '', limitellamadasmes: -1, estado: 'Registrado' }))) as never,
      );

      // Act
      montar();

      // Assert
      expect(html().querySelector('[data-testid="copy-sin-plan"]')).toBeTruthy();
      expect(html().querySelector('[data-testid="btn-emitir-Sandbox"]')).toBeNull();
    });
  });

  describe('nombre duplicado (FR-UI-017, FR-UI-018)', () => {
    it('detecta la colisión en cliente antes de llamar al backend', () => {
      // Arrange
      montar();
      fixture.componentInstance.form.setValue({ nombre_credencial: 'pruebas' });

      // Act / Assert
      expect(fixture.componentInstance.nombreDuplicado('Sandbox')).toBeTrue();
    });

    it('no envía la emisión si el nombre colisiona', () => {
      // Arrange
      montar();
      fixture.componentInstance.form.setValue({ nombre_credencial: 'pruebas' });

      // Act
      fixture.componentInstance.emitir('Sandbox');

      // Assert
      expect(api.emitirCredencial).not.toHaveBeenCalled();
    });

    it('un nombre libre no se marca como duplicado', () => {
      // Arrange
      montar();
      fixture.componentInstance.form.setValue({ nombre_credencial: 'otro-sistema' });

      // Act / Assert
      expect(fixture.componentInstance.nombreDuplicado('Sandbox')).toBeFalse();
    });
  });

  describe('idempotencia (FR-UI-023, SC-003)', () => {
    it('reutiliza la MISMA clave al reintentar tras un fallo de red', () => {
      // Sin esto, un timeout crearía una credencial de más y el secreto de la
      // primera se perdería para siempre.
      // Arrange
      api.emitirCredencial.and.returnValue(throwError(() => ({ error: {} })) as never);
      montar();
      fixture.componentInstance.form.setValue({ nombre_credencial: 'sistema-a' });

      // Act
      fixture.componentInstance.emitir('Sandbox');
      fixture.componentInstance.emitir('Sandbox');

      // Assert
      const clave1 = api.emitirCredencial.calls.argsFor(0)[2];
      const clave2 = api.emitirCredencial.calls.argsFor(1)[2];
      expect(clave1).toBe(clave2);
    });

    it('renueva la clave tras un éxito: el siguiente es otro intento', () => {
      // Arrange
      api.emitirCredencial.and.returnValue(
        of(sobre({ ...credencial({ idcredencial: 3 }), client_id: 'x', client_secret: 's' })) as never,
      );
      montar();
      fixture.componentInstance.form.setValue({ nombre_credencial: 'sistema-a' });
      fixture.componentInstance.emitir('Sandbox');
      const primera = api.emitirCredencial.calls.argsFor(0)[2];

      // Act
      fixture.componentInstance.form.setValue({ nombre_credencial: 'sistema-b' });
      fixture.componentInstance.emitir('Sandbox');

      // Assert
      expect(api.emitirCredencial.calls.argsFor(1)[2]).not.toBe(primera);
    });
  });

  describe('navegación al secreto', () => {
    it('pasa la credencial por estado de navegación, no por la URL', () => {
      // Arrange
      const emitida = { ...credencial({ idcredencial: 4 }), client_id: 'i', client_secret: 'sec' };
      api.emitirCredencial.and.returnValue(of(sobre(emitida)) as never);
      montar();
      const navegar = spyOn(TestBed.inject(Router), 'navigate');
      fixture.componentInstance.form.setValue({ nombre_credencial: 'sistema-c' });

      // Act
      fixture.componentInstance.emitir('Sandbox');

      // Assert
      const [ruta, extras] = navegar.calls.mostRecent().args as [string[], { state: object }];
      expect(ruta).toEqual(['/partners/portal/credencial-emitida']);
      expect(JSON.stringify(extras.state)).toContain('sec');
      expect(ruta.join('/')).not.toContain('sec');
    });
  });

  describe('regenerar credencial vencida (FR-UI-024, US-FE-5)', () => {
    it('marca como vencida una credencial pasada y ofrece regenerar', () => {
      // Arrange
      api.miPartner.and.returnValue(
        of(
          sobre(
            detalle({
              credenciales: [credencial({ idcredencial: 5, fecha_expiracion: 1000 })],
            }),
          ),
        ) as never,
      );

      // Act
      montar();

      // Assert
      expect(html().querySelector('[data-testid="vencida-5"]')).toBeTruthy();
      expect(html().querySelector('[data-testid="btn-regenerar-5"]')).toBeTruthy();
    });

    it('regenerar reutiliza el nombre y el entorno de la vencida', () => {
      // Arrange
      api.emitirCredencial.and.returnValue(throwError(() => ({ error: {} })) as never);
      montar();

      // Act
      fixture.componentInstance.regenerar(
        credencial({ idcredencial: 5, nombre_credencial: 'vieja', fecha_expiracion: 1000 }),
      );

      // Assert
      const [, cuerpo] = api.emitirCredencial.calls.mostRecent().args;
      expect(cuerpo.nombre_credencial).toBe('vieja');
      expect(cuerpo.entorno).toBe('Sandbox');
    });
  });

  describe('partner suspendido (RN-PAC-016)', () => {
    it('explica por qué se le cortó el acceso, no solo que está suspendido', () => {
      // Arrange — el partner suspendido conserva la lectura y esta es la
      // pantalla donde entiende el motivo y qué hacer.
      api.miPartner.and.returnValue(of(sobre(detalle({ estado: 'Suspendido' }))) as never);
      api.estadoAcceso.and.returnValue(
        of(
          sobre({
            idpartner: 1,
            activo: false,
            fecha_suspension: '2026-08-01T09:00:00+00:00',
            motivo_suspension: 'Mora de 18 días en excedente de API',
            en_mora: true,
            dias_mora: 18,
            avisos_enviados: [],
            credenciales: [],
            historial: [],
          }),
        ) as never,
      );

      // Act
      montar();

      // Assert
      const panel = html().querySelector('[data-testid="panel-suspension"]');
      expect(panel).toBeTruthy();
      expect(panel!.textContent).toContain('Mora de 18 días en excedente de API');
      expect(html().querySelector('[data-testid="dias-mora"]')?.textContent).toContain('18');
    });

    it('no pide el detalle de acceso cuando el partner no está suspendido', () => {
      // Act
      montar();

      // Assert
      expect(api.estadoAcceso).not.toHaveBeenCalled();
      expect(html().querySelector('[data-testid="panel-suspension"]')).toBeNull();
    });
  });

  describe('revocación de autoservicio (SRS §3.4.3)', () => {
    it('ofrece revocar cada credencial vigente', () => {
      // Arrange — el endpoint existía y ninguna pantalla lo llamaba: el partner
      // no podía cortar una credencial comprometida.
      api.miPartner.and.returnValue(
        of(sobre(detalle({ credenciales: [credencial({ idcredencial: 7 })] }))) as never,
      );

      // Act
      montar();

      // Assert
      expect(html().querySelector('[data-testid="btn-revocar-7"]')).toBeTruthy();
    });

    it('no ofrece revocar una credencial ya vencida (se regenera, no se revoca)', () => {
      // Arrange
      api.miPartner.and.returnValue(
        of(
          sobre(
            detalle({
              credenciales: [credencial({ idcredencial: 8, fecha_expiracion: 1000 })],
            }),
          ),
        ) as never,
      );

      // Act
      montar();

      // Assert
      expect(html().querySelector('[data-testid="btn-revocar-8"]')).toBeNull();
      expect(html().querySelector('[data-testid="btn-regenerar-8"]')).toBeTruthy();
    });

    it('avisa en 2 pasos y explica que las demás credenciales siguen operando', async () => {
      // Arrange — montar primero: `TestBed.inject` antes de configurar el
      // módulo lo instancia y rompe el `configureTestingModule` de `montar()`.
      montar();
      const dialog = TestBed.inject(ConfirmDialogService);
      spyOn(dialog, 'confirm').and.resolveTo(false);

      // Act
      await fixture.componentInstance.revocar(
        credencial({ idcredencial: 7, nombre_credencial: 'tablero-interno' }),
      );

      // Assert — cancelar no llama al backend
      const peticion = (dialog.confirm as jasmine.Spy).calls.mostRecent().args[0];
      expect(peticion.tone).toBe('danger');
      expect(peticion.message).toContain('tablero-interno');
      expect(peticion.message).toContain('reemplazo');
      expect(api.revocarCredencial).not.toHaveBeenCalled();
    });
  });

  describe('solicitar producción (FR-UI-026)', () => {
    it('se ofrece en «Pruebas activo»', () => {
      // Act
      montar();

      // Assert
      expect(html().querySelector('[data-testid="btn-solicitar-produccion"]')).toBeTruthy();
    });

    it('en otro estado explica la ruta en vez de ofrecer un botón que fallaría', () => {
      // Arrange
      api.miPartner.and.returnValue(of(sobre(detalle({ estado: 'Registrado' }))) as never);

      // Act
      montar();

      // Assert
      expect(html().querySelector('[data-testid="btn-solicitar-produccion"]')).toBeNull();
      expect(html().querySelector('[data-testid="ruta-produccion"]')).toBeTruthy();
    });
  });

  describe('partner suspendido (FR-UI-034)', () => {
    it('no ofrece emitir credenciales', () => {
      // Arrange
      api.miPartner.and.returnValue(
        of(sobre(detalle({ estado: 'Suspendido', activo: false }))) as never,
      );

      // Act
      montar();

      // Assert
      expect(html().querySelector('[data-testid="btn-emitir-Sandbox"]')).toBeNull();
    });
  });
});
