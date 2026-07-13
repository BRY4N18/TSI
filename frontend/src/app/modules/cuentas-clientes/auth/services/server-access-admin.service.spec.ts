/** @marker unit */
import { provideHttpClient } from '@angular/common/http';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { ServerAccessAdminService } from './server-access-admin.service';

describe('ServerAccessAdminService', () => {
  let service: ServerAccessAdminService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });

    service = TestBed.inject(ServerAccessAdminService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('lists server users from versioned API', () => {
    // Arrange
    const response = {
      data: [
        {
          idusuarioservidor: 1,
          usuario: 'deploy-bot',
          activo: true,
          roles: ['Ops'],
        },
      ],
      meta: { pagination: null },
    };

    // Act
    service.listServerUsers().subscribe((value) => {
      expect(value.data.length).toBe(1);
    });

    // Assert
    const req = httpMock.expectOne('/api/v1/usuarios-servidor');
    expect(req.request.method).toBe('GET');
    req.flush(response);
  });

  it('assigns server role to server user', () => {
    // Arrange
    const payload = { idusuarioservidor: 3, idrolservidor: 7 };
    const response = {
      data: {
        idusuarioservidor: 3,
        usuario: 'infra-admin',
        activo: true,
        roles: ['DBA'],
      },
      meta: { pagination: null },
    };

    // Act
    service.assignServerRole(payload).subscribe((value) => {
      expect(value.data.usuario).toBe('infra-admin');
    });

    // Assert
    const req = httpMock.expectOne('/api/v1/usuarios-servidor/3/roles-servidor');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ idrolservidor: 7 });
    req.flush(response);
  });

  it('creates server role in catalog endpoint', () => {
    // Arrange
    const payload = { rolservidor: 'Monitoring', descripcion: 'Read-only metrics' };
    const response = {
      data: {
        idrolservidor: 12,
        rolservidor: 'Monitoring',
        descripcion: 'Read-only metrics',
        activo: true,
      },
      meta: { pagination: null },
    };

    // Act
    service.createServerRole(payload).subscribe((value) => {
      expect(value.data.rolservidor).toBe('Monitoring');
    });

    // Assert
    const req = httpMock.expectOne('/api/v1/roles-servidor');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(payload);
    req.flush(response);
  });
});
