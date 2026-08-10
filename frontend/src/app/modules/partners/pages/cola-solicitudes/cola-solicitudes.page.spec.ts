/** @marker unit */
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of, throwError } from 'rxjs';

import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';
import { PartnerApiService } from '../../services/partner-api.service';
import type { PartnerListItem } from '../../services/models/partner.types';
import { ColaSolicitudesPage } from './cola-solicitudes.page';

function pendiente(over: Partial<PartnerListItem> = {}): PartnerListItem {
  return {
    idpartner: 7,
    idcliente: 100,
    nombrepartner: 'Aseguradora Norte',
    planapi: 'Profesional',
    limitellamadasmes: 10000,
    limitellamadasminuto: 120,
    activo: true,
    estado: 'Pendiente de aprobación',
    ...over,
  };
}

const sobre = (data: PartnerListItem[]) => ({
  data,
  meta: { pagination: { next_cursor: null, limit: 50 } },
});

const MOTIVO_VALIDO = 'Faltan pruebas de carga en el entorno de sandbox';

describe('ColaSolicitudesPage', () => {
  let api: jasmine.SpyObj<PartnerApiService>;
  let auth: jasmine.SpyObj<AuthApiService>;
  let fixture: ComponentFixture<ColaSolicitudesPage>;

  function montar(): void {
    TestBed.configureTestingModule({
      imports: [ColaSolicitudesPage],
      providers: [
        provideRouter([]),
        { provide: PartnerApiService, useValue: api },
        { provide: AuthApiService, useValue: auth },
      ],
    });
    fixture = TestBed.createComponent(ColaSolicitudesPage);
    fixture.detectChanges();
  }

  const html = () => fixture.nativeElement as HTMLElement;

  beforeEach(() => {
    api = jasmine.createSpyObj<PartnerApiService>('PartnerApiService', [
      'listar',
      'resolverPromocion',
    ]);
    auth = jasmine.createSpyObj<AuthApiService>('AuthApiService', ['hasRole', 'hasAnyRole']);
    auth.hasRole.and.returnValue(true); // Administrador por defecto
    api.listar.and.returnValue(of(sobre([pendiente()])) as never);
    api.resolverPromocion.and.returnValue(
      of({ data: { idpartner: 7, estado: 'Producción activa' }, meta: { pagination: null } }) as never,
    );
  });

  describe('origen de la cola (Decisión 8)', () => {
    it('se alimenta del listado filtrado, sin endpoint nuevo', () => {
      // Act
      montar();

      // Assert
      expect(api.listar).toHaveBeenCalledWith(
        jasmine.objectContaining({ estado: 'Pendiente de aprobación' }),
      );
    });

    it('el estado vacío es un resultado deseable, no un error', () => {
      // Arrange
      api.listar.and.returnValue(of(sobre([])) as never);

      // Act
      montar();

      // Assert
      expect(html().textContent).toContain('No hay solicitudes pendientes');
      expect(html().querySelector('[data-testid="error-state"]')).toBeNull();
    });

    it('muestra el estado de error con Reintentar si la carga falla', () => {
      // Arrange
      api.listar.and.returnValue(throwError(() => new Error('red')) as never);

      // Act
      montar();

      // Assert
      expect(html().querySelector('[data-testid="error-state"]')).toBeTruthy();
    });
  });

  describe('separación de actores (FR-UI-011)', () => {
    it('el Administrador ve las acciones de resolver', () => {
      // Act
      montar();

      // Assert
      expect(html().querySelector('[data-testid="btn-aprobar-7"]')).toBeTruthy();
      expect(html().querySelector('[data-testid="btn-rechazar-7"]')).toBeTruthy();
    });

    it('el Desarrollador de APIs ve la cola SIN acciones de resolver', () => {
      // Si pudiera resolver, la aprobación humana dejaría de ser un control.
      // Arrange
      auth.hasRole.and.returnValue(false);

      // Act
      montar();

      // Assert
      expect(html().querySelector('[data-testid="solicitud-7"]')).toBeTruthy();
      expect(html().querySelector('[data-testid="btn-aprobar-7"]')).toBeNull();
      expect(html().querySelector('[data-testid="btn-rechazar-7"]')).toBeNull();
    });
  });

  describe('aprobar (FR-UI-009)', () => {
    it('exige confirmación en 2 pasos', () => {
      // Arrange
      montar();

      // Act — el primer click solo abre la confirmación
      fixture.componentInstance.pedirConfirmacionAprobar(pendiente());
      fixture.detectChanges();

      // Assert
      expect(html().querySelector('[data-testid="confirmar-aprobar-7"]')).toBeTruthy();
      expect(api.resolverPromocion).not.toHaveBeenCalled();
    });

    it('NO muestra ningún secreto al Administrador', () => {
      // El backend devuelve la credencial productiva, pero su secreto no es de
      // quien aprueba: no tendría canal seguro para entregarlo (BE-DELTA-02).
      // Arrange
      api.resolverPromocion.and.returnValue(
        of({
          data: {
            idpartner: 7,
            estado: 'Producción activa',
            credencial: { client_secret: 'SECRETO-QUE-NO-DEBE-VERSE', client_id: 'x' },
          },
          meta: { pagination: null },
        }) as never,
      );
      montar();

      // Act
      fixture.componentInstance.aprobar(pendiente());
      fixture.detectChanges();

      // Assert
      expect(html().textContent).not.toContain('SECRETO-QUE-NO-DEBE-VERSE');
    });

    it('avisa de que el secreto lo verá el partner, no el Administrador', () => {
      // Arrange
      montar();

      // Act
      fixture.componentInstance.pedirConfirmacionAprobar(pendiente());
      fixture.detectChanges();

      // Assert
      expect(html().textContent).toContain('El secreto no se te mostrará a ti');
    });

    it('refresca la cola tras aprobar', () => {
      // Arrange
      montar();
      api.listar.calls.reset();

      // Act
      fixture.componentInstance.aprobar(pendiente());

      // Assert
      expect(api.listar).toHaveBeenCalled();
    });
  });

  describe('rechazar con motivo (FR-UI-010, RN-PON-007)', () => {
    it('no envía nada si el motivo está vacío', () => {
      // El 422 del backend no debería alcanzarse desde esta UI.
      // Arrange
      montar();
      fixture.componentInstance.abrirRechazo(pendiente());

      // Act
      fixture.componentInstance.rechazar(pendiente());

      // Assert
      expect(api.resolverPromocion).not.toHaveBeenCalled();
    });

    it('no acepta un motivo demasiado corto para ser accionable', () => {
      // Arrange
      montar();
      fixture.componentInstance.abrirRechazo(pendiente());
      fixture.componentInstance.formRechazo.setValue({ motivo: 'no' });

      // Act
      fixture.componentInstance.rechazar(pendiente());

      // Assert
      expect(api.resolverPromocion).not.toHaveBeenCalled();
    });

    it('envía el motivo literal que escribió el Administrador', () => {
      // Arrange
      montar();
      fixture.componentInstance.abrirRechazo(pendiente());
      fixture.componentInstance.formRechazo.setValue({ motivo: MOTIVO_VALIDO });

      // Act
      fixture.componentInstance.rechazar(pendiente());

      // Assert
      const [, cuerpo] = api.resolverPromocion.calls.mostRecent().args;
      expect(cuerpo).toEqual({ decision: 'rechazar', motivo: MOTIVO_VALIDO });
    });

    it('advierte que el motivo se envía al contacto técnico', () => {
      // Arrange
      montar();

      // Act
      fixture.componentInstance.abrirRechazo(pendiente());
      fixture.detectChanges();

      // Assert
      expect(html().textContent).toContain('se envía al contacto técnico');
    });

    it('el motivo es texto libre, no un catálogo de códigos', () => {
      // Arrange
      montar();

      // Act
      fixture.componentInstance.abrirRechazo(pendiente());
      fixture.detectChanges();

      // Assert
      expect(html().querySelector('[data-testid="input-motivo"]')?.tagName).toBe('TEXTAREA');
    });
  });

  describe('concurrencia entre administradores (FR-UI-012)', () => {
    it('informa sin culpar al usuario y refresca la cola', () => {
      // Arrange
      api.resolverPromocion.and.returnValue(
        throwError(() => ({ error: { code: 'sin_solicitud_pendiente' } })) as never,
      );
      montar();
      api.listar.calls.reset();

      // Act
      fixture.componentInstance.aprobar(pendiente());
      fixture.detectChanges();

      // Assert
      expect(html().querySelector('[data-testid="aviso-ya-resuelta"]')).toBeTruthy();
      expect(html().textContent).toContain('ya fue resuelta por otro administrador');
      expect(api.listar).toHaveBeenCalled();
    });

    it('el aviso de concurrencia no se presenta como error del usuario', () => {
      // Arrange
      api.resolverPromocion.and.returnValue(
        throwError(() => ({ error: { code: 'sin_solicitud_pendiente' } })) as never,
      );
      montar();

      // Act
      fixture.componentInstance.aprobar(pendiente());
      fixture.detectChanges();

      // Assert
      expect(fixture.componentInstance.errorAccion()).toBeNull();
    });
  });
});
