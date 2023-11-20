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
    this.router.events.pipe(
      tap(() => {
        // close all dialogs on page change (esp. help dialogs)
        dialog.closeAll();
      })
    ).subscribe();
    this.init();
  }

  init(): void {
    this.authService.settings.getSiteSettings().subscribe(() => {
      // initialize authentication cycle by refreshing access token
      if (this.authService.hasPreviousLogin()) {
        this.authService.refreshToken().subscribe(() => {
            this.authService.fetchCurrentUser().subscribe(() => this.authService.settings.init());
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
  }

  demoLogin(): void {
    if (this.authService.settings.siteSettings$.value.demoMode) {
      this.authService.fetchCurrentUser().subscribe((user) => {
        if (user)
          this.authService.login({ username: user.username, password: '-' }).subscribe(
            () => this.init()
          );
        else
          this.router.navigateByUrl('/login');
      }, error => {
        this.router.navigateByUrl('/login');
      });
    }
    else
      this.router.navigateByUrl('/login');
  }
}
