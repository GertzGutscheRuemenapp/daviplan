import { Component } from '@angular/core';
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

  constructor(router: Router, dialog: MatDialog, authService: AuthService) {

    // auto apply site settings when new ones were fetched
    authService.settings.getSiteSettings().subscribe(settings => {
      authService.settings.fetchProjectSettings();
      authService.settings.fetchBaseDataSettings();
      authService.settings.applySiteSettings(settings);
      // initialize authentication cycle by refreshing access token
      if (authService.hasPreviousLogin())
        authService.refreshToken().subscribe();
      // fetch demo user in demo mode if not logged in
      else if (settings.demoMode) {
        authService.fetchCurrentUser().subscribe((user) => {
          if (user)
            authService.login({ username: user.username, password: '-' }).subscribe();
        });
      }
    })
    router.events.pipe(
      tap(() => {
        // close all dialogs on page change (esp. help dialogs)
        dialog.closeAll();
      })
    ).subscribe();
  }
}
