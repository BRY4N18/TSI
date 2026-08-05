import { Component, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';

import { EvidenciaSyncSchedulerService } from './modules/evidencia-unidad/services/evidencia-sync-scheduler.service';
import { AlertHostComponent } from './shared/notifications/alert-host.component';
import { ConfirmDialogHostComponent } from './shared/notifications/confirm-dialog-host.component';
import { ToastHostComponent } from './shared/notifications/toast-host.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, ToastHostComponent, AlertHostComponent, ConfirmDialogHostComponent],
  template: `
    <router-outlet />
    <app-toast-host />
    <app-alert-host />
    <app-confirm-dialog-host />
  `,
})
export class AppComponent {
  private readonly evidenciaSyncScheduler = inject(EvidenciaSyncSchedulerService);

  constructor() {
    this.evidenciaSyncScheduler.iniciarAutoSync();
  }
}
