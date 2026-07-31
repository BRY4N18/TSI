/** @marker unit */
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { of, throwError, TimeoutError } from 'rxjs';

import { NotificationService } from '../../../../../shared/notifications/notification.service';
import { ListaSeleccionStorage } from '../../lista-seleccion.storage';
import { UnidadEmergenciaFacadeService } from '../../services/unidad-emergencia-facade.service';
import { CatalogoPage } from './catalogo.page';

describe('CatalogoPage (alta-unidades lista)', () => {
  let fixture: ComponentFixture<CatalogoPage>;
  let component: CatalogoPage;
  let facade: jasmine.SpyObj<UnidadEmergenciaFacadeService>;
  let listaSeleccion: jasmine.SpyObj<ListaSeleccionStorage>;
  let router: Router;

  const unidad = {
    idunidademergencia: 7,
    idcliente: 1,
    idcondado: 10,
    tipopropiedad: 'Externa' as const,
    placa: 'ABC-123',
    capacidad: null,
    contactoproveedor: 'x',
    unidademergencia: 'Ambulancia 1',
    tipounidademergencia: 'Ambulancia' as const,
    activo: true,
    latitud: null,
    longitud: null,
  };

  const listPage = {
    items: [unidad],
    pagination: { next_cursor: 7 as number | null, limit: 20 },
  };

  beforeEach(async () => {
    facade = jasmine.createSpyObj('UnidadEmergenciaFacadeService', [
      'listar',
      'obtener',
      'registrar',
      'editar',
      'darDeBaja',
      'reactivar',
      'importarLote',
    ]);
    facade.listar.and.returnValue(of({ ok: true, data: listPage }));

    listaSeleccion = jasmine.createSpyObj('ListaSeleccionStorage', ['get', 'set', 'clear']);
    listaSeleccion.get.and.returnValue(null);

    await TestBed.configureTestingModule({
      imports: [CatalogoPage],
      providers: [
        provideRouter([]),
        { provide: UnidadEmergenciaFacadeService, useValue: facade },
        { provide: ListaSeleccionStorage, useValue: listaSeleccion },
        NotificationService,
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(CatalogoPage);
    component = fixture.componentInstance;
    router = TestBed.inject(Router);
    spyOn(router, 'navigate').and.resolveTo(true);
  });

  it('carga_lista_con_limit_20_y_cursor_null', () => {
    fixture.detectChanges();
    expect(facade.listar).toHaveBeenCalledWith(
      jasmine.objectContaining({ limit: 20, cursor: null }),
    );
    const html = fixture.nativeElement as HTMLElement;
    expect(html.querySelector('a[href*="editar"]')).toBeNull();
    expect(html.querySelector('td.font-mono')?.textContent?.trim()).toContain('7');
  });

  it('filtros_resetean_cursor', () => {
    fixture.detectChanges();
    facade.listar.calls.reset();
    component.cursor = 50;
    component.filtroQ = 'ABC';
    component.onFiltrosChange();
    expect(facade.listar).toHaveBeenCalledWith(
      jasmine.objectContaining({ q: 'ABC', cursor: null, limit: 20 }),
    );
  });

  it('pager_siguiente_usa_next_cursor', () => {
    fixture.detectChanges();
    facade.listar.calls.reset();
    facade.listar.and.returnValue(
      of({
        ok: true,
        data: {
          items: [{ ...unidad, idunidademergencia: 8, placa: 'XYZ' }],
          pagination: { next_cursor: null, limit: 20 },
        },
      }),
    );
    component.paginaSiguiente();
    expect(component.cursor).toBe(7);
    expect(facade.listar).toHaveBeenCalledWith(
      jasmine.objectContaining({ cursor: 7, limit: 20 }),
    );
  });

  it('timeout_muestra_error_y_reintentar', () => {
    facade.listar.and.returnValue(throwError(() => new TimeoutError()));
    fixture.detectChanges();
    expect(component.unidadesError).toContain('tardó demasiado');
    expect(fixture.nativeElement.querySelector('[data-testid="btn-reintentar-lista"]')).toBeTruthy();
  });

  it('refresh_no_oculta_filas_ya_cargadas', () => {
    fixture.detectChanges();
    expect(component.unidades.length).toBe(1);
    facade.listar.and.returnValue(
      of({
        ok: true,
        data: { items: [unidad], pagination: { next_cursor: null, limit: 20 } },
      }),
    );
    component.loading = true;
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('[data-testid="tabla-unidades"]')).toBeTruthy();
    expect(fixture.nativeElement.querySelector('[data-testid="loading-skeleton"]')).toBeNull();
  });

  it('ojo_navega_a_detalle', () => {
    fixture.detectChanges();
    const eye = fixture.nativeElement.querySelector(
      '[data-testid="btn-ver-detalles"]',
    ) as HTMLButtonElement;
    eye.click();
    expect(listaSeleccion.set).toHaveBeenCalledWith('7');
    expect(router.navigate).toHaveBeenCalledWith([
      '/red-operativa/alta-unidades/detalle',
      7,
    ]);
  });

  it('lapiz_navega_a_editar', () => {
    fixture.detectChanges();
    const pencil = fixture.nativeElement.querySelector(
      '[data-testid="btn-editar-unidad"]',
    ) as HTMLButtonElement;
    pencil.click();
    expect(router.navigate).toHaveBeenCalledWith([
      '/red-operativa/alta-unidades/editar',
      7,
    ]);
  });

  it('cta_nueva_unidad_navega_a_nueva', () => {
    fixture.detectChanges();
    const cta = fixture.nativeElement.querySelector(
      '[data-testid="btn-nueva-unidad"]',
    ) as HTMLButtonElement;
    cta.click();
    expect(router.navigate).toHaveBeenCalledWith(['/red-operativa/alta-unidades/nueva']);
  });

  it('trash_abre_dialogo_baja_en_dos_pasos', () => {
    fixture.detectChanges();
    const trash = fixture.nativeElement.querySelector(
      '[data-testid="btn-baja-unidad"]',
    ) as HTMLButtonElement;
    trash.click();
    fixture.detectChanges();
    expect(component.bajaDialog?.step).toBe(1);
    expect(fixture.nativeElement.querySelector('[data-testid="baja-dialog"]')).toBeTruthy();
  });

  it('no_incluye_workpanel_host', () => {
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('[data-testid="workpanel-host"]')).toBeNull();
  });
});
