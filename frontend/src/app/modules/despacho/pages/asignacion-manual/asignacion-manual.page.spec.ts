/** @marker unit */
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { convertToParamMap, ActivatedRoute } from '@angular/router';
import { of, Subject, throwError } from 'rxjs';

import { DespachoApiService } from '../../services/despacho-api.service';
import { AsignacionManualPage } from './asignacion-manual.page';

describe('AsignacionManualPage', () => {
  let fixture: ComponentFixture<AsignacionManualPage>;
  let api: jasmine.SpyObj<DespachoApiService>;
  let candidatas$: Subject<unknown>;

  beforeEach(async () => {
    api = jasmine.createSpyObj('DespachoApiService', ['listarCandidatas', 'asignarManual']);
    candidatas$ = new Subject();
    api.listarCandidatas.and.returnValue(candidatas$.asObservable() as never);

    await TestBed.configureTestingModule({
      imports: [AsignacionManualPage],
      providers: [
        { provide: DespachoApiService, useValue: api },
        {
          provide: ActivatedRoute,
          useValue: { snapshot: { paramMap: convertToParamMap({ idaccidente: 'ACC-1' }) } },
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(AsignacionManualPage);
    fixture.detectChanges();
  });

  it('constructor_loads_candidatas_and_preselects_first', () => {
    // Act: emulate SSE/HTTP stream pushing candidates
    candidatas$.next({
      data: {
        candidatas: [
          { idunidademergencia: 10, unidademergencia: 'Ambulancia 1', puntuacion: 0.9 },
          { idunidademergencia: 11, unidademergencia: 'Ambulancia 2', puntuacion: 0.5 },
        ],
      },
      meta: {},
    });

    // Assert
    expect(api.listarCandidatas).toHaveBeenCalledWith('ACC-1');
    expect(fixture.componentInstance.candidatas().length).toBe(2);
    expect(fixture.componentInstance.unidadSeleccionada).toBe(10);
  });

  it('asignar_when_success_shows_message', () => {
    // Arrange
    candidatas$.next({ data: { candidatas: [] }, meta: {} });
    api.asignarManual.and.returnValue(
      of<any>({ data: { message: 'Unidad asignada' }, meta: {} }),
    );
    fixture.componentInstance.unidadSeleccionada = 10;

    // Act
    fixture.componentInstance.asignar();

    // Assert
    expect(api.asignarManual).toHaveBeenCalledWith('ACC-1', 10);
    expect(fixture.componentInstance.mensaje()).toBe('Unidad asignada');
  });

  it('asignar_when_api_error_shows_error_message', () => {
    // Arrange
    candidatas$.next({ data: { candidatas: [] }, meta: {} });
    api.asignarManual.and.returnValue(throwError(() => new Error('conflict')));

    // Act
    fixture.componentInstance.asignar();

    // Assert
    expect(fixture.componentInstance.mensaje()).toBe('Error al asignar');
  });
});
