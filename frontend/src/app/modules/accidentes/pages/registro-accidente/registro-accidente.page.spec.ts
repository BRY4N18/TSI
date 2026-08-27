/** @marker unit */
import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { HttpErrorResponse } from '@angular/common/http';
import { of, throwError } from 'rxjs';

import { ConfirmDialogService } from '../../../../shared/notifications/confirm-dialog.service';
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
    // RN-REG-012: obligatorio y >= 1 (de aquí sale el tope de conductores).
    numvehiculos: 2,
    numheridos: 0,
    numvictimas: 0,
    numfallecidos: 0,
    idtiporeportado: null,
    idreferenciaestacion: null,
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
      'deshacerFusion',
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
      'listarTiposReportado',
      'listarReferenciasEstacion',
    ]);
    catalogoApi.listarPaises.and.returnValue(of([]));
    catalogoApi.listarTiposReportado.and.returnValue(
      of([
        { id: 1, nombre: 'Llamada telefónica' },
        { id: 2, nombre: 'App móvil' },
      ]),
    );
    catalogoApi.listarReferenciasEstacion.and.returnValue(
      of([{ id: 1, nombre: 'MEX (America/Mexico_City)' }]),
    );

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
      error: 'duplicado_posible',
      detail: 'Posible duplicado detectado',
      code: '409',
      idaccidente_similar: 'ACC-10',
      idaccidente_principal_sugerido: 'ACC-9',
    };
    accidenteApi.registrar.and.returnValue(
      throwError(() => new HttpErrorResponse({ status: 409, error: { data: conflictBody, meta: {} } })),
    );

    // Act
    component.registrar(false);

    // Assert
    expect(component.duplicadoConflicto()).toEqual(conflictBody as any);
  });

  it('registrar_when_fuera_cobertura_shows_coverage_alert', () => {
    // Arrange
    fillRequiredFields(component);
    const conflictBody = {
      error: 'fuera_cobertura',
      detail: 'Fuera de cobertura operativa',
      code: '409',
      idaccidente_similar: null,
      idaccidente_principal_sugerido: null,
    };
    accidenteApi.registrar.and.returnValue(
      throwError(() => new HttpErrorResponse({ status: 409, error: { data: conflictBody, meta: {} } })),
    );

    // Act
    component.registrar(false);

    // Assert
    expect(component.duplicadoConflicto()).toBeNull();
    expect(notifications.activeAlert()).toEqual(
      jasmine.objectContaining({ title: 'Fuera de cobertura', message: 'Fuera de cobertura operativa' }),
    );
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

  it('registrar_when_validation_error_shows_backend_detail', () => {
    // Arrange — un 400 de validación explica qué corregir; presentarlo como
    // problema de conexión manda al operador a buscar donde no está.
    fillRequiredFields(component);
    accidenteApi.registrar.and.returnValue(
      throwError(
        () =>
          new HttpErrorResponse({
            status: 400,
            error: { error: 'bad_request', detail: 'Fecha futura no permitida', code: '400' },
          }),
      ),
    );

    // Act
    component.registrar(false);

    // Assert
    expect(notifications.activeAlert()?.message).toContain('Fecha futura no permitida');
    expect(notifications.activeAlert()?.message).not.toContain('conexión');
  });

  it('registrar_when_server_error_keeps_connection_message', () => {
    // Arrange — un 500 no le dice nada accionable al operador: ahí sí procede
    // el mensaje genérico.
    fillRequiredFields(component);
    accidenteApi.registrar.and.returnValue(
      throwError(() => new HttpErrorResponse({ status: 500, error: { detail: 'boom' } })),
    );

    // Act
    component.registrar(false);

    // Assert
    expect(notifications.activeAlert()?.message).toContain('conexión');
    expect(notifications.activeAlert()?.message).not.toContain('boom');
  });

  it('confirmarFusion_registra_el_duplicado_y_lo_fusiona_con_el_padre', () => {
    // Arrange — SRS §3.6.1: "el duplicado queda marcado como fusionado y
    // apuntando al caso padre… no se borra". El 409 rechaza el alta, así que el
    // reporte duplicado todavía no existe: hay que registrarlo forzando la
    // advertencia y fusionar **ese** caso, no el que ya estaba registrado.
    fillRequiredFields(component);
    component.duplicadoConflicto.set({
      error: 'duplicado_posible',
      detail: 'Posible duplicado detectado',
      code: '409',
      idaccidente_similar: 'ACC-9',
      idaccidente_principal_sugerido: 'ACC-9',
    });
    accidenteApi.registrar.and.returnValue(
      of<any>({ data: { idaccidente: 'ACC-NUEVO', estado: 'BORRADOR' }, meta: {} }),
    );
    accidenteApi.fusionar.and.returnValue(
      of<any>({
        data: {
          message: 'Reportes fusionados exitosamente',
          idaccidente_duplicado: 'ACC-NUEVO',
          idaccidente_principal: 'ACC-9',
          estado_duplicado: 'FUSIONADO',
        },
        meta: {},
      }),
    );

    // Act
    component.confirmarFusion('ACC-9');

    // Assert — se registra forzando advertencias y se fusiona el caso nuevo
    expect(accidenteApi.registrar).toHaveBeenCalledWith(jasmine.any(Object), true);
    expect(accidenteApi.fusionar).toHaveBeenCalledWith('ACC-NUEVO', {
      idaccidenteprincipal: 'ACC-9',
      confirmacion: true,
    });
    expect(notifications.toasts()).toEqual([
      jasmine.objectContaining({ tone: 'success' }),
    ]);
    expect(component.duplicadoConflicto()).toBeNull();
  });

  it('confirmarFusion_no_marca_como_duplicado_el_caso_ya_registrado', () => {
    // Arrange — el fallo que tenía: fusionaba `idaccidente_similar` (el caso
    // real) contra el id sugerido, que es ese mismo caso. El accidente vivo
    // quedaba apuntándose a sí mismo, desactivado y en FUSIONADO.
    fillRequiredFields(component);
    component.duplicadoConflicto.set({
      error: 'duplicado_posible',
      detail: 'Posible duplicado detectado',
      code: '409',
      idaccidente_similar: 'ACC-9',
      idaccidente_principal_sugerido: 'ACC-9',
    });
    accidenteApi.registrar.and.returnValue(
      of<any>({ data: { idaccidente: 'ACC-NUEVO', estado: 'BORRADOR' }, meta: {} }),
    );
    accidenteApi.fusionar.and.returnValue(
      of<any>({
        data: {
          message: 'Reportes fusionados exitosamente',
          idaccidente_duplicado: 'ACC-NUEVO',
          idaccidente_principal: 'ACC-9',
          estado_duplicado: 'FUSIONADO',
        },
        meta: {},
      }),
    );

    // Act
    component.confirmarFusion('ACC-9');

    // Assert
    expect(accidenteApi.fusionar).not.toHaveBeenCalledWith('ACC-9', jasmine.anything());
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

    it('descartarBorradorLocal_with_confirm_clears_draft_and_resets_form', async () => {
      // Arrange
      const confirmDialog = TestBed.inject(ConfirmDialogService);
      spyOn(confirmDialog, 'confirm').and.resolveTo(true);
      component.form.controls.descripcion.setValue('borrador viejo');
      component.draftRestored.set(true);
      localStorage.setItem(DRAFT_KEY, JSON.stringify(component.form.getRawValue()));

      // Act
      await component.descartarBorradorLocal();

      // Assert
      expect(confirmDialog.confirm).toHaveBeenCalledWith(
        jasmine.objectContaining({ message: '¿Descartar el borrador y empezar de nuevo?' }),
      );
      expect(localStorage.getItem(DRAFT_KEY)).toBeNull();
      expect(component.draftRestored()).toBe(false);
      expect(component.form.controls.descripcion.value).toBe('');
    });

    it('descartarBorradorLocal_when_cancel_keeps_draft', async () => {
      // Arrange
      const confirmDialog = TestBed.inject(ConfirmDialogService);
      spyOn(confirmDialog, 'confirm').and.resolveTo(false);
      component.form.controls.descripcion.setValue('borrador viejo');
      component.draftRestored.set(true);
      localStorage.setItem(DRAFT_KEY, JSON.stringify({ descripcion: 'borrador viejo' }));

      // Act
      await component.descartarBorradorLocal();

      // Assert
      expect(component.draftRestored()).toBe(true);
      expect(component.form.controls.descripcion.value).toBe('borrador viejo');
      expect(localStorage.getItem(DRAFT_KEY)).not.toBeNull();
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
