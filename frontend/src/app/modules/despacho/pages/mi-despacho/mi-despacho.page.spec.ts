/** @marker unit */
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';

import { NotificationService } from '../../../../shared/notifications/notification.service';
import { MiDespachoApiService } from '../../services/mi-despacho-api.service';
import { MiDespachoPage } from './mi-despacho.page';

describe('MiDespachoPage', () => {
  let fixture: ComponentFixture<MiDespachoPage>;
  let api: jasmine.SpyObj<MiDespachoApiService>;
  let notifications: jasmine.SpyObj<NotificationService>;

  beforeEach(async () => {
    api = jasmine.createSpyObj('MiDespachoApiService', ['listarPendientes', 'confirmar', 'rechazar']);
    notifications = jasmine.createSpyObj('NotificationService', ['toast', 'alert']);
    api.listarPendientes.and.returnValue(
      of<any>({
        data: {
          pendientes: [
            { idnotificaciondespacho: 1, idaccidente: 'ACC-1', idseveridad: 3, estadonotificacion: 'Pendiente' },
          ],
        },
        meta: {},
      }),
    );

    await TestBed.configureTestingModule({
      imports: [MiDespachoPage],
      providers: [
        { provide: MiDespachoApiService, useValue: api },
        { provide: NotificationService, useValue: notifications },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(MiDespachoPage);
    fixture.detectChanges();
  });

  it('ngOnInit_loads_pendientes', () => {
    // Assert
    expect(api.listarPendientes).toHaveBeenCalled();
    expect(fixture.componentInstance.pendientes().length).toBe(1);
  });

  it('confirmar_when_success_shows_toast_and_reloads', () => {
    // Arrange
    api.confirmar.and.returnValue(of<any>({ data: { message: 'Confirmado' }, meta: {} }));

    // Act
    fixture.componentInstance.confirmar(1);

    // Assert
    expect(api.confirmar).toHaveBeenCalledWith(1);
    expect(notifications.toast).toHaveBeenCalledWith('Confirmado', 'success');
    expect(api.listarPendientes).toHaveBeenCalledTimes(2);
  });

  it('confirmar_when_error_shows_alert', () => {
    // Arrange
    api.confirmar.and.returnValue(throwError(() => new Error('fail')));

    // Act
    fixture.componentInstance.confirmar(1);

    // Assert
    expect(notifications.alert).toHaveBeenCalled();
  });

  it('iniciarRechazo_opens_empty_motivo_for_that_card', () => {
    // Act
    fixture.componentInstance.iniciarRechazo(1);

    // Assert
    expect(fixture.componentInstance.rechazandoId()).toBe(1);
    expect(fixture.componentInstance.motivoRechazo).toBe('');
  });

  it('confirmarRechazo_when_motivo_empty_does_not_call_api', () => {
    // Arrange
    fixture.componentInstance.iniciarRechazo(1);
    fixture.componentInstance.motivoRechazo = '   ';

    // Act
    fixture.componentInstance.confirmarRechazo(1);

    // Assert
    expect(api.rechazar).not.toHaveBeenCalled();
  });

  it('confirmarRechazo_when_success_sends_motivo_and_reloads', () => {
    // Arrange
    api.rechazar.and.returnValue(of<any>({ data: { message: 'Rechazado' }, meta: {} }));
    fixture.componentInstance.iniciarRechazo(1);
    fixture.componentInstance.motivoRechazo = 'Sin unidad disponible';

    // Act
    fixture.componentInstance.confirmarRechazo(1);

    // Assert
    expect(api.rechazar).toHaveBeenCalledWith(1, { motivo: 'Sin unidad disponible' });
    expect(notifications.toast).toHaveBeenCalledWith('Rechazado', 'success');
    expect(fixture.componentInstance.rechazandoId()).toBeNull();
  });

  it('cancelarRechazo_closes_form_without_calling_api', () => {
    // Arrange
    fixture.componentInstance.iniciarRechazo(1);
    fixture.componentInstance.motivoRechazo = 'algo';

    // Act
    fixture.componentInstance.cancelarRechazo();

    // Assert
    expect(fixture.componentInstance.rechazandoId()).toBeNull();
    expect(fixture.componentInstance.motivoRechazo).toBe('');
    expect(api.rechazar).not.toHaveBeenCalled();
  });

  it('cargar_when_error_sets_error_state', () => {
    // Arrange
    api.listarPendientes.and.returnValue(throwError(() => new Error('fail')));

    // Act
    fixture.componentInstance.cargar();

    // Assert
    expect(fixture.componentInstance.error()).toBeTruthy();
  });
});
