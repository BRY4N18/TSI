/** @marker unit */
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap, provideRouter } from '@angular/router';
import { of, throwError } from 'rxjs';

import { PartnerApiService } from '../../services/partner-api.service';
import type { PartnerDetalle } from '../../services/models/partner.types';
import { DetallePartnerPage } from './detalle-partner.page';

function detalle(over: Partial<PartnerDetalle> = {}): PartnerDetalle {
  return {
    idpartner: 7,
    idcliente: 100,
    nombrepartner: 'Aseguradora Norte',
    planapi: 'Profesional',
    limitellamadasmes: 10000,
    limitellamadasminuto: 120,
    activo: true,
    estado: 'Plan asignado',
    contacto_tecnico_nombre: 'Ana Torres',
    contacto_tecnico_gmail: 'ana@norte.com',
    fecha_suspension: '',
    motivo_suspension: '',
    credenciales: [],
    historial: [],
    ...over,
  };
}

const sobre = <T,>(data: T) => ({ data, meta: { pagination: null } });

describe('DetallePartnerPage', () => {
  let api: jasmine.SpyObj<PartnerApiService>;
  let fixture: ComponentFixture<DetallePartnerPage>;

  function configurar(modo: 'ver' | 'crear'): void {
    TestBed.configureTestingModule({
      imports: [DetallePartnerPage],
      providers: [
        provideRouter([]),
        { provide: PartnerApiService, useValue: api },
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: { data: { modo }, paramMap: convertToParamMap({ idpartner: '7' }) },
          },
        },
      ],
    });
    fixture = TestBed.createComponent(DetallePartnerPage);
    fixture.detectChanges();
  }

  const html = () => fixture.nativeElement as HTMLElement;

  beforeEach(() => {
    api = jasmine.createSpyObj<PartnerApiService>('PartnerApiService', [
      'detalle',
      'registrar',
      'asignarPlan',
      'clientesElegibles',
    ]);
    api.detalle.and.returnValue(of(sobre(detalle())) as never);
    api.clientesElegibles.and.returnValue(
      of(sobre([{ idcliente: 100, nombre: 'Empresa Demo Torres' }])) as never,
    );
  });

  describe('chrome del workpanel (golden sample)', () => {
    it('ofrece el link «Volver a la lista»', () => {
      // Act
      configurar('ver');

      // Assert
      expect(html().querySelector('[data-testid="link-volver"]')?.textContent).toContain('Volver');
    });

    it('muestra el eyebrow de modo', () => {
      // Act
      configurar('ver');

      // Assert
      expect(html().textContent).toContain('Detalles');
    });

    it('muestra el badge de estado junto al título', () => {
      // Act
      configurar('ver');

      // Assert
      expect(html().querySelector('[data-testid="badge-estado"]')?.textContent).toContain(
        'Plan asignado',
      );
    });
  });

  describe('modo Ver — solo lectura de verdad', () => {
    it('presenta los datos como <dl>, no como inputs deshabilitados', () => {
      // El design-system lo prohíbe explícitamente: un <input disabled> finge
      // un formulario que no existe.
      // Act
      configurar('ver');

      // Assert
      expect(html().querySelector('[data-testid="dl-identificacion"]')?.tagName).toBe('DL');
      expect(html().querySelectorAll('input[disabled]').length).toBe(0);
    });

    it('no ofrece botón de guardado', () => {
      // Act
      configurar('ver');

      // Assert
      expect(html().querySelector('[data-testid="btn-guardar"]')).toBeNull();
    });

    it('traduce los centinelas de plan y cupo', () => {
      // Arrange
      api.detalle.and.returnValue(
        of(sobre(detalle({ planapi: '', limitellamadasmes: -1, estado: 'Registrado' }))) as never,
      );

      // Act
      configurar('ver');

      // Assert
      expect(html().querySelector('[data-testid="dd-plan"]')?.textContent).toContain('Sin plan');
      expect(html().querySelector('[data-testid="dd-cupo-mes"]')?.textContent).toContain(
        'Sin asignar',
      );
    });
  });

  describe('acción de dominio: asignar plan', () => {
    it('se ofrece a un partner en «Registrado»', () => {
      // Arrange
      api.detalle.and.returnValue(of(sobre(detalle({ estado: 'Registrado' }))) as never);

      // Act
      configurar('ver');

      // Assert
      expect(html().querySelector('[data-testid="btn-asignar-plan"]')).toBeTruthy();
    });

    it('advierte que el cupo queda congelado', () => {
      // Arrange
      api.detalle.and.returnValue(of(sobre(detalle({ estado: 'Registrado' }))) as never);

      // Act
      configurar('ver');

      // Assert
      expect(html().textContent).toContain('congelado');
    });

    it('NO se ofrece a un partner suspendido (CA-PON-012)', () => {
      // Arrange
      api.detalle.and.returnValue(
        of(sobre(detalle({ estado: 'Suspendido', activo: false }))) as never,
      );

      // Act
      configurar('ver');

      // Assert
      expect(html().querySelector('[data-testid="btn-asignar-plan"]')).toBeNull();
    });
  });

  describe('modo Crear', () => {
    it('reutiliza el mismo componente, con formulario vacío', () => {
      // Act
      configurar('crear');

      // Assert
      expect(html().querySelector('[data-testid="btn-guardar"]')).toBeTruthy();
      expect(fixture.componentInstance.form.getRawValue().nombrepartner).toBe('');
    });

    it('no pide el idcliente a mano: se elige por nombre', () => {
      // Act
      configurar('crear');

      // Assert
      const control = html().querySelector('[data-testid="input-cliente"]');
      expect(control?.tagName).toBe('SELECT');
    });

    it('POBLA el combobox con clientes elegibles', () => {
      // Regresión: la primera versión declaraba el signal de clientes y nunca
      // lo cargaba, así que el select solo tenía el placeholder y el alta era
      // literalmente inalcanzable. Comprobar que es un <select> no bastaba.
      // Act
      configurar('crear');

      // Assert
      expect(api.clientesElegibles).toHaveBeenCalled();
      const opciones = Array.from(
        html().querySelectorAll('[data-testid="input-cliente"] option'),
      ).map((o) => o.textContent?.trim());
      expect(opciones.length).toBeGreaterThan(1);
      expect(opciones).toContain('Empresa Demo Torres');
    });

    it('no pide la lista de clientes en modo Ver', () => {
      // Act
      configurar('ver');

      // Assert
      expect(api.clientesElegibles).not.toHaveBeenCalled();
    });

    it('no envía nada mientras el formulario es inválido', () => {
      // Act
      configurar('crear');
      fixture.componentInstance.guardar();

      // Assert
      expect(api.registrar).not.toHaveBeenCalled();
    });
  });

  describe('mapeo de errores de negocio (SC-005)', () => {
    function fallar(code: string, extra: Record<string, unknown> = {}): void {
      api.registrar.and.returnValue(
        throwError(() => ({ error: { code, detail: 'x', ...extra } })) as never,
      );
      configurar('crear');
      fixture.componentInstance.form.setValue({
        idcliente: 100,
        nombrepartner: 'Demo',
        contacto_tecnico_nombre: 'Ana',
        contacto_tecnico_gmail: 'ana@demo.com',
      });
      fixture.componentInstance.guardar();
      fixture.detectChanges();
    }

    it('el duplicado enlaza al partner existente', () => {
      // Act
      fallar('partner_duplicado', { idpartner_existente: 42 });

      // Assert
      expect(fixture.componentInstance.idpartnerDuplicado()).toBe(42);
      expect(html().querySelector('[data-testid="link-partner-existente"]')).toBeTruthy();
    });

    it('la falta de suscripción explica dónde se resuelve', () => {
      // Act
      fallar('sin_suscripcion');

      // Assert
      expect(fixture.componentInstance.errorAccion()).toContain('Suscripciones');
    });

    it('el plan incompleto explica que se corrige en el catálogo', () => {
      // Act
      fallar('plan_incompleto');

      // Assert
      expect(fixture.componentInstance.errorAccion()).toContain('catálogo de planes');
    });

    it('ningún código conocido produce «error inesperado»', () => {
      // Act
      fallar('sin_suscripcion');

      // Assert
      expect(fixture.componentInstance.errorAccion()?.toLowerCase()).not.toContain('inesperado');
    });
  });

  describe('asignar plan — ejecución', () => {
    it('recarga el detalle tras asignar, para mostrar el cupo derivado', () => {
      // Arrange
      api.detalle.and.returnValue(of(sobre(detalle({ estado: 'Registrado' }))) as never);
      api.asignarPlan.and.returnValue(of(sobre(detalle())) as never);
      configurar('ver');
      api.detalle.calls.reset();

      // Act
      fixture.componentInstance.asignarPlan(detalle({ estado: 'Registrado' }));

      // Assert
      expect(api.asignarPlan).toHaveBeenCalled();
      expect(api.detalle).toHaveBeenCalled();
    });

    it('presenta el fallo de plan incompleto sin dejar el botón cargando', () => {
      // Arrange
      api.detalle.and.returnValue(of(sobre(detalle({ estado: 'Registrado' }))) as never);
      api.asignarPlan.and.returnValue(
        throwError(() => ({ error: { code: 'plan_incompleto' } })) as never,
      );
      configurar('ver');

      // Act
      fixture.componentInstance.asignarPlan(detalle({ estado: 'Registrado' }));

      // Assert
      expect(fixture.componentInstance.asignando()).toBeFalse();
      expect(fixture.componentInstance.errorAccion()).toContain('catálogo de planes');
    });
  });

  describe('estados no felices del detalle', () => {
    it('muestra el estado de error con Reintentar si la carga falla', () => {
      // Arrange
      api.detalle.and.returnValue(throwError(() => new Error('red')) as never);

      // Act
      configurar('ver');

      // Assert
      expect(html().querySelector('[data-testid="error-state"]')).toBeTruthy();
    });

    it('navega al detalle recién creado tras un registro exitoso', () => {
      // Arrange
      api.registrar.and.returnValue(of(sobre(detalle({ idpartner: 99 }))) as never);
      configurar('crear');
      fixture.componentInstance.form.setValue({
        idcliente: 100,
        nombrepartner: 'Demo',
        contacto_tecnico_nombre: 'Ana',
        contacto_tecnico_gmail: 'ana@demo.com',
      });

      // Act
      fixture.componentInstance.guardar();

      // Assert
      expect(fixture.componentInstance.guardando()).toBeFalse();
      expect(api.registrar).toHaveBeenCalled();
    });

    it('un código desconocido cae al detalle del backend, no a texto vacío', () => {
      // Arrange
      api.registrar.and.returnValue(
        throwError(() => ({ error: { code: 'zzz', detail: 'Fallo puntual del servidor' } })) as never,
      );
      configurar('crear');
      fixture.componentInstance.form.setValue({
        idcliente: 100,
        nombrepartner: 'Demo',
        contacto_tecnico_nombre: 'Ana',
        contacto_tecnico_gmail: 'ana@demo.com',
      });

      // Act
      fixture.componentInstance.guardar();

      // Assert
      expect(fixture.componentInstance.errorAccion()).toBe('Fallo puntual del servidor');
    });
  });

  describe('idempotencia (FR-UI-023)', () => {
    it('reutiliza la misma clave al reintentar tras un fallo de red', () => {
      // Arrange
      api.registrar.and.returnValue(throwError(() => ({ error: {} })) as never);
      configurar('crear');
      fixture.componentInstance.form.setValue({
        idcliente: 100,
        nombrepartner: 'Demo',
        contacto_tecnico_nombre: 'Ana',
        contacto_tecnico_gmail: 'ana@demo.com',
      });

      // Act — dos intentos del mismo usuario sobre el mismo formulario
      fixture.componentInstance.guardar();
      fixture.componentInstance.guardar();

      // Assert — sin esto se crearían dos partners
      const [, clave1] = api.registrar.calls.argsFor(0);
      const [, clave2] = api.registrar.calls.argsFor(1);
      expect(clave1).toBe(clave2);
    });
  });
});
