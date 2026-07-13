/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';

import { DespachoSseService } from './despacho-sse.service';

describe('DespachoSseService', () => {
  it('streamDespacho_when_called_returns_observable', () => {
    TestBed.configureTestingModule({ providers: [DespachoSseService, provideHttpClient()] });
    const service = TestBed.inject(DespachoSseService);
    const obs = service.streamDespacho('ACC-1');
    expect(obs.subscribe).toBeDefined();
  });
});
