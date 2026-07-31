import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';

import { NotificationService } from '../../../../shared/notifications/notification.service';
import { PipelineApiService } from '../../services/pipeline-api.service';
import { ProspectoApiService } from '../../services/prospecto-api.service';
import { PipelineBoardPage } from './pipeline-board.page';

describe('PipelineBoardPage', () => {
  let fixture: ComponentFixture<PipelineBoardPage>;
  let page: PipelineBoardPage;
  let api: jasmine.SpyObj<ProspectoApiService>;
  let pipelineApi: jasmine.SpyObj<PipelineApiService>;

  const sample = {
    idprospecto: 1,
    nombres: 'Ana',
    apellidos: 'Pérez',
    gmail: 'a@x.com',
    empresa: 'Acme',
    tipo_organizacion: 'Privado' as const,
    cargo: 'Gerente',
    telefono: '099',
    como_nos_conocio: 'web',
    etapa_actual: 'Nuevo' as const,
    idusuario: 20,
    activo: true,
    motivo_inactividad: null,
  };

  beforeEach(async () => {
    api = jasmine.createSpyObj('ProspectoApiService', ['listar']);
    pipelineApi = jasmine.createSpyObj('PipelineApiService', ['registrarTransicion']);
    api.listar.and.returnValue(of({ data: [sample], meta: {} }));
    pipelineApi.registrarTransicion.and.returnValue(
      of({ data: { prospecto: { ...sample, etapa_actual: 'Contactado' as const } } }),
    );

    await TestBed.configureTestingModule({
      imports: [PipelineBoardPage],
      providers: [
        provideRouter([]),
        { provide: ProspectoApiService, useValue: api },
        { provide: PipelineApiService, useValue: pipelineApi },
        { provide: NotificationService, useValue: { toast: jasmine.createSpy('toast') } },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(PipelineBoardPage);
    page = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('lista_activos_con_limit_acotado', () => {
    expect(api.listar).toHaveBeenCalledWith(jasmine.objectContaining({ activo: true, limit: 100 }));
  });

  it('muestra_ojo_y_avanza_sin_drag', () => {
    const root: HTMLElement = fixture.nativeElement;
    expect(root.querySelector('[data-testid="btn-ver-prospecto-board"]')).toBeTruthy();
    expect(root.querySelector('[draggable="true"]')).toBeNull();
    page.avanzar(sample);
    expect(pipelineApi.registrarTransicion).toHaveBeenCalled();
  });
});
