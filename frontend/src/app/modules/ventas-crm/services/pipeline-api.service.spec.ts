/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';

import { PipelineApiService } from './pipeline-api.service';

describe('PipelineApiService', () => {
  let service: PipelineApiService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [HttpClientTestingModule] });
    service = TestBed.inject(PipelineApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('registrarTransicion_posts_pipeline', () => {
    service
      .registrarTransicion(1, { etapa_nueva: 'Contactado', etapa_actual_esperada: 'Nuevo' })
      .subscribe();
    const req = httpMock.expectOne('/api/v1/ventas-crm/prospectos/1/pipeline');
    expect(req.request.method).toBe('POST');
    req.flush({ data: {} });
  });
});
