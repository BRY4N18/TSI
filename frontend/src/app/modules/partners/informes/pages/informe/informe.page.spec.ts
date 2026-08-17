/** @marker unit */
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap, provideRouter } from '@angular/router';
import { of } from 'rxjs';

import { InformePartnersPage } from './informe.page';
import { AuthApiService } from '../../../../cuentas-clientes/auth/services/auth-api.service';

function rutaDe(informe: string) {
  const paramMap = convertToParamMap({ informe });
  return { paramMap: of(paramMap), snapshot: { paramMap, data: {} as Record<string, unknown> } };
}

describe('InformePartnersPage', () => {
  let fixture: ComponentFixture<InformePartnersPage>;
  let http: HttpTestingController;

  function montar(informe: string, roles: string[] = ['Administrador']) {
    TestBed.resetTestingModule();
    TestBed.configureTestingModule({
      imports: [InformePartnersPage],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: ActivatedRoute, useValue: rutaDe(informe) },
        {
          provide: AuthApiService,
          useValue: {
            isAuthenticated: () => true,
            hasRole: (r: string) => roles.includes(r),
          },
        },
      ],
    });
    fixture = TestBed.createComponent(InformePartnersPage);
    http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
  }

  function peticion(informe: string) {
    return http.expectOne((r) => r.url === `/api/v1/informes/partners-api/${informe}`);
  }

  function texto(testid: string): string | null {
    const el = fixture.nativeElement.querySelector(`[data-testid="${testid}"]`);
    return el ? (el.textContent as string).replace(/\s+/g, ' ').trim() : null;
  }

  function envelope(data: unknown[], acotadoA?: 'propios' | 'todos') {
    return {
      data,
      meta: {
        pagination: { cursor: null, limit: 50, has_next: false },
        filtros: {},
        ...(acotadoA ? { acotado_a: acotadoA } : {}),
      },
    };
  }

  afterEach(() => http.verify());

  describe('filtros de periodo', () => {
    it('rango_when_es_estado_actual_no_se_pinta', () => {
      for (const id of ['partners', 'credenciales', 'versiones-contrato', 'alcance-datos']) {
        montar(id);
        peticion(id).flush(envelope([], 'todos'));
        fixture.detectChanges();
        expect(fixture.nativeElement.querySelector('[data-testid="filtro-desde"]'))
          .withContext(id)
          .toBeNull();
      }
    });

    it('rango_when_es_cambios_acceso_si_se_pinta', () => {
      montar('cambios-acceso');
      peticion('cambios-acceso').flush(envelope([], 'todos'));
      fixture.detectChanges();
      expect(fixture.nativeElement.querySelector('[data-testid="filtro-desde"]')).not.toBeNull();
    });

    it('paginacion_when_hay_filas_no_muestra_total_ni_numeros_navegables', () => {
      montar('partners');
      peticion('partners').flush(
        envelope([{ cuenta: 'A', nombre_partner: 'P', estado_acceso: 'Registrado' }], 'todos'),
      );
      fixture.detectChanges();
      const nav = texto('paginacion') ?? '';
      expect(nav).toContain('Página 1');
      expect(nav).not.toContain('de 2');
      expect(nav).not.toMatch(/\d+\s+registros/);
    });
  });

  describe('el aviso de alcance', () => {
    it('acotado_a_propios_when_llega_muestra_el_aviso', () => {
      montar('partners', ['PartnerIntegracion']);
      peticion('partners').flush(
        envelope([{ cuenta: 'A', nombre_partner: 'Mio', estado_acceso: 'Registrado' }], 'propios'),
      );
      fixture.detectChanges();
      expect(texto('aviso-alcance')).toContain('tus registros');
    });

    it('acotado_a_todos_when_llega_NO_muestra_aviso', () => {
      montar('partners');
      peticion('partners').flush(
        envelope([{ cuenta: 'A', nombre_partner: 'P', estado_acceso: 'Registrado' }], 'todos'),
      );
      fixture.detectChanges();
      expect(texto('aviso-alcance')).toBeNull();
    });

    it('lista_vacia_acotada_when_se_muestra_menciona_el_acotamiento', () => {
      montar('credenciales', ['PartnerIntegracion']);
      peticion('credenciales').flush(envelope([], 'propios'));
      fixture.detectChanges();
      const vacio = texto('empty-state') ?? '';
      expect(vacio).toContain('No hay credenciales con esos criterios.');
      expect(vacio).toContain('entre tus registros');
    });

    it('lista_vacia_sin_acotar_when_se_muestra_solo_da_su_mensaje', () => {
      montar('versiones-contrato');
      peticion('versiones-contrato').flush(envelope([], 'todos'));
      fixture.detectChanges();
      const vacio = texto('empty-state') ?? '';
      expect(vacio).toContain('No hay versiones de contrato con esos criterios.');
      expect(vacio).not.toContain('entre tus registros');
      expect(vacio.toLowerCase()).not.toContain('sin datos');
    });
  });

  describe('el filtro partner', () => {
    it('gestor_when_abre_acceso_ve_el_filtro_partner', () => {
      montar('partners', ['DesarrolladorAPIs']);
      peticion('partners').flush(envelope([], 'todos'));
      fixture.detectChanges();
      expect(fixture.nativeElement.querySelector('[data-testid="filtro-partner"]')).not.toBeNull();
    });

    it('partner_when_abre_NO_ve_el_filtro_partner', () => {
      montar('partners', ['PartnerIntegracion']);
      peticion('partners').flush(envelope([], 'propios'));
      fixture.detectChanges();
      expect(fixture.nativeElement.querySelector('[data-testid="filtro-partner"]')).toBeNull();
    });
  });

  describe('credencial inactiva y secreto', () => {
    it('inactiva_when_llega_indica_que_no_esta_activa_sin_motivo', () => {
      montar('credenciales');
      peticion('credenciales').flush(
        envelope(
          [
            {
              partner: 'Andina',
              nombre_credencial: 'revocada',
              entorno: 'Sandbox',
              activa: false,
              fecha_creacion: '2026-01-01T00:00:00Z',
              fecha_expiracion: null,
              dias_para_caducar: null,
            },
          ],
          'todos',
        ),
      );
      fixture.detectChanges();
      const fila = texto('fila-informe') ?? '';
      expect(fila).toContain('No');
      expect(fila).not.toContain('revocacion');
      expect(fila).not.toContain('cascada');
      expect(fila).not.toContain('comprometido');
      expect(fixture.nativeElement.textContent).not.toContain('client_secret');
      expect(fixture.nativeElement.textContent).not.toContain('secret_hash');
    });

    it('pruebas_y_produccion_when_llegan_coexisten', () => {
      montar('credenciales');
      peticion('credenciales').flush(
        envelope(
          [
            {
              partner: 'Andina',
              nombre_credencial: 'sandbox',
              entorno: 'Sandbox',
              activa: true,
              fecha_creacion: '2026-01-01T00:00:00Z',
              fecha_expiracion: null,
              dias_para_caducar: null,
            },
            {
              partner: 'Andina',
              nombre_credencial: 'prod',
              entorno: 'Producción',
              activa: true,
              fecha_creacion: '2026-01-02T00:00:00Z',
              fecha_expiracion: null,
              dias_para_caducar: null,
            },
          ],
          'todos',
        ),
      );
      fixture.detectChanges();
      expect(fixture.nativeElement.querySelectorAll('[data-testid="fila-informe"]').length).toBe(2);
      const tabla = texto('tabla-informe') ?? '';
      expect(tabla).toContain('Sandbox');
      expect(tabla).toContain('Producción');
    });
  });

  describe('un error no se convierte en tabla vacia', () => {
    it('error_400_when_llega_muestra_el_detalle_del_backend', () => {
      montar('partners');
      const detail = "estado 'Activo' no es válido, use uno de: Registrado, Suspendido.";
      peticion('partners').flush(
        { error: 'bad_request', detail, code: '400' },
        { status: 400, statusText: 'Bad Request' },
      );
      fixture.detectChanges();
      expect(texto('error-detalle')).toBe(detail);
      expect(texto('empty-state')).toBeNull();
      expect(texto('tabla-informe')).toBeNull();
    });

    it('error_400_when_se_muestra_no_ofrece_reintentar', () => {
      montar('partners');
      peticion('partners').flush(
        { error: 'bad_request', detail: 'limit no puede superar 500', code: '400' },
        { status: 400, statusText: 'Bad Request' },
      );
      fixture.detectChanges();
      expect(texto('btn-reintentar')).toBeNull();
    });

    it('error_403_when_llega_se_distingue_de_una_lista_vacia', () => {
      montar('versiones-contrato');
      peticion('versiones-contrato').flush(
        { error: 'forbidden', detail: 'No puede consultar los registros de otro partner.', code: '403' },
        { status: 403, statusText: 'Forbidden' },
      );
      fixture.detectChanges();
      expect(texto('error-permiso')).toContain('No puede consultar los registros de otro partner.');
      expect(texto('empty-state')).toBeNull();
    });

    it('error_500_when_llega_si_ofrece_reintentar', () => {
      montar('partners');
      peticion('partners').flush({}, { status: 500, statusText: 'Server Error' });
      fixture.detectChanges();
      expect(texto('btn-reintentar')).toContain('Reintentar');
    });
  });

  describe('ausente no es ilimitado ni cero', () => {
    it('alcance_sin_zonas_when_llega_se_ve_ausente_no_ilimitado', () => {
      montar('alcance-datos');
      peticion('alcance-datos').flush(
        envelope(
          [
            {
              cuenta: 'Ferrer',
              zonas_geograficas: null,
              frecuencia_reportes: null,
              formato_reportes: null,
              canales_notificacion: null,
              destinatarios_reportes: null,
            },
          ],
          'todos',
        ),
      );
      fixture.detectChanges();
      const fila = texto('fila-informe') ?? '';
      expect(fila).toContain('—');
      expect(fila.toLowerCase()).not.toContain('ilimitado');
      expect(fila.toLowerCase()).not.toContain('todas las zonas');
    });

    it('reactivacion_sin_motivo_when_llega_se_ve_ausente', () => {
      montar('cambios-acceso');
      peticion('cambios-acceso').flush(
        envelope(
          [
            {
              partner: 'Andina',
              credencial: null,
              tipo_cambio: 'reactivacion',
              estado_anterior: 'Suspendido',
              estado_nuevo: 'Activo',
              motivo: null,
              ejecutado_por: 'Administrador',
              fecha: '2026-08-01T12:00:00Z',
            },
          ],
          'todos',
        ),
      );
      fixture.detectChanges();
      const celdas = fixture.nativeElement.querySelectorAll('[data-testid="fila-informe"] td');
      expect(celdas[5].textContent.trim()).toBe('—');
    });

    it('partner_no_suspendido_when_llega_fecha_y_motivo_ausentes', () => {
      montar('partners');
      peticion('partners').flush(
        envelope(
          [
            {
              cuenta: 'A',
              nombre_partner: 'Vivo',
              estado_acceso: 'Producción activa',
              plan_api: 'pro',
              limite_llamadas_mes: 0,
              limite_llamadas_minuto: null,
              contacto_tecnico: null,
              fecha_suspension: null,
              motivo_suspension: null,
            },
          ],
          'todos',
        ),
      );
      fixture.detectChanges();
      const celdas = fixture.nativeElement.querySelectorAll('[data-testid="fila-informe"] td');
      expect(celdas[4].textContent.trim()).toBe('0');
      expect(celdas[7].textContent.trim()).toBe('—');
      expect(celdas[8].textContent.trim()).toBe('—');
    });

    it('version_retirada_when_llega_no_se_omite', () => {
      montar('versiones-contrato');
      peticion('versiones-contrato').flush(
        envelope(
          [
            {
              servicio: 'Siniestros',
              version: '1.0',
              estado: 'retirada',
              spec_url: null,
              fecha_publicacion: '2025-01-01T00:00:00Z',
              fecha_retiro: '2026-01-01T00:00:00Z',
            },
            {
              servicio: 'Siniestros',
              version: '2.0',
              estado: 'vigente',
              spec_url: 'https://example',
              fecha_publicacion: '2026-01-01T00:00:00Z',
              fecha_retiro: null,
            },
          ],
          'todos',
        ),
      );
      fixture.detectChanges();
      expect(fixture.nativeElement.querySelectorAll('[data-testid="fila-informe"]').length).toBe(2);
      const celdasVigente = fixture.nativeElement.querySelectorAll(
        '[data-testid="fila-informe"]',
      )[1].querySelectorAll('td');
      expect(celdasVigente[5].textContent.trim()).toBe('—');
    });
  });
});
