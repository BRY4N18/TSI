import { HttpRequest, HttpResponse } from '@angular/common/http';
import { of } from 'rxjs';

import { clearDemoSessionToken, demoSessionInterceptor, storeDemoSessionToken } from './demo-session.interceptor';

describe('demoSessionInterceptor', () => {
  afterEach(() => clearDemoSessionToken());

  it('adds Authorization for interacciones when token stored', (done) => {
    // Arrange
    storeDemoSessionToken('abc');
    const req = new HttpRequest('POST', '/api/v1/ventas-crm/demo/interacciones', {});
    // Act
    demoSessionInterceptor(req, (nextReq) => {
      // Assert
      expect(nextReq.headers.get('Authorization')).toBe('Bearer abc');
      done();
      return of(new HttpResponse({ status: 200, body: {} }));
    });
  });
});
