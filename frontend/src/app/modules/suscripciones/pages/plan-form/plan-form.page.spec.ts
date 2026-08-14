import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ReactiveFormsModule } from '@angular/forms';
import { provideRouter, ActivatedRoute } from '@angular/router';
import { of } from 'rxjs';

import { NotificationService } from '../../../../shared/notifications/notification.service';
import { PlanApiService } from '../../services/plan-api.service';
import { PlanFormPage } from './plan-form.page';

describe('PlanFormPage', () => {
  let fixture: ComponentFixture<PlanFormPage>;
  let page: PlanFormPage;
  let planApi: jasmine.SpyObj<PlanApiService>;

  beforeEach(async () => {
    planApi = jasmine.createSpyObj('PlanApiService', [
      'crear',
      'actualizar',
      'listar',
      'listarSeveridades',
    ]);
    planApi.crear.and.returnValue(of({ data: { idplan: 9, nombre: 'Nuevo' } }));
    // El selector de severidades se alimenta de `Dim_Severidad`, no de una lista
    // escrita en duro en el componente.
    planApi.listarSeveridades.and.returnValue(
      of([
        { idseveridad: 1, severidad: 'Leve' },
        { idseveridad: 2, severidad: 'Moderado' },
        { idseveridad: 3, severidad: 'Grave' },
        { idseveridad: 4, severidad: 'Fatal' },
      ]),
    );

    await TestBed.configureTestingModule({
      imports: [PlanFormPage, ReactiveFormsModule],
      providers: [
        provideRouter([]),
        { provide: PlanApiService, useValue: planApi },
        {
          provide: ActivatedRoute,
          useValue: { snapshot: { paramMap: { get: () => null } } },
        },
        {
          provide: NotificationService,
          useValue: { toast: jasmine.createSpy('toast') },
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(PlanFormPage);
    page = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('creates a plan on publish', () => {
    expect(page.esEdicion()).toBe(false);
    page.form.setValue({
      nombre: 'Plan Demo',
      precio: 49,
      precio_excedente_llamada: 0.05,
      nivel: 'Básico',
      periodicidad: 'Mensual',
      carga_lote_habilitada: false,
      unidades_max: 5,
      usuarios_max: 3,
      api_calls_mes: 1000,
      api_calls_minuto: 30,
    });
    page.guardar();
    expect(planApi.crear).toHaveBeenCalled();
  });

  it('carga las severidades del catálogo y envía sus identificadores', () => {
    expect(page.severidadesCatalogo().length).toBe(4);
    // Por defecto queda marcada la más leve.
    expect(page.severidadesSeleccionadas()).toEqual([1]);
    page.alternarSeveridad(3);
    expect(page.severidadesSeleccionadas()).toEqual([1, 3]);
    page.alternarSeveridad(1);
    expect(page.severidadesSeleccionadas()).toEqual([3]);
  });

  it('places primary save CTA in the page header', () => {
    fixture.detectChanges();
    const btn = fixture.nativeElement.querySelector(
      '[data-testid="btn-guardar-plan-header"]',
    ) as HTMLButtonElement | null;
    expect(btn).toBeTruthy();
    expect(btn?.getAttribute('form')).toBe('plan-form');
    expect(btn?.textContent?.trim()).toContain('Publicar plan');
  });
});
