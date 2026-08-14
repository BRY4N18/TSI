/** @marker unit */
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';

import { ConfirmDialogService } from '../../../../shared/notifications/confirm-dialog.service';
import { PartnerApiService } from '../../services/partner-api.service';
import { PartnerColaAcceso } from '../../services/models/partner.types';
import { ColaAccesoPage } from './cola-acceso.page';

const SUSPENDIDO: PartnerColaAcceso = {
  idpartner: 2,
  nombrepartner: 'Andes Logística',
  activo: false,
  motivo_suspension: 'Mora de 18 días en excedente de API',
  fecha_suspension: '2026-08-01T09:00:00+00:00',
  dias_mora: 0,
  ultimo_aviso: '',
};

const EN_MORA: PartnerColaAcceso = {
  idpartner: 3,
  nombrepartner: 'Sierra Datos',
  activo: true,
  motivo_suspension: '',
  fecha_suspension: '',
  dias_mora: 11,
  ultimo_aviso: 'aviso_previo_suspension',
};

function sobre<T>(data: T) {
  return { data, meta: { pagination: null } };
}

describe('ColaAccesoPage (RF-PAC-005 / RF-PAC-009)', () => {
  let api: jasmine.SpyObj<PartnerApiService>;
  let fixture: ComponentFixture<ColaAccesoPage>;
  const html = () => fixture.nativeElement as HTMLElement;

  function montar(filas: PartnerColaAcceso[]): void {
    api.colaAcceso.and.returnValue(of(sobre(filas)) as never);
    TestBed.configureTestingModule({
      imports: [ColaAccesoPage],
      providers: [{ provide: PartnerApiService, useValue: api }],
    });
    fixture = TestBed.createComponent(ColaAccesoPage);
    fixture.detectChanges();
  }

  beforeEach(() => {
    api = jasmine.createSpyObj<PartnerApiService>('PartnerApiService', [
      'colaAcceso',
      'suspender',
      'reactivar',
    ]);
  });

  it('ofrece reactivar a los suspendidos y suspender a los que siguen activos', () => {
    // Act
    montar([SUSPENDIDO, EN_MORA]);

    // Assert
    expect(html().querySelector('[data-testid="btn-reactivar-2"]')).toBeTruthy();
    expect(html().querySelector('[data-testid="btn-suspender-2"]')).toBeNull();
    expect(html().querySelector('[data-testid="btn-suspender-3"]')).toBeTruthy();
  });

  it('presenta el motivo como texto redactado, no como código', () => {
    // Act
    montar([SUSPENDIDO]);

    // Assert
    expect(html().textContent).toContain('Mora de 18 días en excedente de API');
  });

  it('al reactivar explica que las credenciales revocadas siguen inactivas a propósito', async () => {
    // Arrange — RN-PAC-011: si la UI no lo dice, parecerá un fallo.
    montar([SUSPENDIDO]);
    const dialog = TestBed.inject(ConfirmDialogService);
    spyOn(dialog, 'confirm').and.resolveTo(true);
    api.reactivar.and.returnValue(
      of({
        data: {
          idpartner: 2,
          activo: true,
          credenciales_restituidas: 1,
          credenciales_no_restituidas: 2,
        },
        meta: { pagination: null },
      }) as never,
    );

    // Act
    await fixture.componentInstance.reactivar(SUSPENDIDO);
    fixture.detectChanges();

    // Assert
    const texto = html().querySelector('[data-testid="resultado-accion"]')?.textContent ?? '';
    expect(texto).toContain('restituidas: 1');
    expect(texto).toContain('2 sin restituir');
    expect(texto).toContain('seguridad');
  });

  it('cancelar la confirmación no llama al backend', async () => {
    // Arrange — suspender desactiva TODAS las credenciales: no puede dispararse
    // de un solo clic.
    montar([EN_MORA]);
    const dialog = TestBed.inject(ConfirmDialogService);
    spyOn(dialog, 'confirm').and.resolveTo(false);

    // Act
    await fixture.componentInstance.suspender(EN_MORA);

    // Assert
    expect(api.suspender).not.toHaveBeenCalled();
  });

  it('avisa de que la suspensión alcanza a pruebas y a producción', async () => {
    // Arrange
    montar([EN_MORA]);
    const dialog = TestBed.inject(ConfirmDialogService);
    spyOn(dialog, 'confirm').and.resolveTo(false);

    // Act
    await fixture.componentInstance.suspender(EN_MORA);

    // Assert
    const peticion = (dialog.confirm as jasmine.Spy).calls.mostRecent().args[0];
    expect(peticion.message).toContain('TODAS');
    expect(peticion.tone).toBe('danger');
  });
});
