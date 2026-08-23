/** @marker unit */
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap } from '@angular/router';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';

import { InformeCuentasPage } from './informe.page';

function rutaDe(informe: string) {
  const paramMap = convertToParamMap({ informe });
  return {
    paramMap: of(paramMap),
    snapshot: { paramMap, data: {} as Record<string, unknown> },
  };
}

describe('InformeCuentasPage', () => {
  let fixture: ComponentFixture<InformeCuentasPage>;
  let http: HttpTestingController;

  function montar(informe: string) {
    TestBed.configureTestingModule({
      imports: [InformeCuentasPage],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: ActivatedRoute, useValue: rutaDe(informe) },
      ],
    });
    fixture = TestBed.createComponent(InformeCuentasPage);
    http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();

    // Los listados con filtros de catálogo piden además sus opciones. Se
    // responde aquí y no en cada prueba porque no es el objeto de ninguna: sin
    // esto, `http.verify()` fallaría por una petición pendiente en todas.
    for (const peticion of http.match((r) => r.url.endsWith('/catalogos'))) {
      peticion.flush({ data: {} });
    }

  }

  function peticion(informe: string) {
    return http.expectOne((r) => r.url === `/api/v1/informes/cuentas-clientes/${informe}`);
  }

  function texto(testid: string): string | null {
    const el = fixture.nativeElement.querySelector(`[data-testid="${testid}"]`);
    return el ? (el.textContent as string).replace(/\s+/g, ' ').trim() : null;
  }

  function envelope(data: unknown[], cursor: string | null = null) {
    return {
      data,
      meta: { pagination: { cursor, limit: 50, has_next: cursor !== null }, filtros: {} },
    };
  }

  afterEach(() => http.verify());

  describe('la carga inicial', () => {
    it('al_abrir_when_se_monta_consulta_su_ruta', () => {
      montar('sesiones-activas');

      const req = peticion('sesiones-activas');
      expect(req.request.params.get('limit')).toBe('50');
      req.flush(envelope([]));
    });

    it('titulo_when_se_monta_es_el_de_la_definicion', () => {
      montar('sesiones-activas');
      peticion('sesiones-activas').flush(envelope([]));
      fixture.detectChanges();

      expect(texto('titulo-informe')).toBe('Sesiones activas');
    });

    it('columnas_when_hay_filas_son_las_declaradas', () => {
      montar('sesiones-activas');
      peticion('sesiones-activas').flush(
        envelope([{ usuario: 'Ana', navegador: 'Firefox', fecha_inicio: '2026-08-11T12:00:00Z' }]),
      );
      fixture.detectChanges();

      const cabeceras = Array.from(
        fixture.nativeElement.querySelectorAll('th') as NodeListOf<HTMLElement>,
      ).map((th) => th.textContent?.trim());

      expect(cabeceras).toEqual(['Usuario', 'Navegador', 'Inicio']);
    });
  });

  describe('un error no se convierte en tabla vacia', () => {
    it('error_400_when_llega_muestra_el_detalle_del_backend', () => {
      // Es la mitad del valor de la capa: un backend que rechaza y una pantalla
      // que lo pinta como vacío desperdician el trabajo que costó rechazar.
      montar('cuentas-por-estado');
      const detail = "El filtro 'estado' no admite el valor 'Suspendido'; use uno de: Activo.";
      peticion('cuentas-por-estado').flush(
        { error: 'bad_request', detail, code: '400' },
        { status: 400, statusText: 'Bad Request' },
      );
      fixture.detectChanges();

      expect(texto('error-detalle')).toBe(detail);
      expect(texto('empty-state')).toBeNull();
      expect(texto('tabla-informe')).toBeNull();
    });

    it('error_400_when_se_muestra_no_ofrece_reintentar', () => {
      montar('cuentas-por-estado');
      peticion('cuentas-por-estado').flush(
        { error: 'bad_request', detail: 'limit no puede superar 500', code: '400' },
        { status: 400, statusText: 'Bad Request' },
      );
      fixture.detectChanges();

      expect(texto('btn-reintentar')).toBeNull();
    });

    it('error_403_when_llega_se_distingue_de_una_lista_vacia', () => {
      montar('cuentas-por-estado');
      peticion('cuentas-por-estado').flush(
        { error: 'forbidden', detail: 'Privilegios insuficientes', code: '403' },
        { status: 403, statusText: 'Forbidden' },
      );
      fixture.detectChanges();

      expect(texto('error-permiso')).toContain('Privilegios insuficientes');
      expect(texto('empty-state')).toBeNull();
    });

    it('error_500_when_llega_si_ofrece_reintentar', () => {
      montar('cuentas-por-estado');
      peticion('cuentas-por-estado').flush(
        {},
        { status: 500, statusText: 'Server Error' },
      );
      fixture.detectChanges();

      expect(texto('btn-reintentar')).toContain('Reintentar');
    });
  });

  describe('el valor ausente', () => {
    it('fecha_ausente_when_llega_null_no_se_muestra_como_1970', () => {
      montar('cuentas-por-estado');
      peticion('cuentas-por-estado').flush(
        envelope([
          {
            razon_social: 'Empresa A',
            tipo: 'Corporativo',
            estado: 'Pendiente',
            estado_onboarding: null,
            fecha_inicio_contrato: null,
            propietario: null,
          },
        ]),
      );
      fixture.detectChanges();

      const celdas = fixture.nativeElement.querySelectorAll('[data-testid="fila-informe"] td');

      expect(celdas[4].textContent.trim()).toBe('—');
      expect(celdas[4].textContent).not.toContain('1970');
      expect(celdas[5].textContent.trim()).toBe('—');
    });

    it('fila_sin_propietario_when_llega_no_se_omite', () => {
      montar('cuentas-por-estado');
      peticion('cuentas-por-estado').flush(
        envelope([
          {
            razon_social: 'Empresa A',
            tipo: 'Corporativo',
            estado: 'Pendiente',
            estado_onboarding: null,
            fecha_inicio_contrato: null,
            propietario: null,
          },
        ]),
      );
      fixture.detectChanges();

      expect(fixture.nativeElement.querySelectorAll('[data-testid="fila-informe"]').length).toBe(1);
    });

    it('lista_de_roles_when_llega_se_muestra_separada', () => {
      montar('usuarios-por-rol');
      peticion('usuarios-por-rol').flush(
        envelope([
          { nombre: 'Ana', gmail: 'ana@tsi.com', roles: ['Administrador', 'Operador'], activo: true },
        ]),
      );
      fixture.detectChanges();

      const celdas = fixture.nativeElement.querySelectorAll('[data-testid="fila-informe"] td');

      expect(celdas[2].textContent.trim()).toBe('Administrador, Operador');
    });

    it('lista_vacia_de_roles_when_llega_se_muestra_ausente', () => {
      // Quien no tiene roles no tiene «cero roles»: no los tiene.
      montar('usuarios-por-rol');
      peticion('usuarios-por-rol').flush(
        envelope([{ nombre: 'Ana', gmail: 'ana@tsi.com', roles: [], activo: true }]),
      );
      fixture.detectChanges();

      const celdas = fixture.nativeElement.querySelectorAll('[data-testid="fila-informe"] td');

      expect(celdas[2].textContent.trim()).toBe('—');
    });
  });

  describe('los filtros', () => {
    it('rango_when_el_listado_es_de_estado_actual_no_se_pinta', () => {
      montar('cuentas-por-estado');
      peticion('cuentas-por-estado').flush(envelope([]));
      fixture.detectChanges();

      expect(fixture.nativeElement.querySelector('[data-testid="filtro-desde"]')).toBeNull();
    });

    it('rango_when_el_listado_es_de_periodo_si_se_pinta', () => {
      montar('transferencias-propiedad');
      peticion('transferencias-propiedad').flush(envelope([]));
      fixture.detectChanges();

      expect(fixture.nativeElement.querySelector('[data-testid="filtro-desde"]')).not.toBeNull();
    });

    it('barra_when_el_listado_no_declara_filtros_no_se_pinta', () => {
      montar('credenciales-temporales');
      peticion('credenciales-temporales').flush(envelope([]));
      fixture.detectChanges();

      expect(fixture.nativeElement.querySelector('[data-testid="filtros-informe"]')).toBeNull();
    });
  });

  describe('la paginacion', () => {
    it('sin_resultados_when_no_hay_filas_muestra_el_mensaje_del_dominio', () => {
      montar('solicitudes-alta-pendientes');
      peticion('solicitudes-alta-pendientes').flush(envelope([]));
      fixture.detectChanges();

      expect(texto('empty-state')).toContain('No hay solicitudes de alta pendientes.');
    });

    it('transferencias_vacio_when_se_muestra_explica_la_decision_28', () => {
      montar('transferencias-propiedad');
      peticion('transferencias-propiedad').flush(envelope([]));
      fixture.detectChanges();

      expect(texto('empty-state')).toContain('aún no se alimenta');
    });

    it('paginacion_when_hay_filas_no_muestra_recuento_total', () => {
      montar('sesiones-activas');
      peticion('sesiones-activas').flush(
        envelope([{ usuario: 'Ana', navegador: 'Firefox', fecha_inicio: '2026-08-11T12:00:00Z' }]),
      );
      fixture.detectChanges();

      const nav = texto('paginacion') ?? '';

      expect(nav).toContain('Página 1');
      expect(nav).not.toMatch(/\d+\s+(registros|resultados)/);
      expect(nav).not.toContain('de 1');
    });
  });
});
