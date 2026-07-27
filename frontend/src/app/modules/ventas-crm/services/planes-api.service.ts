import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { ApiEnvelope, PlanPublico } from '../models/prospectos.types';

@Injectable({ providedIn: 'root' })
export class PlanesApiService {
  private readonly http = inject(HttpClient);
  private readonly base = '/api/v1/ventas-crm/planes';

  listar(): Observable<ApiEnvelope<PlanPublico[]>> {
    return this.http.get<ApiEnvelope<PlanPublico[]>>(this.base);
  }
}
