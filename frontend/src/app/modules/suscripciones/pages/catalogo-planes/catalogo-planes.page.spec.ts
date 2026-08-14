import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of, throwError, TimeoutError } from 'rxjs';

import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';
import { NotificationService } from '../../../../shared/notifications/notification.service';
import { PlanApiService } from '../../services/plan-api.service';
import { CatalogoPlanesPage } from './catalogo-planes.page';

describe('CatalogoPlanesPage', () => {
  let fixture: ComponentFixture<CatalogoPlanesPage>;
  let page: CatalogoPlanesPage;
  let planApi: jasmine.SpyObj<PlanApiService>;

  const samplePlan = {
    idplan: 1,
    nombre: 'Profesional',
    precio: 149,
    nivel: 'Profesional' as const,
    activo: true,
    limites: { unidades_max: 25, usuarios_max: 10, api_calls_mes: 10000, api_calls_minuto: 120 },
  };

  beforeEach(async () => {
    planApi = jasmine.createSpyObj('PlanApiService', [
      'listar',
      'actualizar',
      'buscarPorId',
      'listarSeveridades',
    ]);
    // Ambas pantallas traducen los ids de severidad que guarda el plan a los
    // nombres de `Dim_Severidad`.
    planApi.listarSeveridades.and.returnValue(
      of([
        { idseveridad: 1, severidad: 'Leve' },
        { idseveridad: 2, severidad: 'Moderado' },
        { idseveridad: 3, severidad: 'Grave' },
        { idseveridad: 4, severidad: 'Fatal' },
      ]),
    );
    planApi.listar.and.returnValue(
      of({
        data: [samplePlan],
        meta: { pagination: { next_cursor: 7, limit: 20 } },
      }),
    );
    planApi.actualizar.and.returnValue(of({ data: { idplan: 1, activo: false } }));

    await TestBed.configureTestingModule({
      imports: [CatalogoPlanesPage],
      providers: [
        provideRouter([]),
        { provide: PlanApiService, useValue: planApi },
        {
          provide: AuthApiService,
          useValue: { hasRole: (r: string) => r === 'DirectorEstrategia' },
        },
        {
          provide: NotificationService,
          useValue: { toast: jasmine.createSpy('toast') },
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(CatalogoPlanesPage);
    page = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('carga_lista_con_limit_20_y_cursor_null', () => {
    expect(page.esDirector()).toBe(true);
    expect(planApi.listar).toHaveBeenCalledWith(
      jasmine.objectContaining({
        limit: 20,
        cursor: null,
        solo_activos: false,
      }),
    );
  });

  it('filtros_resetean_cursor', () => {
    page.cursor = 50;
    page.filtroQ = 'Pro';
    page.onFiltroSelect();
    expect(planApi.listar).toHaveBeenCalledWith(
      jasmine.objectContaining({ cursor: null, limit: 20 }),
    );
  });

  it('filtro_estado_activo_envia_activo_true', () => {
    planApi.listar.calls.reset();
    page.filtroEstado = 'activo';
    page.onFiltroSelect();
    expect(planApi.listar).toHaveBeenCalledWith(
      jasmine.objectContaining({ activo: true, cursor: null, limit: 20 }),
    );
  });

  it('filtro_estado_inactivo_envia_activo_false', () => {
    planApi.listar.calls.reset();
    page.filtroEstado = 'inactivo';
    page.onFiltroSelect();
    expect(planApi.listar).toHaveBeenCalledWith(
      jasmine.objectContaining({ activo: false, cursor: null, limit: 20 }),
    );
  });

  it('filtro_nivel_se_incluye_en_query', () => {
    planApi.listar.calls.reset();
    page.filtroNivel = 'Profesional';
    page.onFiltroSelect();
    expect(planApi.listar).toHaveBeenCalledWith(
      jasmine.objectContaining({ nivel: 'Profesional', cursor: null, limit: 20 }),
    );
  });

  it('pager_siguiente_usa_next_cursor', () => {
    planApi.listar.calls.reset();
    planApi.listar.and.returnValue(
      of({
        data: [samplePlan],
        meta: { pagination: { next_cursor: null, limit: 20 } },
      }),
    );
    page.paginaSiguiente();
    expect(page.cursor).toBe(7);
    expect(planApi.listar).toHaveBeenCalledWith(
      jasmine.objectContaining({ cursor: 7, limit: 20 }),
    );
  });

  it('timeout_muestra_error_y_reintentar', fakeAsync(() => {
    planApi.listar.and.returnValue(throwError(() => new TimeoutError()));
    page.cargar({ resetCursor: true });
    tick();
    fixture.detectChanges();
    expect(page.error()).toContain('tardó demasiado');
    const root: HTMLElement = fixture.nativeElement;
    expect(root.querySelector('[data-testid="btn-reintentar-lista"]')).toBeTruthy();
  }));

  it('requires confirmation before deactivating', () => {
    page.pedirDesactivar({ idplan: 1, nombre: 'Profesional', activo: true });
    expect(page.planPendienteDesactivar()?.idplan).toBe(1);
    expect(planApi.actualizar).not.toHaveBeenCalled();
    page.confirmarDesactivar();
    expect(planApi.actualizar).toHaveBeenCalled();
  });

  it('renders eye and pencil actions and create CTA in header', () => {
    const root: HTMLElement = fixture.nativeElement;
    expect(root.querySelector('[data-testid="btn-crear-plan"]')).toBeTruthy();
    expect(root.querySelector('[data-testid="btn-ver-plan"]')).toBeTruthy();
    expect(root.querySelector('[data-testid="btn-editar-plan"]')).toBeTruthy();
    expect(root.querySelector('[data-testid="btn-desactivar-plan"]')).toBeTruthy();
    expect(root.querySelector('[data-testid="catalogo-planes-filtros"]')).toBeTruthy();
  });
});
