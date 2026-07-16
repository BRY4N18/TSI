/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { AppShellComponent } from './app-shell.component';
import { AuthApiService } from '../../modules/cuentas-clientes/auth/services/auth-api.service';
import type { Profile } from '../../modules/cuentas-clientes/auth/services/auth-api.types';

function buildAuthApiStub(profile: Profile | null) {
  return {
    getProfile: () => profile,
    hasRole: (role: string) => profile?.roles.includes(role) ?? false,
    logout: () => ({ subscribe: (obs: { next: () => void }) => obs.next() }),
    clearSession: () => {},
  };
}

describe('AppShellComponent', () => {
  function createComponent(profile: Profile | null) {
    TestBed.configureTestingModule({
      imports: [AppShellComponent],
      providers: [
        provideRouter([]),
        { provide: AuthApiService, useValue: buildAuthApiStub(profile) },
      ],
    });
    return TestBed.createComponent(AppShellComponent).componentInstance;
  }

  it('initials_when_gmail_has_two_parts_returns_two_letters', () => {
    // Arrange / Act
    const component = createComponent({
      idusuario: 1,
      gmail: 'bryan.lombeida@tsi.com',
      roles: ['Operador'],
    });

    // Assert
    expect(component.initials).toBe('BL');
  });

  it('initials_when_gmail_has_single_word_returns_first_letter', () => {
    // Arrange / Act
    const component = createComponent({ idusuario: 1, gmail: 'operador@tsi.com', roles: ['Operador'] });

    // Assert
    expect(component.initials).toBe('O');
  });

  it('initials_when_no_profile_returns_placeholder', () => {
    // Arrange / Act
    const component = createComponent(null);

    // Assert
    expect(component.initials).toBe('?');
  });

  it('navGroups_when_role_operador_includes_emergencias_pero_no_administracion', () => {
    // Arrange / Act
    const component = createComponent({
      idusuario: 1,
      gmail: 'operador@tsi.com',
      roles: ['Operador'],
    });

    // Assert
    const groupNames = component.navGroups().map((g) => g.name);
    expect(groupNames).toContain('Emergencias');
    expect(groupNames).not.toContain('Administración');
  });

  it('navGroups_when_role_sin_modulos_returns_empty', () => {
    // Arrange / Act
    const component = createComponent({ idusuario: 1, gmail: 'sinrol@tsi.com', roles: ['RolInexistente'] });

    // Assert
    expect(component.navGroups()).toEqual([]);
  });
});
