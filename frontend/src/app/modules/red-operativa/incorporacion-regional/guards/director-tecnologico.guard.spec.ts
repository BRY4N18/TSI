/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';

import {
  administradorODirectorTecnologicoGuard,
  directorTecnologicoGuard,
} from './director-tecnologico.guard';
import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';

describe('directorTecnologicoGuard', () => {
  it('allows_director_tecnologico_role', () => {
    // Arrange
    TestBed.configureTestingModule({
      providers: [
        {
          provide: AuthApiService,
          useValue: {
            isAuthenticated: () => true,
            hasRole: (r: string) => r === 'DirectorTecnologico',
          },
        },
        { provide: Router, useValue: { createUrlTree: () => false } },
      ],
    });

    // Act
    const result = TestBed.runInInjectionContext(() =>
      directorTecnologicoGuard({} as never, {} as never),
    );

    // Assert
    expect(result).toBe(true);
  });

  it('blocks_administrador_role', () => {
    // Arrange
    let redirected = false;
    TestBed.configureTestingModule({
      providers: [
        {
          provide: AuthApiService,
          useValue: { isAuthenticated: () => true, hasRole: (r: string) => r === 'Administrador' },
        },
        { provide: Router, useValue: { createUrlTree: () => (redirected = true) } },
      ],
    });

    // Act
    TestBed.runInInjectionContext(() => directorTecnologicoGuard({} as never, {} as never));

    // Assert
    expect(redirected).toBe(true);
  });
});

describe('administradorODirectorTecnologicoGuard', () => {
  it('allows_administrador_role', () => {
    // Arrange
    TestBed.configureTestingModule({
      providers: [
        {
          provide: AuthApiService,
          useValue: {
            isAuthenticated: () => true,
            hasRole: (r: string) => r === 'Administrador',
            hasAnyRole: (roles: string[]) => roles.includes('Administrador'),
          },
        },
        { provide: Router, useValue: { createUrlTree: () => false } },
      ],
    });

    // Act
    const result = TestBed.runInInjectionContext(() =>
      administradorODirectorTecnologicoGuard({} as never, {} as never),
    );

    // Assert
    expect(result).toBe(true);
  });

  it('allows_director_tecnologico_role', () => {
    // Arrange
    TestBed.configureTestingModule({
      providers: [
        {
          provide: AuthApiService,
          useValue: {
            isAuthenticated: () => true,
            hasRole: (r: string) => r === 'DirectorTecnologico',
            hasAnyRole: (roles: string[]) => roles.includes('DirectorTecnologico'),
          },
        },
        { provide: Router, useValue: { createUrlTree: () => false } },
      ],
    });

    // Act
    const result = TestBed.runInInjectionContext(() =>
      administradorODirectorTecnologicoGuard({} as never, {} as never),
    );

    // Assert
    expect(result).toBe(true);
  });

  it('blocks_operador_role', () => {
    // Arrange
    let redirected = false;
    TestBed.configureTestingModule({
      providers: [
        {
          provide: AuthApiService,
          useValue: {
            isAuthenticated: () => true,
            hasRole: () => false,
            hasAnyRole: () => false,
          },
        },
        { provide: Router, useValue: { createUrlTree: () => (redirected = true) } },
      ],
    });

    // Act
    TestBed.runInInjectionContext(() =>
      administradorODirectorTecnologicoGuard({} as never, {} as never),
    );

    // Assert
    expect(redirected).toBe(true);
  });
});
