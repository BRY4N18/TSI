/** @marker unit */
import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of, throwError } from 'rxjs';

import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';
import { AccidenteApiService } from '../../services/accidente-api.service';
import { UbicacionCatalogoApiService } from '../../services/ubicacion-catalogo-api.service';
import { ListaAccidentesPage } from './lista-accidentes.page';

describe('ListaAccidentesPage', () => {
  let fixture: ComponentFixture<ListaAccidentesPage>;
  let component: ListaAccidentesPage;
  let api: jasmine.SpyObj<AccidenteApiService>;
  let ubicacionCatalogo: jasmine.SpyObj<UbicacionCatalogoApiService>;
  let authApi: jasmine.SpyObj<AuthApiService>;

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

    await TestBed.configureTestingModule({
      imports: [ListaAccidentesPage],
      providers: [
        { provide: AccidenteApiService, useValue: api },
        { provide: UbicacionCatalogoApiService, useValue: ubicacionCatalogo },
        { provide: AuthApiService, useValue: authApi },
        provideRouter([]),
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(ListaAccidentesPage);
    component = fixture.componentInstance;
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
});
