/** @marker unit */
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { AuthApiService } from '../services/auth-api.service';
import { AccessDeniedPage } from './access-denied.page';

describe('AccessDeniedPage', () => {
  let fixture: ComponentFixture<AccessDeniedPage>;
  let authApi: jasmine.SpyObj<AuthApiService>;

  function montar(perfil: unknown) {
    authApi.getProfile.and.returnValue(perfil as any);
    TestBed.configureTestingModule({
      imports: [AccessDeniedPage],
      providers: [provideRouter([]), { provide: AuthApiService, useValue: authApi }],
    });
    fixture = TestBed.createComponent(AccessDeniedPage);
    fixture.detectChanges();
  }

  beforeEach(() => {
    authApi = jasmine.createSpyObj('AuthApiService', ['getProfile']);
  });

  it('explica_que_la_sesion_sigue_activa_y_el_problema_es_el_rol', () => {
    // Arrange / Act
    montar({ idusuario: 2, gmail: 'admin@tsi.com', roles: ['Administrador'] });

    // Assert — el usuario no debe creer que perdió la sesión
    const texto = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(texto).toContain('Acceso denegado');
    expect(texto).toContain('Tu sesión sigue activa');
    expect(texto).not.toContain('Iniciar sesión');
  });

  it('muestra_la_sesion_vigente_para_orientar_al_usuario', () => {
    // Act
    montar({ idusuario: 2, gmail: 'admin@tsi.com', roles: ['Administrador'] });

    // Assert
    const rol = (fixture.nativeElement as HTMLElement).querySelector(
      '[data-testid="rol-actual"]',
    );
    expect(rol?.textContent).toContain('admin@tsi.com');
    expect(rol?.textContent).toContain('Administrador');
  });

  it('ofrece_volver_al_home_del_rol_no_al_portal_publico', () => {
    // Act
    montar({ idusuario: 10, gmail: 'op@tsi.com', roles: ['Operador'] });

    // Assert
    const cta = (fixture.nativeElement as HTMLElement).querySelector(
      '[data-testid="btn-volver-inicio"]',
    );
    expect(cta?.getAttribute('href')).toBe('/accidentes/lista');
  });

  it('sin_roles_no_rompe', () => {
    // Act
    montar({ idusuario: 1, gmail: 'x@tsi.com', roles: [] });

    // Assert
    expect(
      (fixture.nativeElement as HTMLElement).querySelector('[data-testid="rol-actual"]')
        ?.textContent,
    ).toContain('sin roles asignados');
  });
});
