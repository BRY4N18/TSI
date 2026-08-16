/**
 * Cliente único de los 32 listados tácticos simples.
 *
 * Uno solo, no uno por departamento: todos comparten ruta, envelope, cursor y
 * forma de error. Un servicio por departamento sería la misma consulta escrita
 * siete veces, y la primera copia que se despistara abriría el hueco.
 *
 * Contrato: `specs/002-tactico/contrato-informes-simples-frontend.md`.
 */

import { HttpClient, HttpErrorResponse, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, catchError, throwError } from 'rxjs';

import {
  ErrorEnvelope,
  ErrorListado,
  ListadoEnvelope,
  ValoresFiltro,
} from './informes-listado.types';

export interface PeticionListado {
  /** Ruta relativa a la base, p. ej. `emergencias/casos`. */
  ruta: string;
  filtros?: ValoresFiltro;
  /** Opaco: se reenvía tal cual, sin interpretarlo. */
  cursor?: string | null;
  limit?: number;
}

/** Igual que el defecto del backend. Cambiarlo aquí no cambia el máximo real. */
export const LIMIT_DEFECTO = 50;

@Injectable({ providedIn: 'root' })
export class InformesListadoService {
  private readonly http = inject(HttpClient);
  private readonly base = '/api/v1/informes';

  listar<T>(peticion: PeticionListado): Observable<ListadoEnvelope<T>> {
    return this.http
      .get<ListadoEnvelope<T>>(`${this.base}/${peticion.ruta}`, {
        params: construirParams(peticion),
      })
      .pipe(catchError((error) => throwError(() => clasificarError(error))));
  }
}

/**
 * Arma la query descartando los filtros sin valor.
 *
 * Un filtro vacío **no viaja**. Enviarlo como cadena vacía haría que el backend
 * lo viera declarado, y `meta.filtros` refleja los filtros *aplicados*: un
 * filtro que no se aplicó no es un filtro con valor nulo, es un filtro que no
 * está.
 */
export function construirParams(peticion: PeticionListado): HttpParams {
  let params = new HttpParams().set('limit', String(peticion.limit ?? LIMIT_DEFECTO));

  for (const [nombre, valor] of Object.entries(peticion.filtros ?? {})) {
    if (valor === null || valor === undefined || valor === '') {
      continue;
    }
    params = params.set(nombre, String(valor));
  }

  if (peticion.cursor) {
    params = params.set('cursor', peticion.cursor);
  }
  return params;
}

/**
 * Traduce el fallo a algo que la pantalla pueda presentar honestamente.
 *
 * ⚠️ **Un `400` no se convierte en lista vacía.** El backend rechaza en vez de
 * recortar —`limit` sobre el máximo, enumeración desconocida, rango en un
 * listado de estado actual—, y tragarse ese error para pintar una tabla vacía
 * reintroduce el fallo silencioso que la regla existe para evitar: el
 * consumidor leería «no hay resultados» donde el sistema dijo «tu petición está
 * mal».
 *
 * ⚠️ **Un `403` tampoco.** Dice que no tienes acceso, que es distinto de que no
 * haya datos — y es la diferencia que el backend eligió a propósito frente a
 * devolver `200` con `data: []`.
 *
 * El `detail` viaja tal cual porque está escrito para leerse: nombra los
 * valores válidos, y sustituirlo por «Ha ocurrido un error» tira justo la
 * información con la que quien lo lee podría corregir su petición.
 */
export function clasificarError(error: unknown): ErrorListado {
  if (!(error instanceof HttpErrorResponse)) {
    return {
      tipo: 'servidor',
      mensaje: 'No se pudo completar la consulta.',
      reintentable: true,
    };
  }

  const detail = detalleDe(error);

  if (error.status === 400) {
    return {
      tipo: 'peticion',
      mensaje: detail ?? 'La consulta tiene un filtro que el informe no admite.',
      // Repetir la misma petición devuelve el mismo `400`. Ofrecer
      // «Reintentar» invitaría a insistir en vez de a corregir el filtro.
      reintentable: false,
    };
  }

  if (error.status === 403) {
    return {
      tipo: 'permiso',
      mensaje: detail ?? 'No tienes acceso a este informe.',
      reintentable: false,
    };
  }

  if (error.status === 0) {
    return {
      tipo: 'red',
      mensaje: 'No se pudo contactar con el servidor.',
      reintentable: true,
    };
  }

  return {
    tipo: 'servidor',
    mensaje: detail ?? 'El informe no está disponible en este momento.',
    reintentable: true,
  };
}

function detalleDe(error: HttpErrorResponse): string | null {
  const cuerpo = error.error as Partial<ErrorEnvelope> | null;
  const detail = cuerpo?.detail;
  return typeof detail === 'string' && detail.trim() !== '' ? detail : null;
}
