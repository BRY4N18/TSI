import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

import { AuthApiService } from '../../modules/cuentas-clientes/auth/services/auth-api.service';
import { AlertHostComponent } from '../notifications/alert-host.component';
import { ToastHostComponent } from '../notifications/toast-host.component';
import { TablerIconComponent } from '../ui/icon/tabler-icon.component';
import { NAV_LINKS, NavLink } from './nav-links';

interface NavGroup {
  name: string;
  links: NavLink[];
}

@Component({
  selector: 'app-shell',
  standalone: true,
  imports: [
    RouterLink,
    RouterLinkActive,
    RouterOutlet,
    TablerIconComponent,
    ToastHostComponent,
    AlertHostComponent,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="flex min-h-screen flex-col bg-bg-page">
      <header
        class="relative flex h-16 shrink-0 items-center justify-between border-b border-border-default bg-bg-surface px-6"
      >
        <div class="flex shrink-0 items-center gap-3">
          <button
            type="button"
            class="flex h-9 w-9 items-center justify-center rounded-md border border-border-default text-text-primary sm:hidden"
            (click)="toggleSidebar()"
            aria-label="Abrir menú de navegación"
          >
            <app-tabler-icon name="menu" [size]="22" />
          </button>
          <div class="flex items-center gap-3">
            <span
              class="grid h-8 w-8 place-items-center rounded-md bg-accent-primary text-xs font-bold text-white"
              >TSI</span
            >
            <span class="text-sm font-semibold text-text-primary">Tráfico Seguro Integral</span>
          </div>
        </div>

        <!-- Buscador global: solo estructura visual, sin lógica de búsqueda todavía
             (pendiente hasta que exista un endpoint/índice de búsqueda global). -->
        <div class="flex flex-1 items-center justify-end sm:justify-center">
          <!-- Desktop/tablet: siempre visible, centrado -->
          <input
            type="search"
            class="hidden w-full max-w-sm rounded-full border border-border-default bg-bg-page px-3.5 py-2 text-sm text-text-primary placeholder:text-text-secondary disabled:cursor-not-allowed sm:block"
            placeholder="Buscar accidentes, expedientes, unidades…"
            disabled
          />

          <!-- Mobile: colapsa a ícono de lupa que expande el input -->
          @if (!searchExpanded()) {
            <button
              type="button"
              class="flex h-9 w-9 items-center justify-center text-text-secondary sm:hidden"
              (click)="toggleSearch()"
              aria-label="Buscar"
            >
              <app-tabler-icon name="search" [size]="18" />
            </button>
          } @else {
            <div
              class="absolute inset-x-0 top-16 border-b border-border-default bg-bg-surface p-3 sm:hidden"
            >
              <input
                type="search"
                class="w-full rounded-full border border-border-default bg-bg-page px-3.5 py-2 text-sm text-text-primary placeholder:text-text-secondary disabled:cursor-not-allowed"
                placeholder="Buscar accidentes, expedientes, unidades…"
                disabled
              />
            </div>
          }
        </div>

        <div class="flex shrink-0 items-center gap-3 text-sm">
          <!-- Selector de región: única opción fija; no hay endpoint de regiones
               disponible para el usuario autenticado todavía. -->
          <button
            type="button"
            class="flex h-9 w-9 items-center justify-center rounded-md border border-border-default text-text-secondary opacity-60 disabled:cursor-not-allowed"
            disabled
            title="Región: Todas las regiones"
          >
            <app-tabler-icon name="map-pin" [size]="20" />
          </button>

          <!-- Campana de notificaciones: sin fuente de datos todavía, sin contador. -->
          <div class="relative">
            <button
              type="button"
              class="flex h-9 w-9 items-center justify-center rounded-md border border-border-default text-text-secondary hover:bg-bg-page hover:text-text-primary"
              (click)="toggleNotifications()"
              aria-label="Notificaciones"
            >
              <app-tabler-icon name="bell" [size]="20" />
            </button>
            @if (notificationsOpen()) {
              <div
                class="absolute right-0 top-[calc(100%+0.5rem)] z-30 min-w-56 rounded-md border border-border-default bg-bg-surface p-3 text-xs text-text-secondary shadow-lg"
              >
                No hay notificaciones nuevas
              </div>
            }
          </div>

          @if (profile) {
            <span
              class="grid h-8 w-8 place-items-center rounded-full bg-accent-primary text-xs font-semibold text-white"
              >{{ initials }}</span
            >
            <span class="text-text-primary">{{ profile.gmail }}</span>
            <span
              class="rounded-full border border-border-default bg-bg-page px-2 py-0.5 text-xs text-text-secondary"
              >{{ profile.roles.join(', ') }}</span
            >
          }
          <button
            type="button"
            class="inline-flex items-center gap-1.5 rounded-md border border-border-default px-3 py-1.5 font-medium text-text-secondary hover:bg-bg-page hover:text-text-primary"
            (click)="logout()"
          >
            <app-tabler-icon name="logout" [size]="18" />
            Cerrar sesión
          </button>
        </div>
      </header>

      <div class="relative flex min-h-0 flex-1">
        @if (sidebarOpen()) {
          <div class="fixed inset-0 z-10 bg-black/40 sm:hidden" (click)="closeSidebar()"></div>
        }

        <aside
          class="fixed inset-y-0 top-16 z-20 flex w-60 shrink-0 -translate-x-full flex-col gap-6 overflow-y-auto border-r border-border-default bg-bg-surface p-3 shadow-lg transition-transform duration-200 sm:static sm:translate-x-0 sm:shadow-none"
          [class.translate-x-0]="sidebarOpen()"
        >
          @if (navGroups().length) {
            @for (group of navGroups(); track group.name) {
              <div class="flex flex-col gap-1">
                <span
                  class="mb-1 px-3 text-[0.7rem] font-medium uppercase tracking-wide text-text-secondary"
                  >{{ group.name }}</span
                >
                @for (link of group.links; track link.path) {
                  <a
                    class="flex items-center gap-3 rounded-md border-l-4 px-3 py-2.5 text-sm font-medium transition-colors"
                    [routerLink]="link.path"
                    routerLinkActive
                    #rla="routerLinkActive"
                    [class.border-transparent]="!rla.isActive"
                    [class.text-text-secondary]="!rla.isActive"
                    [class.hover:bg-bg-page]="!rla.isActive"
                    [class.hover:text-text-primary]="!rla.isActive"
                    [class.border-accent-primary]="rla.isActive"
                    [class.text-accent-primary]="rla.isActive"
                    [class.font-semibold]="rla.isActive"
                    [style.background-color]="rla.isActive ? 'rgba(46,111,242,0.1)' : null"
                    [title]="link.description"
                    (click)="closeSidebar()"
                  >
                    <app-tabler-icon [name]="link.icon" [size]="24" />
                    <span>{{ link.label }}</span>
                  </a>
                }
              </div>
            }
          } @else {
            <p class="p-2 text-sm text-text-secondary">
              Tu rol no tiene módulos operativos asignados todavía.
            </p>
          }
        </aside>

        <main class="min-w-0 flex-1 overflow-auto">
          <router-outlet />
        </main>
      </div>
    </div>

    <app-toast-host />
    <app-alert-host />
  `,
})
export class AppShellComponent {
  private readonly authApi = inject(AuthApiService);
  private readonly router = inject(Router);

  readonly profile = this.authApi.getProfile();
  readonly sidebarOpen = signal(false);
  readonly searchExpanded = signal(false);
  readonly notificationsOpen = signal(false);

  private readonly availableLinks = NAV_LINKS.filter((link) =>
    link.roles.some((role) => this.authApi.hasRole(role)),
  );

  readonly navGroups = computed<NavGroup[]>(() => {
    const order: string[] = [];
    const byGroup = new Map<string, NavLink[]>();

    for (const link of this.availableLinks) {
      if (!byGroup.has(link.group)) {
        byGroup.set(link.group, []);
        order.push(link.group);
      }
      byGroup.get(link.group)!.push(link);
    }

    return order.map((name) => ({ name, links: byGroup.get(name)! }));
  });

  get initials(): string {
    const gmail = this.profile?.gmail ?? '';
    const local = gmail.split('@')[0] ?? '';
    const parts = local.split(/[._-]/).filter(Boolean);
    const chars = parts.length >= 2 ? [parts[0][0], parts[1][0]] : [local[0] ?? '?'];
    return chars.join('').toUpperCase();
  }

  toggleSidebar(): void {
    this.sidebarOpen.update((open) => !open);
  }

  closeSidebar(): void {
    this.sidebarOpen.set(false);
  }

  toggleSearch(): void {
    this.searchExpanded.update((open) => !open);
  }

  toggleNotifications(): void {
    this.notificationsOpen.update((open) => !open);
  }

  logout(): void {
    this.authApi.logout().subscribe({
      next: () => {
        this.authApi.clearSession();
        void this.router.navigate(['/cuentas-clientes/auth/login']);
      },
      error: () => {
        this.authApi.clearSession();
        void this.router.navigate(['/cuentas-clientes/auth/login']);
      },
    });
  }
}
