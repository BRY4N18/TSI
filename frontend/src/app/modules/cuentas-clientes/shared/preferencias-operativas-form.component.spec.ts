/** @marker unit */
import {
  deserializarPreferencias,
  serializarPreferencias,
} from './preferencias-operativas-form.component';

describe('preferencias operativas — serialización', () => {
  it('guarda el umbral de llegada como JSON y las zonas como lista de ids', () => {
    const serializado = serializarPreferencias({
      tiempoLlegadaMaxMin: 20,
      canales: 'ambos',
      telefonoSms: '+593999556677',
      condados: [
        { id: 7, nombre: 'Cuauhtemoc' },
        { id: 9, nombre: 'Benito Juarez' },
      ],
      destinatarios: 'ops@rescate.com, direccion@rescate.com',
    });

    expect(JSON.parse(serializado.umbrales_alerta)).toEqual({ tiempo_llegada_max_min: 20 });
    expect(JSON.parse(serializado.zonas_geograficas)).toEqual([7, 9]);
    expect(serializado.canales_notificacion).toBe('ambos');
    expect(serializado.destinatarios_reportes).toBe('ops@rescate.com, direccion@rescate.com');
  });

  it('sin umbral declarado guarda un objeto vacío, no un nulo', () => {
    const serializado = serializarPreferencias({
      tiempoLlegadaMaxMin: null,
      canales: 'email',
      telefonoSms: '',
      condados: [],
      destinatarios: '',
    });

    expect(serializado.umbrales_alerta).toBe('{}');
    expect(serializado.zonas_geograficas).toBe('[]');
  });

  it('reconstruye el formulario desde lo guardado', () => {
    const form = deserializarPreferencias({
      umbrales_alerta: '{"tiempo_llegada_max_min": 15}',
      canales_notificacion: 'sms',
      telefono_sms: '+593999000111',
      zonas_geograficas: '[3, 4]',
      destinatarios_reportes: 'a@b.com',
    });

    expect(form.tiempoLlegadaMaxMin).toBe(15);
    expect(form.canales).toBe('sms');
    expect(form.condados.map((c) => c.id)).toEqual([3, 4]);
    expect(form.destinatarios).toBe('a@b.com');
  });

  it('tolera los centinelas de Pinot sin reventar', () => {
    // Pinot guarda `'null'` (la cadena) donde no hay valor; `JSON.parse` de eso
    // devuelve `null`, e iterarlo lanzaría TypeError.
    const form = deserializarPreferencias({
      umbrales_alerta: 'null',
      zonas_geograficas: 'null',
      telefono_sms: null,
      destinatarios_reportes: null,
    });

    expect(form.tiempoLlegadaMaxMin).toBeNull();
    expect(form.condados).toEqual([]);
    expect(form.canales).toBe('email');
    expect(form.destinatarios).toBe('');
  });

  it('ida y vuelta conserva lo declarado', () => {
    const original = {
      tiempoLlegadaMaxMin: 30,
      canales: 'email' as const,
      telefonoSms: '',
      condados: [{ id: 11, nombre: 'Coyoacan' }],
      destinatarios: 'reportes@cliente.com',
    };
    const vuelta = deserializarPreferencias(serializarPreferencias(original));

    expect(vuelta.tiempoLlegadaMaxMin).toBe(30);
    expect(vuelta.condados.map((c) => c.id)).toEqual([11]);
    expect(vuelta.destinatarios).toBe('reportes@cliente.com');
  });
});
