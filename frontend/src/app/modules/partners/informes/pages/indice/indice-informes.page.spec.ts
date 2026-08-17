/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { IndiceInformesPartnersPage } from './indice-informes.page';
import { AuthApiService } from '../../../../cuentas-clientes/auth/services/auth-api.service';

function montar(roles: string[]) {
  TestBed.resetTestingModule();
  TestBed.configureTestingModule({
    imports: [IndiceInformesPartnersPage],
    providers: [
      provideRouter([]),
      {
        provide: AuthApiService,
        useValue: {
          isAuthenticated: () => true,
          hasRole: (r: string) => roles.includes(r),
        },
      },
    ],
  });
  const fixture = TestBed.createComponent(IndiceInformesPartnersPage);
  fixture.detectChanges();
  return fixture;
}

function enlaces(fixture: ReturnType<typeof montar>): string[] {
  return Array.from(
    fixture.nativeElement.querySelectorAll('[data-testid^="enlace-"]') as NodeListOf<HTMLElement>,
  ).map((el) => el.getAttribute('data-testid') ?? '');
}

describe('IndiceInformesPartnersPage', () => {
  it('gestor_when_abre_ve_cinco_enlaces', () => {
    const fixture = montar(['DesarrolladorAPIs']);
    const ids = enlaces(fixture);
    expect(ids.sort()).toEqual(
      [
        'enlace-alcance-datos',
        'enlace-cambios-acceso',
        'enlace-credenciales',
        'enlace-partners',
        'enlace-versiones-contrato',
      ].sort(),
    );
    expect(fixture.nativeElement.querySelector('[data-testid="titulo-indice"]').textContent).toContain(
      'Informes de Partners',
    );
  });

  it('director_when_abre_ve_cinco_enlaces', () => {
    const fixture = montar(['DirectorTecnologico']);
    expect(enlaces(fixture).length).toBe(5);
  });

  it('partner_when_abre_ve_exactamente_tres_y_cero_de_contrato', () => {
    const fixture = montar(['PartnerIntegracion']);
    const ids = enlaces(fixture);
    expect(ids.sort()).toEqual(
      ['enlace-cambios-acceso', 'enlace-credenciales', 'enlace-partners'].sort(),
    );
    expect(ids).not.toContain('enlace-versiones-contrato');
    expect(ids).not.toContain('enlace-alcance-datos');
    expect(fixture.nativeElement.querySelector('[data-testid="titulo-indice"]').textContent).toContain(
      'Estado de mi acceso',
    );
  });
});
