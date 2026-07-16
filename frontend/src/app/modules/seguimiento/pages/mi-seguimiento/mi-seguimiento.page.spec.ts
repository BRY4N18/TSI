/** @marker unit */
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { of, throwError } from 'rxjs';

import { NotificationService } from '../../../../shared/notifications/notification.service';
import { MiSeguimientoApiService } from '../../services/mi-seguimiento-api.service';
import { MiSeguimientoPage } from './mi-seguimiento.page';

const DESPACHO_CONFIRMADO = {
  iddespacho: 42,
  idaccidente: 'ACC-1',
  idunidademergencia: 1,
  estado_despacho: 'Confirmado' as const,
};

describe('MiSeguimientoPage', () => {
  let fixture: ComponentFixture<MiSeguimientoPage>;
  let api: jasmine.SpyObj<MiSeguimientoApiService>;
  let notifications: jasmine.SpyObj<NotificationService>;
  let router: jasmine.SpyObj<Router>;
  let watchPositionSpy: jasmine.Spy;
  let clearWatchSpy: jasmine.Spy;
  let successCallback: PositionCallback | null;
  let errorCallback: PositionErrorCallback | null;

  function fakePosition(latitud: number, longitud: number): GeolocationPosition {
    return {
      coords: {
        latitude: latitud,
        longitude: longitud,
        accuracy: 5,
        altitude: null,
        altitudeAccuracy: null,
        heading: null,
        speed: null,
      },
      timestamp: Date.now(),
    } as GeolocationPosition;
  }

  async function setup(despacho: typeof DESPACHO_CONFIRMADO | null): Promise<void> {
    successCallback = null;
    errorCallback = null;
    watchPositionSpy = spyOn(navigator.geolocation, 'watchPosition').and.callFake(
      (success: PositionCallback, error?: PositionErrorCallback | null) => {
        successCallback = success;
        errorCallback = error ?? null;
        return 1;
      },
    );
    clearWatchSpy = spyOn(navigator.geolocation, 'clearWatch');

    api = jasmine.createSpyObj('MiSeguimientoApiService', [
      'obtenerActual',
      'registrarPosicion',
      'registrarLlegada',
      'abortarMision',
    ]);
    api.obtenerActual.and.returnValue(of<any>({ data: { despacho }, meta: {} }));
    api.registrarPosicion.and.returnValue(of<any>({ data: {}, meta: {} }));
    notifications = jasmine.createSpyObj('NotificationService', ['toast', 'alert']);
    router = jasmine.createSpyObj('Router', ['navigate']);

    await TestBed.configureTestingModule({
      imports: [MiSeguimientoPage],
      providers: [
        { provide: MiSeguimientoApiService, useValue: api },
        { provide: NotificationService, useValue: notifications },
        { provide: Router, useValue: router },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(MiSeguimientoPage);
    fixture.detectChanges();
  }

  describe('con despacho activo', () => {
    beforeEach(() => setup(DESPACHO_CONFIRMADO));

    it('ngOnInit_loads_actual_and_starts_gps_watch', () => {
      expect(api.obtenerActual).toHaveBeenCalled();
      expect(watchPositionSpy).toHaveBeenCalled();
      expect(fixture.componentInstance.despacho()).toEqual(DESPACHO_CONFIRMADO);
    });

    it('onPosicion_sends_registrarPosicion_with_despacho_data', () => {
      successCallback!(fakePosition(19.4, -99.1));

      expect(api.registrarPosicion).toHaveBeenCalledWith(
        jasmine.objectContaining({
          idunidademergencia: 1,
          idaccidente: 'ACC-1',
          latitud: 19.4,
          longitud: -99.1,
        }),
        jasmine.any(String),
      );
    });

    it('onPosicion_throttles_consecutive_updates_within_10_seconds', () => {
      successCallback!(fakePosition(19.4, -99.1));
      successCallback!(fakePosition(19.41, -99.11));

      expect(api.registrarPosicion).toHaveBeenCalledTimes(1);
    });

    it('gps_permission_denied_sets_gpsError', () => {
      errorCallback!({ code: 1, message: 'denied' } as GeolocationPositionError);

      expect(fixture.componentInstance.gpsError()).toBeTruthy();
    });

    it('reintentarGps_restarts_watch', () => {
      watchPositionSpy.calls.reset();

      fixture.componentInstance.reintentarGps();

      expect(watchPositionSpy).toHaveBeenCalled();
    });

    it('ngOnDestroy_clears_gps_watch', () => {
      fixture.destroy();

      expect(clearWatchSpy).toHaveBeenCalledWith(1);
    });

    it('registrarLlegada_when_success_sets_en_sitio_and_stops_gps', () => {
      api.registrarLlegada.and.returnValue(of<any>({ data: {}, meta: {} }));

      fixture.componentInstance.registrarLlegada();

      expect(api.registrarLlegada).toHaveBeenCalledWith(42, jasmine.any(String));
      expect(fixture.componentInstance.estado()).toBe('en_sitio');
      expect(clearWatchSpy).toHaveBeenCalled();
      expect(notifications.toast).toHaveBeenCalled();
    });

    it('registrarLlegada_when_error_sets_apiError', () => {
      api.registrarLlegada.and.returnValue(throwError(() => new Error('fail')));

      fixture.componentInstance.registrarLlegada();

      expect(fixture.componentInstance.apiError()).toBeTruthy();
      expect(fixture.componentInstance.registrandoLlegada()).toBeFalse();
    });

    it('iniciarAbortar_opens_confirmation_panel', () => {
      fixture.componentInstance.iniciarAbortar();

      expect(fixture.componentInstance.confirmandoAbortar()).toBeTrue();
    });

    it('cancelarAbortar_closes_panel_without_calling_api', () => {
      fixture.componentInstance.iniciarAbortar();

      fixture.componentInstance.cancelarAbortar();

      expect(fixture.componentInstance.confirmandoAbortar()).toBeFalse();
      expect(api.abortarMision).not.toHaveBeenCalled();
    });

    it('confirmarAbortar_when_success_sets_abortada_and_navigates', () => {
      api.abortarMision.and.returnValue(of<any>({ data: {}, meta: {} }));
      fixture.componentInstance.iniciarAbortar();
      fixture.componentInstance.motivoAbortar = 'Falsa alarma';

      fixture.componentInstance.confirmarAbortar();

      expect(api.abortarMision).toHaveBeenCalledWith(
        42,
        { motivo: 'Falsa alarma' },
        jasmine.any(String),
      );
      expect(fixture.componentInstance.estado()).toBe('abortada');
      expect(router.navigate).toHaveBeenCalledWith(['/despacho/mi-despacho']);
    });

    it('confirmarAbortar_when_error_sets_apiError', () => {
      api.abortarMision.and.returnValue(throwError(() => new Error('fail')));
      fixture.componentInstance.iniciarAbortar();

      fixture.componentInstance.confirmarAbortar();

      expect(fixture.componentInstance.apiError()).toBeTruthy();
      expect(fixture.componentInstance.abortando()).toBeFalse();
    });
  });

  describe('sin despacho activo', () => {
    beforeEach(() => setup(null));

    it('does_not_start_gps_watch_and_leaves_despacho_null', () => {
      expect(watchPositionSpy).not.toHaveBeenCalled();
      expect(fixture.componentInstance.despacho()).toBeNull();
    });

    it('registrarLlegada_is_a_noop_without_despacho', () => {
      fixture.componentInstance.registrarLlegada();

      expect(api.registrarLlegada).not.toHaveBeenCalled();
    });
  });

  describe('cuando obtenerActual falla', () => {
    beforeEach(async () => {
      watchPositionSpy = spyOn(navigator.geolocation, 'watchPosition');
      api = jasmine.createSpyObj('MiSeguimientoApiService', [
        'obtenerActual',
        'registrarPosicion',
        'registrarLlegada',
        'abortarMision',
      ]);
      api.obtenerActual.and.returnValue(throwError(() => new Error('fail')));

      await TestBed.configureTestingModule({
        imports: [MiSeguimientoPage],
        providers: [
          { provide: MiSeguimientoApiService, useValue: api },
          { provide: NotificationService, useValue: jasmine.createSpyObj('NotificationService', ['toast', 'alert']) },
          { provide: Router, useValue: jasmine.createSpyObj('Router', ['navigate']) },
        ],
      }).compileComponents();

      fixture = TestBed.createComponent(MiSeguimientoPage);
      fixture.detectChanges();
    });

    it('sets_apiError_and_stops_loading', () => {
      expect(fixture.componentInstance.apiError()).toBeTruthy();
      expect(fixture.componentInstance.cargando()).toBeFalse();
    });
  });
});
