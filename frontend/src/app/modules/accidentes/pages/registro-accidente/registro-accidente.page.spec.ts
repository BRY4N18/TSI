/** @marker unit */
import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { HttpErrorResponse } from '@angular/common/http';
import { of, throwError } from 'rxjs';

import { NotificationService } from '../../../../shared/notifications/notification.service';
import { AccidenteApiService } from '../../services/accidente-api.service';
import { GeocodificacionApiService } from '../../services/geocodificacion-api.service';
import { UbicacionCatalogoApiService } from '../../services/ubicacion-catalogo-api.service';
import { RegistroAccidentePage } from './registro-accidente.page';

function fillRequiredFields(component: RegistroAccidentePage): void {
  component.form.setValue({
    latitudinicio: 19.4326,
    longitudinicio: -99.1332,
    fechahoraaccidente: '2026-07-12T10:00',
    idseveridad: 2,
    descripcion: 'Choque leve',
    idcalle: 5,
    codigopostal: '',
    numvehiculos: 0,
    numheridos: 0,
    numvictimas: 0,
    numfallecidos: 0,
    idtiporeportado: null,
    registroRetrospectivo: false,
    justificacionRetrospectiva: '',
  });
}

describe('RegistroAccidentePage', () => {
  let fixture: ComponentFixture<RegistroAccidentePage>;
  let component: RegistroAccidentePage;
  let accidenteApi: jasmine.SpyObj<AccidenteApiService>;
  let geoApi: jasmine.SpyObj<GeocodificacionApiService>;
  let catalogoApi: jasmine.SpyObj<UbicacionCatalogoApiService>;
  let notifications: NotificationService;

  beforeEach(async () => {
    accidenteApi = jasmine.createSpyObj('AccidenteApiService', [
      'registrar',
      'confirmarReporte',
      'fusionar',
    ]);
    geoApi = jasmine.createSpyObj('GeocodificacionApiService', ['sugerir']);
    geoApi.sugerir.and.returnValue(
      of<any>({ data: { idcalle: 5, en_cobertura_operativa: true, ubicacion: {} }, meta: {} }),
    );
    catalogoApi = jasmine.createSpyObj('UbicacionCatalogoApiService', [
      'listarPaises',
      'listarEstados',
      'listarCondados',
      'listarCiudades',
      'listarCalles',
    ]);
    catalogoApi.listarPaises.and.returnValue(of([]));

    await TestBed.configureTestingModule({
      imports: [RegistroAccidentePage],
      providers: [
        { provide: AccidenteApiService, useValue: accidenteApi },
        { provide: GeocodificacionApiService, useValue: geoApi },
        { provide: UbicacionCatalogoApiService, useValue: catalogoApi },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(RegistroAccidentePage);
    component = fixture.componentInstance;
    notifications = TestBed.inject(NotificationService);
    fixture.detectChanges();
  });

  it('onCoordsChange_updates_form_and_debounces_geocodificacion', () => {
    // Arrange
    jasmine.clock().install();

    // Act
    component.onCoordsChange({ lat: 19.4326, lng: -99.1332 });

    // Assert: coords applied immediately, geocoding not yet called
    expect(component.form.controls.latitudinicio.value).toBe(19.4326);
    expect(component.form.controls.longitudinicio.value).toBe(-99.1332);
    expect(geoApi.sugerir).not.toHaveBeenCalled();

    // Act: advance past the debounce window
    jasmine.clock().tick(600);

    // Assert
    expect(geoApi.sugerir).toHaveBeenCalledWith(19.4326, -99.1332);
    expect(component.calleSugerida()).toBe(5);
    expect(component.form.controls.idcalle.value).toBe(5);
    expect(component.fueraCobertura()).toBe(false);

    jasmine.clock().uninstall();
  });

  it('registrar_when_form_invalid_does_not_call_api', () => {
    // Act
    component.registrar(false);

    // Assert
    expect(accidenteApi.registrar).not.toHaveBeenCalled();
  });

  it('registrar_when_success_shows_estado_message', () => {
    // Arrange
    fillRequiredFields(component);
    accidenteApi.registrar.and.returnValue(
      of<any>({
        data: { idaccidente: 'ACC-1', estado: 'REPORTADO', advertencias: [] },
        meta: {},
      }),
    );

    // Act
    component.registrar(false);

    // Assert
    expect(notifications.toasts()).toEqual([
      jasmine.objectContaining({ message: 'Accidente registrado (ACC-1)', tone: 'success' }),
    ]);
    expect(component.advertencias()).toEqual([]);
  });

  it('registrar_when_warnings_returned_keeps_borrador_and_lists_advertencias', () => {
    // Arrange
    fillRequiredFields(component);
    accidenteApi.registrar.and.returnValue(
      of<any>({
        data: {
          idaccidente: 'ACC-2',
          estado: 'BORRADOR',
          advertencias: [{ code: 'fuera_cobertura', detail: 'Fuera de cobertura' }],
        },
        meta: {},
      }),
    );

    // Act
    component.registrar(true);

    // Assert
    expect(component.advertencias().length).toBe(1);
    expect(notifications.toasts()).toEqual([
      jasmine.objectContaining({ message: 'Accidente registrado (ACC-2)', tone: 'success' }),
    ]);
  });

  it('registrar_when_duplicado_conflict_opens_dialog', () => {
    // Arrange
    fillRequiredFields(component);
    const conflictBody = {
      error: 'conflict',
      detail: 'Posible duplicado',
      code: 'duplicado_posible',
      idaccidente_similar: 'ACC-9',
      idaccidente_principal_sugerido: 'ACC-9',
      idaccidente_duplicado_sugerido: 'ACC-10',
    };
    accidenteApi.registrar.and.returnValue(
      throwError(() => new HttpErrorResponse({ status: 409, error: conflictBody })),
    );

    // Act
    component.registrar(false);

    // Assert
    expect(component.duplicadoConflicto()).toEqual(conflictBody as any);
  });

  it('registrar_when_api_error_shows_error_message', () => {
    // Arrange
    fillRequiredFields(component);
    accidenteApi.registrar.and.returnValue(
      throwError(() => new HttpErrorResponse({ status: 500, error: {} })),
    );

    // Act
    component.registrar(false);

    // Assert
    expect(notifications.activeAlert()).toEqual(
      jasmine.objectContaining({ title: 'Error al registrar' }),
    );
  });

  it('confirmarFusion_calls_fusionar_with_selected_principal', () => {
    // Arrange
    component.duplicadoConflicto.set({
      error: 'conflict',
      detail: 'Posible duplicado',
      code: 'duplicado_posible',
      idaccidente_similar: 'ACC-9',
      idaccidente_principal_sugerido: 'ACC-9',
      idaccidente_duplicado_sugerido: 'ACC-10',
    });
    accidenteApi.fusionar.and.returnValue(
      of<any>({
        data: {
          message: 'Reportes fusionados exitosamente',
          idaccidente_duplicado: 'ACC-10',
          idaccidente_principal: 'ACC-9',
          estado_duplicado: 'FUSIONADO',
        },
        meta: {},
      }),
    );

    // Act
    component.confirmarFusion('ACC-9');

    // Assert
    expect(accidenteApi.fusionar).toHaveBeenCalledWith('ACC-10', {
      idaccidenteprincipal: 'ACC-9',
      confirmacion: true,
    });
    expect(notifications.toasts()).toEqual([
      jasmine.objectContaining({ message: 'Reportes fusionados exitosamente', tone: 'success' }),
    ]);
    expect(component.duplicadoConflicto()).toBeNull();
  });

  it('confirmarBorrador_when_no_borrador_pending_does_nothing', () => {
    // Act
    component.confirmarBorrador();

    // Assert
    expect(accidenteApi.confirmarReporte).not.toHaveBeenCalled();
  });

  it('confirmarBorrador_when_borrador_pending_confirms_and_clears_advertencias', () => {
    // Arrange
    fillRequiredFields(component);
    accidenteApi.registrar.and.returnValue(
      of<any>({ data: { idaccidente: 'ACC-3', estado: 'BORRADOR', advertencias: [] }, meta: {} }),
    );
    accidenteApi.confirmarReporte.and.returnValue(
      of<any>({ data: { message: 'Confirmado' }, meta: {} }),
    );
    component.registrar(false);

    // Act
    component.confirmarBorrador();

    // Assert
    expect(accidenteApi.confirmarReporte).toHaveBeenCalledWith('ACC-3', { confirmacion: true });
    expect(notifications.toasts()).toEqual([
      jasmine.objectContaining({ message: 'Accidente registrado (ACC-3)', tone: 'success' }),
      jasmine.objectContaining({ message: 'Confirmado', tone: 'success' }),
    ]);
    expect(component.advertencias()).toEqual([]);
  });

  describe('RNF-REG-006 — resiliencia de captura ante interrupción de red', () => {
    const DRAFT_KEY = 'tsi.registro-accidente.draft';

    afterEach(() => localStorage.removeItem(DRAFT_KEY));

    it(
      'autoguarda_el_formulario_en_localStorage_tras_el_debounce',
      fakeAsync(() => {
        // Act
        component.form.controls.descripcion.setValue('Choque en avenida principal');
        tick(600);

        // Assert
        const raw = localStorage.getItem(DRAFT_KEY);
        expect(raw).not.toBeNull();
        expect(JSON.parse(raw!).descripcion).toBe('Choque en avenida principal');
      }),
    );

    it('restaura_el_borrador_guardado_al_crear_una_nueva_instancia', () => {
      // Arrange
      localStorage.setItem(
        DRAFT_KEY,
        JSON.stringify({ ...component.form.getRawValue(), descripcion: 'Borrador previo' }),
      );
      const newFixture = TestBed.createComponent(RegistroAccidentePage);

      // Act
      newFixture.detectChanges();

      // Assert
      expect(newFixture.componentInstance.draftRestored()).toBe(true);
      expect(newFixture.componentInstance.form.controls.descripcion.value).toBe('Borrador previo');
    });

    it('limpia_el_borrador_al_registrar_exitosamente_sin_advertencias', () => {
      // Arrange
      fillRequiredFields(component);
      localStorage.setItem(DRAFT_KEY, JSON.stringify(component.form.getRawValue()));
      accidenteApi.registrar.and.returnValue(
        of<any>({ data: { idaccidente: 'ACC-9', estado: 'REPORTADO', advertencias: [] }, meta: {} }),
      );

      // Act
      component.registrar(false);

      // Assert
      expect(localStorage.getItem(DRAFT_KEY)).toBeNull();
    });

    it(
      'syncStatus_reacciona_a_los_eventos_online_y_offline',
      fakeAsync(() => {
        // Act
        window.dispatchEvent(new Event('offline'));

        // Assert
        expect(component.syncStatus()).toBe('offline');

        // Act
        window.dispatchEvent(new Event('online'));

        // Assert: pasa por "reconnecting" antes de volver a "live"
        expect(component.syncStatus()).toBe('reconnecting');
        tick(1100);
        expect(component.syncStatus()).toBe('live');
      }),
    );
  });
});
