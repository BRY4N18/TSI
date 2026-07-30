/** @marker unit */
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { convertToParamMap, ActivatedRoute } from '@angular/router';
import { of, throwError } from 'rxjs';

import { NotificationService } from '../../../../shared/notifications/notification.service';
import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';
import { AccidenteApiService } from '../../services/accidente-api.service';
import { EvidenciaApiService } from '../../../evidencia-unidad/services/evidencia-api.service';
import { DespachoApiService } from '../../../despacho/services/despacho-api.service';
import { UbicacionCatalogoApiService } from '../../services/ubicacion-catalogo-api.service';
import { DetalleAccidentePage } from './detalle-accidente.page';

describe('DetalleAccidentePage', () => {
  let fixture: ComponentFixture<DetalleAccidentePage>;
  let api: jasmine.SpyObj<AccidenteApiService>;
  let evidenciaApi: jasmine.SpyObj<EvidenciaApiService>;
  let despachoApi: jasmine.SpyObj<DespachoApiService>;
  let authApi: jasmine.SpyObj<AuthApiService>;
  let notifications: NotificationService;

  const detalleBase = {
    idaccidente: 'ACC-1',
    estado_actual: 'REGISTRADO',
    descripcion: 'Choque',
    numvehiculos: 2,
    historial_estados: [],
  };

  async function setup(query: Record<string, string> = {}): Promise<void> {
    api = jasmine.createSpyObj('AccidenteApiService', [
      'detalle',
      'actualizar',
      'descartar',
      'deshacerDescarte',
      'escalarSeveridad',
    ]);
    api.detalle.and.returnValue(of<any>({ data: detalleBase, meta: {} }));

    evidenciaApi = jasmine.createSpyObj('EvidenciaApiService', ['listarServidor', 'isFotoItem']);
    evidenciaApi.listarServidor.and.returnValue(of<any>({ data: { items: [] }, meta: {} }));
    evidenciaApi.isFotoItem.and.callFake((item: any): item is any => item?.tipo === 'foto');

    despachoApi = jasmine.createSpyObj('DespachoApiService', ['obtenerEstado']);
    despachoApi.obtenerEstado.and.returnValue(
      of<any>({ data: { unidades_activas: [], intentos: [] }, meta: {} }),
    );

    authApi = jasmine.createSpyObj('AuthApiService', ['hasAnyRole']);
    authApi.hasAnyRole.and.returnValue(true);

    const catalogoApi = jasmine.createSpyObj('UbicacionCatalogoApiService', [
      'listarUnidadesEmergencia',
    ]);
    catalogoApi.listarUnidadesEmergencia.and.returnValue(
      of([
        { id: 1, nombre: 'Ambulancia 01' },
        { id: 2, nombre: 'Grúa 02' },
      ]),
    );

    await TestBed.configureTestingModule({
      imports: [DetalleAccidentePage],
      providers: [
        { provide: AccidenteApiService, useValue: api },
        { provide: EvidenciaApiService, useValue: evidenciaApi },
        { provide: DespachoApiService, useValue: despachoApi },
        { provide: AuthApiService, useValue: authApi },
        { provide: UbicacionCatalogoApiService, useValue: catalogoApi },
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: {
              paramMap: convertToParamMap({ idaccidente: 'ACC-1' }),
              queryParamMap: convertToParamMap(query),
            },
          },
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(DetalleAccidentePage);
    notifications = TestBed.inject(NotificationService);
    fixture.detectChanges();
  }

  beforeEach(async () => {
    await setup();
  });

  it('ngOnInit_loads_accidente_detail', () => {
    // Assert
    expect(api.detalle).toHaveBeenCalledWith('ACC-1');
    expect(fixture.componentInstance.accidente()?.idaccidente).toBe('ACC-1');
    expect(fixture.componentInstance.numvehiculos).toBe(2);
  });

  it('modo_detalles_muestra_titulo_sin_guardar', () => {
    // Assert
    expect(fixture.componentInstance.tituloModo()).toBe('Detalles');
    expect(fixture.componentInstance.esModoEditar()).toBe(false);
    const titulo = fixture.nativeElement.querySelector('[data-testid="modo-titulo"]');
    expect(titulo?.textContent?.trim()).toBe('Detalles');
    expect(fixture.nativeElement.querySelector('[data-testid="btn-save-header"]')).toBeNull();
    const input = fixture.nativeElement.querySelector('#numvehiculos') as HTMLInputElement | null;
    expect(input?.disabled).toBe(true);
    expect(fixture.nativeElement.querySelector('[data-testid="link-ver-siniestro"]')).not.toBeNull();
    expect((fixture.nativeElement as HTMLElement).textContent).not.toContain('Completar en sitio');
  });

  it('guardar_en_modo_detalles_no_llama_api', () => {
    // Act
    fixture.componentInstance.guardar();

    // Assert
    expect(api.actualizar).not.toHaveBeenCalled();
  });

  it('btn_save_header_visible_solo_en_modo_editar', async () => {
    // Arrange
    TestBed.resetTestingModule();
    await setup({ focus: 'edit' });

    // Assert
    expect(fixture.componentInstance.tituloModo()).toBe('Editar caso');
    const btn = fixture.nativeElement.querySelector('[data-testid="btn-save-header"]');
    expect(btn).not.toBeNull();
    expect(btn.textContent).toContain('Guardar cambios');
    const input = fixture.nativeElement.querySelector('#numvehiculos') as HTMLInputElement | null;
    expect(input?.disabled).toBe(false);
  });

  it('guardar_updates_and_reloads', async () => {
    // Arrange
    TestBed.resetTestingModule();
    await setup({ focus: 'edit' });
    api.actualizar.and.returnValue(of<any>({ data: { message: 'ok' }, meta: {} }));
    fixture.componentInstance.numvehiculos = 3;

    // Act
    fixture.componentInstance.guardar();

    // Assert
    expect(api.actualizar).toHaveBeenCalledWith('ACC-1', {
      numvehiculos: 3,
      numheridos: 0,
      numfallecidos: 0,
      descripcion: 'Choque',
    });
    expect(notifications.toasts()).toEqual([
      jasmine.objectContaining({ message: 'Actualizado', tone: 'success' }),
    ]);
    expect(api.detalle).toHaveBeenCalledTimes(2);
    expect(fixture.componentInstance.saving()).toBe(false);
  });

  it('guardar_on_error_keeps_form_values_and_alerts', async () => {
    // Arrange
    TestBed.resetTestingModule();
    await setup({ focus: 'edit' });
    api.actualizar.and.returnValue(throwError(() => ({ error: { detail: 'fallo' } })));
    fixture.componentInstance.numvehiculos = 9;
    fixture.componentInstance.descripcion = 'editado';

    // Act
    fixture.componentInstance.guardar();

    // Assert
    expect(fixture.componentInstance.numvehiculos).toBe(9);
    expect(fixture.componentInstance.descripcion).toBe('editado');
    expect(notifications.activeAlert()?.message).toContain('fallo');
    expect(fixture.componentInstance.saving()).toBe(false);
  });

  it('focus_edit_query_sets_focusEdit_flag', async () => {
    // Arrange
    TestBed.resetTestingModule();
    await setup({ focus: 'edit' });

    // Assert
    expect(fixture.componentInstance.focusEdit()).toBe(true);
  });

  it('ngOnInit_when_tecnico_role_does_not_load_despacho', () => {
    // Arrange
    despachoApi.obtenerEstado.calls.reset();
    authApi.hasAnyRole.and.returnValue(false);

    // Act
    fixture.componentInstance.cargar();

    // Assert
    expect(despachoApi.obtenerEstado).not.toHaveBeenCalled();
    expect(fixture.componentInstance.puedeVerDespacho()).toBe(false);
  });

  it('descartar_discards_case_and_reloads', () => {
    // Arrange
    api.descartar.and.returnValue(of<any>({ data: { message: 'ok' }, meta: {} }));

    // Act
    fixture.componentInstance.descartar();

    // Assert
    expect(api.descartar).toHaveBeenCalledWith('ACC-1', { motivo: 'Descartado por operador' });
    expect(notifications.toasts()).toEqual([
      jasmine.objectContaining({
        message: 'Caso descartado',
        tone: 'success',
        actionLabel: 'Deshacer',
      }),
    ]);
  });
});
