import { TestBed } from '@angular/core/testing';
import { Router, UrlTree } from '@angular/router';
import { provideRouter } from '@angular/router';

import { administradorGuard } from './administrador.guard';
import { AuthApiService } from '../../cuentas-clientes/auth/services/auth-api.service';

function ejecutar(): boolean | UrlTree {
  return TestBed.runInInjectionContext(
    () => administradorGuard(null as never, null as never) as boolean | UrlTree,
  );
}

describe('administradorGuard', () => {
  function configurar(autenticado: boolean, roles: string[]): void {
    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        {
          provide: AuthApiService,
          useValue: {
            isAuthenticated: () => autenticado,
            hasAnyRole: (pedidos: string[]) => pedidos.some((r) => roles.includes(r)),
          },
        },
      ],
    });
  }

  it('deja pasar al Administrador', () => {
    // Arrange
    configurar(true, ['Administrador']);

    // Act / Assert
    expect(ejecutar()).toBeTrue();
  });

  it('🎯 NO deja pasar al Desarrollador de APIs', () => {
    // El guard de la consola (gestorPartnersGuard) sí lo admite; este no, y es
    // deliberado: decidir qué hacer con un excedente no cobrado es una decisión
    // de negocio, no de plataforma.
    // Arrange
    configurar(true, ['DesarrolladorAPIs']);

    // Act
    const resultado = ejecutar();

    // Assert
    expect(resultado).not.toBeTrue();
    expect((resultado as UrlTree).toString()).toContain('access-denied');
  });

  it('no deja pasar a un Partner de integración', () => {
    // Arrange
    configurar(true, ['PartnerIntegracion']);

    // Act / Assert
    expect(ejecutar()).not.toBeTrue();
  });

  it('sin sesión manda al login, no a access-denied', () => {
    // Arrange — no es que le falten permisos: es que no ha entrado
    configurar(false, []);

    // Act
    const resultado = ejecutar() as UrlTree;

    // Assert
    expect(resultado.toString()).toContain('login');
  });

  it('un usuario con Administrador entre varios roles pasa', () => {
    // Arrange
    configurar(true, ['DesarrolladorAPIs', 'Administrador']);

    // Act / Assert
    expect(ejecutar()).toBeTrue();
  });
});
