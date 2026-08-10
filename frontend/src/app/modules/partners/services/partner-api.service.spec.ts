/** @marker unit */
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';

import { ContratoApiService } from './contrato-api.service';
import { PartnerApiService, nuevaClaveIdempotencia } from './partner-api.service';

/**
 * Estos tests ejercitan el servicio DE VERDAD contra `HttpTestingController`.
 * Las páginas lo mockean, así que sin este archivo la construcción real de
 * URLs, parámetros y cabeceras no la verificaba nadie.
 */
describe('PartnerApiService', () => {
  let api: PartnerApiService;
  let contratos: ContratoApiService;
  let http: HttpTestingController;

  const BASE = '/api/v1/partners';

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    api = TestBed.inject(PartnerApiService);
    contratos = TestBed.inject(ContratoApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  describe('listar', () => {
    it('siempre envía un limit explícito', () => {
      // Pinot aplica un LIMIT 10 implícito y silencioso a las consultas sin
      // límite: pedir «todo» devolvería 10 filas sin que nadie se entere.
      // Act
      api.listar().subscribe();

      // Assert
      const req = http.expectOne((r) => r.url === BASE);
      expect(req.request.params.get('limit')).toBe('20');
      req.flush({ data: [], meta: { pagination: null } });
    });

    it('envía el filtro de estado cuando se indica', () => {
      // Act
      api.listar({ estado: 'Pendiente de aprobación' }).subscribe();

      // Assert
      const req = http.expectOne((r) => r.url === BASE);
      expect(req.request.params.get('estado')).toBe('Pendiente de aprobación');
      req.flush({ data: [], meta: { pagination: null } });
    });

    it('omite el cursor en la primera página', () => {
      // Act
      api.listar({ cursor: null }).subscribe();

      // Assert
      const req = http.expectOne((r) => r.url === BASE);
      expect(req.request.params.has('cursor')).toBeFalse();
      req.flush({ data: [], meta: { pagination: null } });
    });

    it('envía el cursor en las siguientes', () => {
      // Act
      api.listar({ cursor: 55 }).subscribe();

      // Assert
      const req = http.expectOne((r) => r.url === BASE);
      expect(req.request.params.get('cursor')).toBe('55');
      req.flush({ data: [], meta: { pagination: null } });
    });
  });

  describe('miPartner (BE-DELTA-01)', () => {
    it('llama a /partners/me sin ningún identificador', () => {
      // Act
      api.miPartner().subscribe();

      // Assert
      const req = http.expectOne(`${BASE}/me`);
      expect(req.request.method).toBe('GET');
      req.flush({ data: {}, meta: { pagination: null } });
    });
  });

  describe('Idempotency-Key', () => {
    it('el registro la envía como cabecera', () => {
      // Act
      api
        .registrar(
          {
            idcliente: 1,
            nombrepartner: 'X',
            contacto_tecnico_nombre: 'A',
            contacto_tecnico_gmail: 'a@b.com',
          },
          'clave-registro',
        )
        .subscribe();

      // Assert
      const req = http.expectOne(BASE);
      expect(req.request.headers.get('Idempotency-Key')).toBe('clave-registro');
      req.flush({ data: {}, meta: { pagination: null } });
    });

    it('la emisión de credenciales la envía — es la que protege el secreto', () => {
      // Act
      api.emitirCredencial(7, { nombre_credencial: 'x' }, 'clave-emision').subscribe();

      // Assert
      const req = http.expectOne(`${BASE}/7/credenciales`);
      expect(req.request.headers.get('Idempotency-Key')).toBe('clave-emision');
      req.flush({ data: {}, meta: { pagination: null } });
    });

    it('la resolución de promoción la envía', () => {
      // Act
      api.resolverPromocion(7, { decision: 'aprobar' }, 'clave-resolucion').subscribe();

      // Assert
      const req = http.expectOne(`${BASE}/7/solicitud-produccion/resolucion`);
      expect(req.request.headers.get('Idempotency-Key')).toBe('clave-resolucion');
      req.flush({ data: {}, meta: { pagination: null } });
    });

    it('la asignación de plan la envía', () => {
      // Act
      api.asignarPlan(7, 'clave-plan').subscribe();

      // Assert
      const req = http.expectOne(`${BASE}/7/plan-acceso`);
      expect(req.request.headers.get('Idempotency-Key')).toBe('clave-plan');
      req.flush({ data: {}, meta: { pagination: null } });
    });

    it('la solicitud de producción la envía', () => {
      // Act
      api.solicitarProduccion(7, 'prod', 'clave-solicitud').subscribe();

      // Assert
      const req = http.expectOne(`${BASE}/7/solicitud-produccion`);
      expect(req.request.headers.get('Idempotency-Key')).toBe('clave-solicitud');
      expect(req.request.body).toEqual({ nombre_credencial: 'prod' });
      req.flush({ data: {}, meta: { pagination: null } });
    });
  });

  describe('listarCredenciales', () => {
    it('filtra por entorno y por activas cuando se pide', () => {
      // Act
      api.listarCredenciales(7, { entorno: 'Producción', soloActivas: true }).subscribe();

      // Assert
      const req = http.expectOne((r) => r.url === `${BASE}/7/credenciales`);
      expect(req.request.params.get('entorno')).toBe('Producción');
      expect(req.request.params.get('solo_activas')).toBe('true');
      req.flush({ data: [], meta: { pagination: null } });
    });

    it('no envía filtros vacíos', () => {
      // Act
      api.listarCredenciales(7).subscribe();

      // Assert
      const req = http.expectOne((r) => r.url === `${BASE}/7/credenciales`);
      expect(req.request.params.keys().length).toBe(0);
      req.flush({ data: [], meta: { pagination: null } });
    });
  });

  describe('nuevaClaveIdempotencia', () => {
    it('genera claves distintas en cada llamada', () => {
      // Act
      const claves = new Set(Array.from({ length: 20 }, () => nuevaClaveIdempotencia()));

      // Assert
      expect(claves.size).toBe(20);
    });
  });

  describe('ContratoApiService', () => {
    it('exige id_servicio: el contrato se versiona POR SERVICIO', () => {
      // Act
      contratos.consultar(2).subscribe();

      // Assert
      const req = http.expectOne((r) => r.url === '/api/v1/contrato-integracion');
      expect(req.request.params.get('id_servicio')).toBe('2');
      req.flush({ data: {}, meta: { pagination: null } });
    });

    it('permite pedir una versión concreta', () => {
      // Act
      contratos.consultar(1, 'v1').subscribe();

      // Assert
      const req = http.expectOne((r) => r.url === '/api/v1/contrato-integracion');
      expect(req.request.params.get('version')).toBe('v1');
      req.flush({ data: {}, meta: { pagination: null } });
    });

    it('omite version cuando no se indica', () => {
      // Act
      contratos.consultar(1).subscribe();

      // Assert
      const req = http.expectOne((r) => r.url === '/api/v1/contrato-integracion');
      expect(req.request.params.has('version')).toBeFalse();
      req.flush({ data: {}, meta: { pagination: null } });
    });
  });
});
