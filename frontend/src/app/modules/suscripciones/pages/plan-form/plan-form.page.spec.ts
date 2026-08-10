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
    planApi = jasmine.createSpyObj('PlanApiService', ['crear', 'actualizar', 'listar']);
    planApi.crear.and.returnValue(of({ data: { idplan: 9, nombre: 'Nuevo' } }));

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
      severidad_baja: true,
      severidad_media: false,
      severidad_alta: false,
      carga_lote_habilitada: false,
      unidades_max: 5,
      usuarios_max: 3,
      api_calls_mes: 1000,
      api_calls_minuto: 30,
    });
    page.guardar();
    expect(planApi.crear).toHaveBeenCalled();
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
