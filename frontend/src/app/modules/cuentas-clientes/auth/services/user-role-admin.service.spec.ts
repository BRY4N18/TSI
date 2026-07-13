/** @marker unit */
import { provideHttpClient } from '@angular/common/http';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { UserRoleAdminService } from './user-role-admin.service';

describe('UserRoleAdminService', () => {
  let service: UserRoleAdminService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });

    service = TestBed.inject(UserRoleAdminService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('listUsers_when_ok_returns_envelope', () => {
    // Act
    service.listUsers().subscribe((res) => {
      expect(res.data.length).toBe(1);
    });

    // Assert
    const req = httpMock.expectOne('/api/v1/usuarios');
    expect(req.request.method).toBe('GET');
    req.flush({ data: [{ idusuario: 1, roles: [] }], meta: {} });
  });

  it('createUser_posts_payload', () => {
    // Arrange
    const payload = {
      nombres: 'Ana',
      apellidos: 'Perez',
      gmail: 'ana@test.com',
      identificacion: '0102030405',
      genero: 'F',
      telefono: '0999999999',
      fechanacimiento: '1990-01-01',
      roleIds: [1],
    };

    // Act
    service.createUser(payload).subscribe((res) => {
      expect(res.data.idusuario).toBe(9);
    });

    // Assert
    const req = httpMock.expectOne('/api/v1/usuarios');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(payload);
    req.flush({ data: { idusuario: 9, roles: [] }, meta: {} });
  });

  it('updateUser_patches_resource', () => {
    // Act
    service.updateUser(3, { activo: false }).subscribe((res) => {
      expect(res.data.activo).toBeFalse();
    });

    // Assert
    const req = httpMock.expectOne('/api/v1/usuarios/3');
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body).toEqual({ activo: false });
    req.flush({ data: { idusuario: 3, activo: false, roles: [] }, meta: {} });
  });

  it('deactivateUser_delegates_to_updateUser_with_activo_false', () => {
    // Act
    service.deactivateUser(4).subscribe();

    // Assert
    const req = httpMock.expectOne('/api/v1/usuarios/4');
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body).toEqual({ activo: false });
    req.flush({ data: { idusuario: 4, activo: false, roles: [] }, meta: {} });
  });

  it('listRoles_when_ok_returns_envelope', () => {
    // Act
    service.listRoles().subscribe((res) => {
      expect(res.data.length).toBe(1);
    });

    // Assert
    const req = httpMock.expectOne('/api/v1/roles');
    expect(req.request.method).toBe('GET');
    req.flush({ data: [{ idrol: 1, rol: 'Admin', descripcion: '', activo: true }], meta: {} });
  });

  it('createRole_posts_payload', () => {
    // Act
    service.createRole({ rol: 'Supervisor', descripcion: 'desc' }).subscribe((res) => {
      expect(res.data.rol).toBe('Supervisor');
    });

    // Assert
    const req = httpMock.expectOne('/api/v1/roles');
    expect(req.request.method).toBe('POST');
    req.flush({ data: { idrol: 2, rol: 'Supervisor', descripcion: 'desc', activo: true }, meta: {} });
  });

  it('updateRole_patches_resource', () => {
    // Act
    service.updateRole(2, { activo: false }).subscribe();

    // Assert
    const req = httpMock.expectOne('/api/v1/roles/2');
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body).toEqual({ activo: false });
    req.flush({ data: { idrol: 2, rol: 'Supervisor', descripcion: 'desc', activo: false }, meta: {} });
  });

  it('assignRole_posts_idrol_to_user_roles_endpoint', () => {
    // Act
    service.assignRole({ idusuario: 3, idrol: 7 }).subscribe();

    // Assert
    const req = httpMock.expectOne('/api/v1/usuarios/3/roles');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ idrol: 7 });
    req.flush({ data: { idusuario: 3, roles: ['x'] }, meta: {} });
  });
});
