/** @marker unit */
import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { of, throwError } from 'rxjs';

import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';
import { ListaSeleccionStorage } from '../../lista-seleccion.storage';
import { AccidenteApiService } from '../../services/accidente-api.service';
import { UbicacionCatalogoApiService } from '../../services/ubicacion-catalogo-api.service';
import { ListaAccidentesPage } from './lista-accidentes.page';

describe('ListaAccidentesPage', () => {
  let fixture: ComponentFixture<ListaAccidentesPage>;
  let component: ListaAccidentesPage;
  let api: jasmine.SpyObj<AccidenteApiService>;
  let ubicacionCatalogo: jasmine.SpyObj<UbicacionCatalogoApiService>;
  let authApi: jasmine.SpyObj<AuthApiService>;
  let listaSeleccion: jasmine.SpyObj<ListaSeleccionStorage>;
  let router: Router;

  beforeEach(async () => {
    api = jasmine.createSpyObj('AccidenteApiService', ['listar']);
    api.listar.and.returnValue(of<any>({ data: [], meta: { pagination: null } }));

    ubicacionCatalogo = jasmine.createSpyObj('UbicacionCatalogoApiService', [
      'listarPaises',
      'listarEstados',
    ]);
    ubicacionCatalogo.listarPaises.and.returnValue(of([]));
    ubicacionCatalogo.listarEstados.and.returnValue(of([]));

    authApi = jasmine.createSpyObj('AuthApiService', ['hasAnyRole']);
    authApi.hasAnyRole.and.returnValue(true);

    listaSeleccion = jasmine.createSpyObj('ListaSeleccionStorage', ['get', 'set', 'clear']);
    listaSeleccion.get.and.returnValue(null);

    await TestBed.configureTestingModule({
      imports: [ListaAccidentesPage],
      providers: [
        { provide: AccidenteApiService, useValue: api },
        { provide: UbicacionCatalogoApiService, useValue: ubicacionCatalogo },
        { provide: AuthApiService, useValue: authApi },
        { provide: ListaSeleccionStorage, useValue: listaSeleccion },
        provideRouter([]),
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(ListaAccidentesPage);
    component = fixture.componentInstance;
    router = TestBed.inject(Router);
    spyOn(router, 'navigate').and.resolveTo(true);
  });

  it('ngOnInit_carga_la_lista_al_iniciar', () => {
    // Act
    fixture.detectChanges();

    // Assert
    expect(api.listar).toHaveBeenCalled();
    expect(component.loading()).toBe(false);
  });

  it('cargar_when_success_populates_accidentes', () => {
    // Arrange
    api.listar.and.returnValue(
      of<any>({
        data: [{ idaccidente: 'ACC-1', idseveridad: 2, descripcion: 'x', activo: true, estado_actual: 'REPORTADO' }],
        meta: { pagination: null },
      }),
    );

    // Act
    fixture.detectChanges();

    // Assert
    expect(component.accidentes().length).toBe(1);
    expect(component.accidentes()[0].idaccidente).toBe('ACC-1');
  });

  it('cargar_when_no_hay_datos_muestra_estado_vacio', () => {
    // Act
    fixture.detectChanges();

    // Assert
    expect(component.accidentes().length).toBe(0);
    expect(component.error()).toBeNull();
    const empty = fixture.nativeElement.querySelector('[data-testid="empty-state"]');
    expect(empty).not.toBeNull();
  });

  it('cargar_when_api_error_muestra_estado_de_error', () => {
    // Arrange
    api.listar.and.returnValue(throwError(() => new Error('network')));

    // Act
    fixture.detectChanges();

    // Assert
    expect(component.error()).toBe('No se pudo cargar la lista de accidentes.');
    const error = fixture.nativeElement.querySelector('[data-testid="error-state"]');
    expect(error).not.toBeNull();
  });

  it(
    'cambiar_filtro_de_severidad_recarga_la_lista_tras_el_debounce',
    fakeAsync(() => {
      // Arrange
      fixture.detectChanges();
      api.listar.calls.reset();

      // Act
      component.filtros.controls.idseveridad.setValue(3);
      tick(300);

      // Assert
      expect(api.listar).toHaveBeenCalledWith(
        jasmine.objectContaining({ idseveridad: 3 }),
      );
    }),
  );

  it('severidadInfo_maps_known_severities_to_icon_and_tone', () => {
    // Act & Assert
    expect(component.severidadInfo(1).tone).toBe('success');
    expect(component.severidadInfo(4).tone).toBe('critical');
  });

  it('muestra_id_texto_plano_ojo_y_lapiz_sin_link_en_id', () => {
    // Arrange
    api.listar.and.returnValue(
      of<any>({
        data: [
          {
            idaccidente: 'ACC-1',
            idseveridad: 2,
            descripcion: 'x',
            activo: true,
            estado_actual: 'REPORTADO',
            fechahoraaccidente: Date.now(),
          },
        ],
        meta: { pagination: null },
      }),
    );

    // Act
    fixture.detectChanges();

    // Assert
    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelector('[aria-label="Ver detalles"]')).not.toBeNull();
    expect(el.querySelector('[aria-label="Editar caso"]')).not.toBeNull();
    expect(el.textContent).toContain('ACC-1');
    const idCell = Array.from(el.querySelectorAll('td')).find((td) =>
      (td.textContent ?? '').includes('ACC-1'),
    );
    expect(idCell?.querySelector('a')).toBeNull();
    expect(idCell?.querySelector('.text-accent-primary')).toBeNull();
  });

  it('abrirCaso_edit_persists_lastId_and_navigates_with_focus', () => {
    // Arrange
    fixture.detectChanges();

    // Act
    component.abrirCaso('ACC-9', 'edit');

    // Assert
    expect(listaSeleccion.set).toHaveBeenCalledWith('ACC-9');
    expect(router.navigate).toHaveBeenCalledWith(['/accidentes', 'ACC-9'], {
      queryParams: { focus: 'edit' },
    });
  });

  it('fila_seleccionada_expone_row_selected_cuando_hay_lastId', () => {
    // Arrange
    listaSeleccion.get.and.returnValue('ACC-1');
    api.listar.and.returnValue(
      of<any>({
        data: [
          {
            idaccidente: 'ACC-1',
            idseveridad: 1,
            descripcion: 'a',
            activo: true,
            estado_actual: 'REPORTADO',
            fechahoraaccidente: Date.now(),
          },
        ],
        meta: { pagination: null },
      }),
    );

    // Act
    fixture.detectChanges();

    // Assert
    expect(fixture.nativeElement.querySelector('[data-testid="row-selected"]')).not.toBeNull();
  });

  it('cta_nuevo_registro_visible_cuando_puedeRegistrar', () => {
    // Arrange
    authApi.hasAnyRole.and.returnValue(true);
    fixture.detectChanges();

    // Assert
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Nuevo registro');
    expect(text.toLowerCase()).not.toContain('elementos físicos');
  });
});
