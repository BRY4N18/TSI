/** @marker unit */
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { of, throwError } from 'rxjs';

import { NotificationService } from '../../../../shared/notifications/notification.service';
import { MiDespachoApiService } from '../../services/mi-despacho-api.service';
import { MiDespachoPage } from './mi-despacho.page';

describe('MiDespachoPage', () => {
  let fixture: ComponentFixture<MiDespachoPage>;
  let api: jasmine.SpyObj<MiDespachoApiService>;
  let notifications: jasmine.SpyObj<NotificationService>;
  let router: jasmine.SpyObj<Router>;

  beforeEach(async () => {
    api = jasmine.createSpyObj('MiDespachoApiService', ['listarPendientes', 'confirmar', 'rechazar']);
    notifications = jasmine.createSpyObj('NotificationService', ['toast', 'alert']);
    router = jasmine.createSpyObj('Router', ['navigate']);
    api.listarPendientes.and.returnValue(
      of<any>({
        data: {
          pendientes: [
            {
              idnotificaciondespacho: 1,
              idaccidente: 'ACC-1',
              idseveridad: 3,
              estadonotificacion: 'Pendiente',
              idunidademergencia: 1,
              unidademergencia: 'Ambulancia 01',
              fechahora: Date.now(),
            },
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
        { provide: Router, useValue: router },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(MiDespachoPage);
    fixture.detectChanges();
  });

  afterEach(() => {
    fixture.destroy(); // detiene el setInterval del countdown
  });

  it('ngOnInit_loads_pendientes', () => {
    // Assert
    expect(api.listarPendientes).toHaveBeenCalled();
    expect(fixture.componentInstance.pendientes().length).toBe(1);
  });

  it('confirmar_when_success_shows_toast_and_navigates_to_mi_seguimiento', () => {
    // Arrange
    api.confirmar.and.returnValue(
      of<any>({
        data: {
          message: 'Confirmado',
          idaccidente: 'ACC-1',
          iddespacho: 42,
          idunidademergencia: 1,
        },
        meta: {},
      }),
    );

    // Act
    fixture.componentInstance.confirmar(1);

    // Assert
    expect(api.confirmar).toHaveBeenCalledWith(1);
    expect(notifications.toast).toHaveBeenCalledWith('Confirmado', 'success');
    expect(router.navigate).toHaveBeenCalledWith(['/seguimiento/mi-seguimiento']);
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

  it('incidenteActivo_returns_first_pendiente_and_colaPendientes_the_rest', () => {
    // Arrange
    api.listarPendientes.and.returnValue(
      of<any>({
        data: {
          pendientes: [
            { idnotificaciondespacho: 1, idaccidente: 'ACC-1', idseveridad: 3, estadonotificacion: 'Pendiente', idunidademergencia: 1, unidademergencia: 'Ambulancia 01', fechahora: Date.now() },
            { idnotificaciondespacho: 2, idaccidente: 'ACC-2', idseveridad: 2, estadonotificacion: 'Pendiente', idunidademergencia: 1, unidademergencia: 'Ambulancia 01', fechahora: Date.now() },
          ],
        },
        meta: {},
      }),
    );

    // Act
    fixture.componentInstance.cargar();

    // Assert
    expect(fixture.componentInstance.incidenteActivo()?.idnotificaciondespacho).toBe(1);
    expect(fixture.componentInstance.colaPendientes().map((p) => p.idnotificaciondespacho)).toEqual([2]);
  });

  it('promoverAlFrente_moves_item_from_cola_to_incidenteActivo', () => {
    // Arrange
    api.listarPendientes.and.returnValue(
      of<any>({
        data: {
          pendientes: [
            { idnotificaciondespacho: 1, idaccidente: 'ACC-1', idseveridad: 3, estadonotificacion: 'Pendiente', idunidademergencia: 1, unidademergencia: 'Ambulancia 01', fechahora: Date.now() },
            { idnotificaciondespacho: 2, idaccidente: 'ACC-2', idseveridad: 2, estadonotificacion: 'Pendiente', idunidademergencia: 1, unidademergencia: 'Ambulancia 01', fechahora: Date.now() },
          ],
        },
        meta: {},
      }),
    );
    fixture.componentInstance.cargar();

    // Act
    fixture.componentInstance.promoverAlFrente(2);

    // Assert
    expect(fixture.componentInstance.incidenteActivo()?.idnotificaciondespacho).toBe(2);
    expect(fixture.componentInstance.colaPendientes().map((p) => p.idnotificaciondespacho)).toEqual([1]);
  });

  it('restanteMs_starts_near_default_timeout_for_a_freshly_notified_incidente', () => {
    // Assert — arranca cerca de 90s (timeout default) para un incidente recién notificado
    const inicial = fixture.componentInstance.restanteMs();
    expect(inicial).not.toBeNull();
    expect(inicial!).toBeGreaterThan(85_000);
    expect(inicial!).toBeLessThanOrEqual(90_000);
  });

  it('restanteMs_is_null_when_no_hay_incidente_activo', () => {
    // Arrange
    api.listarPendientes.and.returnValue(of<any>({ data: { pendientes: [] }, meta: {} }));

    // Act
    fixture.componentInstance.cargar();

    // Assert
    expect(fixture.componentInstance.restanteMs()).toBeNull();
  });
});
