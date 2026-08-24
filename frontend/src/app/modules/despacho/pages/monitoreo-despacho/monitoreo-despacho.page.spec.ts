/** @marker unit */
import { HttpErrorResponse } from '@angular/common/http';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute } from '@angular/router';
import { of, throwError } from 'rxjs';

import { ConfirmDialogService } from '../../../../shared/notifications/confirm-dialog.service';
import { NotificationService } from '../../../../shared/notifications/notification.service';
import { SeguimientoApiService } from '../../../seguimiento/services/seguimiento-api.service';
import { DespachoApiService } from '../../services/despacho-api.service';
import { DespachoSseService } from '../../services/despacho-sse.service';
import { MonitoreoDespachoPage } from './monitoreo-despacho.page';

const ESTADO_EN_ATENCION = {
  idaccidente: 'ACC-1',
  estado_caso: 'EN_ATENCIÓN',
  tiempo_transcurrido_seg: 60,
  intentos: [],
  unidades_activas: [
    {
      iddespacho: 10,
      idunidademergencia: 1,
      unidademergencia: 'Ambulancia 01',
      tipounidademergencia: 'Ambulancia',
      estado: 'En_sitio',
      origen: 'Automatico',
    },
  ],
};

describe('MonitoreoDespachoPage — cierre del caso (SRS §3.6.4)', () => {
  let fixture: ComponentFixture<MonitoreoDespachoPage>;
  let seguimiento: jasmine.SpyObj<SeguimientoApiService>;
  let dialog: jasmine.SpyObj<ConfirmDialogService>;
  let notifications: jasmine.SpyObj<NotificationService>;

  beforeEach(async () => {
    const api = jasmine.createSpyObj('DespachoApiService', ['obtenerEstado']);
    api.obtenerEstado.and.returnValue(of({ data: ESTADO_EN_ATENCION, meta: {} }) as never);
    const sse = jasmine.createSpyObj('DespachoSseService', ['streamDespacho', 'streamResiliente']);
    sse.streamDespacho.and.returnValue(of());
    // La página usa `streamResiliente` desde PG-UI-005: el stream crudo dejaba
    // la vista muerta tras el primer corte y en «En vivo» tras un cierre limpio.
    sse.streamResiliente.and.returnValue(of());
    seguimiento = jasmine.createSpyObj('SeguimientoApiService', [
      'cerrarCaso',
      'cancelarCaso',
      'forzarRetiro',
    ]);
    dialog = jasmine.createSpyObj('ConfirmDialogService', ['confirm']);
    dialog.confirm.and.returnValue(Promise.resolve(true));
    notifications = jasmine.createSpyObj('NotificationService', ['toast', 'alert']);

    await TestBed.configureTestingModule({
      imports: [MonitoreoDespachoPage],
      providers: [
        { provide: DespachoApiService, useValue: api },
        { provide: DespachoSseService, useValue: sse },
        { provide: SeguimientoApiService, useValue: seguimiento },
        { provide: ConfirmDialogService, useValue: dialog },
        { provide: NotificationService, useValue: notifications },
        {
          provide: ActivatedRoute,
          useValue: { snapshot: { paramMap: { get: () => 'ACC-1' } } },
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(MonitoreoDespachoPage);
    fixture.detectChanges();
  });

  it('muestra el motivo real cuando el backend rechaza el cierre', async () => {
    // Arrange — el caso no puede cerrarse si queda una unidad sin retirarse;
    // el operador tiene que leer por qué, no un error genérico.
    const detalle = 'No se puede cerrar: 1 unidad(es) siguen sin retirarse.';
    seguimiento.cerrarCaso.and.returnValue(
      throwError(() => new HttpErrorResponse({ status: 409, error: { detail: detalle } })),
    );
    fixture.componentInstance.resultadoAtencion = 'Atención completada';

    // Act
    await fixture.componentInstance.cerrarCaso();

    // Assert
    expect(fixture.componentInstance.cierreError()).toBe(detalle);
  });

  it('exige el resultado de la atención antes de llamar al backend', async () => {
    // Arrange
    fixture.componentInstance.resultadoAtencion = '   ';

    // Act
    await fixture.componentInstance.cerrarCaso();

    // Assert
    expect(seguimiento.cerrarCaso).not.toHaveBeenCalled();
    expect(fixture.componentInstance.cierreError()).toContain('resultado');
  });

  it('avisa de que el retiro forzado queda registrado como tal', async () => {
    // Arrange
    seguimiento.forzarRetiro.and.returnValue(
      of({ data: { caso_cerrado: false }, meta: {} }) as never,
    );

    // Act
    await fixture.componentInstance.forzarRetiro(10, 'Ambulancia 01');

    // Assert — el aviso previo debe decir que no es una finalización normal
    const request = dialog.confirm.calls.mostRecent().args[0];
    expect(request.message).toContain('forzado');
    expect(request.tone).toBe('danger');
    expect(seguimiento.forzarRetiro).toHaveBeenCalledWith(10);
  });

  it('solo ofrece forzar el retiro de unidades que siguen en el caso', () => {
    // Arrange / Act / Assert
    expect(fixture.componentInstance.esRetirable('En_sitio')).toBeTrue();
    expect(fixture.componentInstance.esRetirable('Confirmado')).toBeTrue();
    expect(fixture.componentInstance.esRetirable('Retirado')).toBeFalse();
    expect(fixture.componentInstance.esRetirable('Timeout')).toBeFalse();
  });
});
