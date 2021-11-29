import { Component } from '@angular/core';
import { SettingsService } from "./settings.service";
import { MatDialog } from "@angular/material/dialog";
import { Router } from "@angular/router";
import { tap } from "rxjs/operators";

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent {

  constructor(private settings: SettingsService, router: Router, dialog: MatDialog) {
    // auto apply settings when new ones were fetched
    // ToDo: is this the right place for this?
    settings.siteSettings$.subscribe(settings => {
      this.settings.applySettings(settings);
    })
    router.events.pipe(
      tap(() => dialog.closeAll())
    ).subscribe();
  }
}
