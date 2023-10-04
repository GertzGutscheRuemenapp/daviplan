import { Component } from '@angular/core';
import { MatDialog } from "@angular/material/dialog";
import { Router } from "@angular/router";
import { share, tap } from "rxjs/operators";
import { AuthService } from "./auth.service";

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent {

  constructor(private router: Router, dialog: MatDialog, private authService: AuthService) {
    authService.settings.getSiteSettings().subscribe(() => {
      // initialize authentication cycle by refreshing access token
      if (authService.hasPreviousLogin()) {
        authService.refreshToken().subscribe(() => {
            authService.fetchCurrentUser().subscribe(() => this.authService.settings.init());
          },
          error => {
            this.demoLogin();
          }
        );
      }
      // fetch demo user in demo mode if not logged in
      else {
        this.demoLogin();
      }
    }, error => {
      this.demoLogin();
    })
    router.events.pipe(
      tap(() => {
        // close all dialogs on page change (esp. help dialogs)
        dialog.closeAll();
      })
    ).subscribe();
  }

  demoLogin(): void {
    if (this.authService.settings.siteSettings$.value.demoMode) {
      this.authService.fetchCurrentUser().subscribe((user) => {
        if (user)
          this.authService.login({ username: user.username, password: '-' }).subscribe(
            () => this.router.navigateByUrl('/')
          );
      });
    }
  }
}
