import { CommonModule, CurrencyPipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { ThemeService } from '../../../../shared/theme/theme.service';
import { TablerIconComponent, TablerIconName } from '../../../../shared/ui/icon/tabler-icon.component';
import { PlanPublico, SeveridadPlan } from '../../models/prospectos.types';
import { PlanesApiService } from '../../services/planes-api.service';

export interface LimiteItem {
  label: string;
  value: string;
}

export interface CapacidadItem {
  icon: TablerIconName;
  title: string;
  description: string;
}

const LABELS_LIMITES: Record<string, string> = {
  unidades_max: 'Unidades máx.',
  usuarios_max: 'Usuarios máx.',
  api_calls_mes: 'Llamadas API / mes',
};

@Component({
  selector: 'app-catalogo-planes',
  standalone: true,
  imports: [CommonModule, RouterLink, CurrencyPipe, TablerIconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './catalogo-planes.page.html',
})
export class CatalogoPlanesPage implements OnInit {
  private readonly api = inject(PlanesApiService);
  readonly themeService = inject(ThemeService);

  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly planes = signal<PlanPublico[]>([]);
  readonly year = new Date().getFullYear();

  readonly capacidades: CapacidadItem[] = [
    {
      icon: 'radio',
      title: 'Monitoreo en tiempo real',
      description:
        'Sigue el estado de cada caso y la posición de las unidades desde un mismo centro de operaciones.',
    },
    {
      icon: 'car-crash',
      title: 'Registro de accidentes',
      description:
        'Captura estructurada del incidente para despacho rápido y trazabilidad del expediente.',
    },
    {
      icon: 'map',
      title: 'Despacho inteligente',
      description:
        'Asigna la unidad adecuada según zona, disponibilidad y severidad del accidente.',
    },
    {
      icon: 'eye',
      title: 'Seguimiento operativo',
      description:
        'Visibilidad continua del ciclo: asignación, en ruta, en sitio y cierre del caso.',
    },
  ];

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    this.loading.set(true);
    this.error.set(null);
    this.api.listar().subscribe({
      next: (res) => {
        this.planes.set(res.data ?? []);
        this.loading.set(false);
      },
      error: () => {
        this.error.set('No se pudo cargar el catálogo de planes.');
        this.loading.set(false);
      },
    });
  }

  scrollTo(sectionId: string): void {
    document.getElementById(sectionId)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  limitesComoLista(limites: string): LimiteItem[] {
    if (!limites?.trim()) {
      return [{ label: 'Límites', value: 'Sin detalle' }];
    }
    try {
      const parsed = JSON.parse(limites) as Record<string, unknown>;
      return Object.entries(parsed).map(([key, raw]) => ({
        label: LABELS_LIMITES[key] ?? this.labelDesdeClave(key),
        value: this.formatearValor(raw),
      }));
    } catch {
      return [{ label: 'Detalle', value: limites }];
    }
  }

  esPopular(plan: PlanPublico): boolean {
    if (plan.destacado === true) return true;
    // Fallback hasta que Dim_Plan/API expongan `destacado`
    return this.normalizarNivel(plan.nivel) === 'profesional';
  }

  slogan(plan: PlanPublico): string {
    switch (this.normalizarNivel(plan.nivel)) {
      case 'basico':
        return 'Ideal para flotas pequeñas que inician operaciones.';
      case 'profesional':
        return 'Cobertura ampliada para operación diaria con más severidades.';
      case 'empresarial':
        return 'Capacidad completa para redes regionales y alta demanda.';
      default:
        return 'Consulta límites y severidades incluidas en este plan.';
    }
  }

  cardClass(plan: PlanPublico): string {
    const base =
      'relative grid h-full content-start gap-4 rounded-[10px] border bg-bg-surface p-5 pt-6 transition-[border-color,box-shadow,transform] duration-200';
    if (this.esPopular(plan)) {
      return `${base} z-[1] border-2 border-accent-primary md:-translate-y-1`;
    }
    return `${base} border-border-default hover:border-accent-primary/35`;
  }

  ctaClass(plan: PlanPublico): string {
    const base =
      'mt-auto inline-flex min-h-11 w-full items-center justify-center rounded-lg px-5 text-center text-sm font-medium transition-colors';
    if (this.esPopular(plan)) {
      return `${base} bg-accent-primary text-white hover:bg-accent-hover`;
    }
    return `${base} border border-accent-primary bg-transparent text-accent-primary hover:bg-accent-primary/10`;
  }

  priceClass(plan: PlanPublico): string {
    const base = 'm-0 text-[2rem] font-bold leading-tight tracking-tight';
    return this.esPopular(plan) ? `${base} text-accent-primary` : `${base} text-text-primary`;
  }

  badgeClass(sev: SeveridadPlan): string {
    switch (sev) {
      case 'Alta':
        return 'bg-alert-urgent-bg text-alert-urgent';
      case 'Media':
        return 'bg-alert-warning-bg text-alert-warning';
      default:
        return 'bg-alert-success-bg text-alert-success';
    }
  }

  private labelDesdeClave(key: string): string {
    return key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
  }

  private formatearValor(raw: unknown): string {
    if (typeof raw === 'number') {
      return new Intl.NumberFormat('es-EC').format(raw);
    }
    return String(raw);
  }

  private normalizarNivel(nivel: string | null | undefined): string {
    return (nivel ?? '')
      .normalize('NFD')
      .replace(/\p{M}/gu, '')
      .trim()
      .toLowerCase();
  }
}
