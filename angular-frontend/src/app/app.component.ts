import { Component } from '@angular/core';
import { SettingsService } from "./settings.service";
import { MatDialog } from "@angular/material/dialog";
import { Router } from "@angular/router";
import { tap } from "rxjs/operators";
import { AuthService } from "./auth.service";

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent {

  constructor(private settings: SettingsService, router: Router, dialog: MatDialog, authService: AuthService) {
    authService.refreshToken().subscribe();
    // auto apply site settings when new ones were fetched
    settings.siteSettings$.subscribe(settings => {
      this.settings.applySiteSettings(settings);
    })
    router.events.pipe(
      tap(() => {
        // close all dialogs on page change
        dialog.closeAll();
      })
    ).subscribe();
  }
}
