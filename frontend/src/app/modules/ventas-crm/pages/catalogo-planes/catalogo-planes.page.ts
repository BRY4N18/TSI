import { CommonModule, CurrencyPipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { BrandMarkComponent } from '../../../../shared/brand/brand-mark.component';
import { TablerIconComponent, TablerIconName } from '../../../../shared/ui/icon/tabler-icon.component';
import { PlanPublico, SeveridadPlan } from '../../models/prospectos.types';
import { PlanesApiService } from '../../services/planes-api.service';

export interface LimiteItem {
  /** Clave original del JSON de límites; sirve para buscar su explicación. */
  clave: string;
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
  api_calls_minuto: 'Llamadas API / minuto',
};

/**
 * Qué significa cada límite, en una frase.
 *
 * El nombre de la métrica ("Unidades máx.") le dice al cliente **cuánto**, pero
 * no **de qué** ni por qué le importa. La revisión del 24/08/2026 (hallazgo #2)
 * lo señaló: «puede haber términos que un cliente nuevo no entienda, a
 * diferencia de un cliente habitual».
 */
const AYUDA_LIMITES: Record<string, string> = {
  unidades_max: 'Ambulancias, grúas o patrullas que puedes tener dadas de alta.',
  usuarios_max: 'Personas de tu equipo con acceso a la plataforma.',
  api_calls_mes: 'Consultas que tus propios sistemas pueden hacer al mes.',
  api_calls_minuto: 'Ritmo máximo de esas consultas.',
};

/**
 * Traducción del vocabulario de severidad a lo que un cliente reconoce.
 *
 * ⚠️ Hay **dos** vocabularios en el sistema: los planes hablan de severidad
 * `Baja | Media | Alta` y los accidentes de `Leve | Moderado | Grave | Fatal`
 * (`Dim_Severidad`). Que no coincidan ya era un problema conocido —lo documenta
 * `database/seed_severidad.py`— y para quien compra es directamente ilegible.
 * Aquí se explica cada nivel con casos reales en vez de con la etiqueta.
 */
const SEVERIDAD_EXPLICADA: Record<string, { titulo: string; ejemplo: string }> = {
  Leve: {
    titulo: 'Incidentes leves',
    ejemplo: 'Roces y daños materiales, sin personas heridas.',
  },
  Moderado: {
    titulo: 'Accidentes con heridos',
    ejemplo: 'Colisiones con personas lesionadas que requieren atención en sitio.',
  },
  Grave: {
    titulo: 'Emergencias graves',
    ejemplo: 'Heridos de gravedad o siniestros con varios vehículos implicados.',
  },
  Fatal: {
    titulo: 'Siniestros con víctimas mortales',
    ejemplo: 'Casos con fallecidos, que exigen la respuesta más amplia.',
  },
};

@Component({
  selector: 'app-catalogo-planes',
  standalone: true,
  imports: [CommonModule, RouterLink, CurrencyPipe, TablerIconComponent, BrandMarkComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './catalogo-planes.page.html',
})
export class CatalogoPlanesPage implements OnInit {
  private readonly api = inject(PlanesApiService);

  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly planes = signal<PlanPublico[]>([]);
  readonly year = new Date().getFullYear();

  /**
   * El ciclo en tres pasos, antes de hablar de precios.
   *
   * Sin esto, un visitante nuevo llega a la tabla de planes sin saber qué
   * compra; los "límites" y las "severidades" no significan nada hasta que se
   * entiende el flujo (hallazgo #1).
   */
  /** Los tres niveles, en orden ascendente de gravedad. */
  readonly nivelesSeveridad: SeveridadPlan[] = ['Leve', 'Moderado', 'Grave', 'Fatal'];

  readonly comoFunciona = [
    {
      titulo: 'Se reporta el accidente',
      detalle:
        'Tu operador registra qué pasó, dónde y con cuántos implicados. El sistema valida los datos críticos en el momento.',
    },
    {
      titulo: 'Sale la unidad adecuada',
      detalle:
        'TSI busca entre tus unidades disponibles la más cercana que pueda atender ese tipo de emergencia, y la despacha.',
    },
    {
      titulo: 'Sigues el caso hasta el cierre',
      detalle:
        'Ves la unidad en ruta, lo que registra en el sitio y el expediente completo cuando termina la atención.',
    },
  ];

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

  /** Explicación en una frase de un límite; vacío si no la hay. */
  ayudaLimite(clave: string): string {
    return AYUDA_LIMITES[clave] ?? '';
  }

  explicacionSeveridad(sev: SeveridadPlan): { titulo: string; ejemplo: string } | null {
    return SEVERIDAD_EXPLICADA[sev] ?? null;
  }

  /**
   * Lo que el plan permite atender, en una frase entendible.
   *
   * "Severidades desbloqueadas: Alta, Media" no le dice a un cliente nuevo qué
   * está comprando. Esto sí (hallazgo #2).
   */
  queAtiende(plan: PlanPublico): string {
    const niveles = plan.severidades_desbloqueadas ?? [];
    if (!niveles.length) {
      return 'Consulta con el equipo comercial qué tipos de emergencia cubre este plan.';
    }
    const titulos = niveles
      .map((s) => SEVERIDAD_EXPLICADA[s]?.titulo.toLowerCase())
      .filter((t): t is string => !!t);
    if (!titulos.length) {
      return 'Consulta con el equipo comercial qué tipos de emergencia cubre este plan.';
    }
    const listado =
      titulos.length === 1
        ? titulos[0]
        : `${titulos.slice(0, -1).join(', ')} y ${titulos[titulos.length - 1]}`;
    return `Tu flota puede atender ${listado}.`;
  }

  /** A quién le sirve el plan, para que la elección no sea solo por precio. */
  paraQuien(plan: PlanPublico): string {
    switch (this.normalizarNivel(plan.nivel)) {
      case 'basico':
        return 'Para empezar: una flota pequeña que atiende su propia zona.';
      case 'profesional':
        return 'Para operar a diario: varias unidades y turnos que se cubren entre sí.';
      case 'empresarial':
        return 'Para redes grandes: cobertura regional e integración con tus sistemas.';
      default:
        return '';
    }
  }

  limitesComoLista(limites: string): LimiteItem[] {
    if (!limites?.trim()) {
      return [{ clave: '', label: 'Límites', value: 'Sin detalle' }];
    }
    try {
      const parsed = JSON.parse(limites) as Record<string, unknown>;
      return Object.entries(parsed).map(([key, raw]) => ({
        clave: key,
        label: LABELS_LIMITES[key] ?? this.labelDesdeClave(key),
        value: this.formatearValor(raw),
      }));
    } catch {
      return [{ clave: '', label: 'Detalle', value: limites }];
    }
  }

  esPopular(plan: PlanPublico): boolean {
    if (typeof plan.destacado === 'boolean') {
      return plan.destacado;
    }
    // Fallback: solo planes comerciales activos con precio real y no demo
    return (plan.precio ?? 0) > 0 && this.normalizarNivel(plan.nivel) === 'profesional' && !plan.nombre.toLowerCase().includes('demo');
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
      'relative grid h-full content-start gap-4 rounded-md border bg-bg-surface p-5 pt-6 transition-[border-color,box-shadow,transform] duration-200';
    if (this.esPopular(plan)) {
      return `${base} z-[1] border-2 border-accent-primary md:-translate-y-1`;
    }
    return `${base} border-border-default hover:border-accent-primary/35`;
  }

  ctaClass(plan: PlanPublico): string {
    // El CTA del plan usa las clases canonicas de boton (design-system.md §5)
    // en vez de repintar el primario/ghost a mano.
    const base = 'tsi-btn mt-auto w-full text-center no-underline';
    return this.esPopular(plan) ? `${base} tsi-btn-primary` : `${base} tsi-btn-ghost`;
  }

  priceClass(plan: PlanPublico): string {
    const base = 'm-0 text-[2rem] font-bold leading-tight tracking-tight';
    return this.esPopular(plan) ? `${base} text-accent-primary` : `${base} text-text-primary`;
  }

  badgeClass(sev: SeveridadPlan): string {
    // ⚠️ Los casos eran 'Alta'/'Media', vocabulario que la API dejó de devolver
    // en la migración del 2026-08-11: TODO caía al `default` y hasta un plan
    // que cubre siniestros fatales se pintaba en verde (hallazgo #2).
    switch (sev) {
      case 'Fatal':
        return 'bg-alert-critical-bg text-alert-critical';
      case 'Grave':
        return 'bg-alert-urgent-bg text-alert-urgent';
      case 'Moderado':
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
