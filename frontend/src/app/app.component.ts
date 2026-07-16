import { Component, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';

import { EvidenciaSyncSchedulerService } from './modules/evidencia-unidad/services/evidencia-sync-scheduler.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet],
  template: `<router-outlet />`,
})
export class AppComponent {
  private readonly evidenciaSyncScheduler = inject(EvidenciaSyncSchedulerService);

  constructor() {
    this.evidenciaSyncScheduler.iniciarAutoSync();
  }
}
