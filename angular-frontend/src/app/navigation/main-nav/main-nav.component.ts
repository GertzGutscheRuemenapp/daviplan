import { Component, OnInit } from '@angular/core';
import { BreakpointObserver, Breakpoints } from '@angular/cdk/layout';
import { Observable } from 'rxjs';
import { share } from 'rxjs/operators';
import { User } from "../../pages/login/users";
import { AuthService } from "../../auth.service";
import {Router} from "@angular/router";
import { environment } from "../../../environments/environment";

@Component({
  selector: 'app-main-nav',
  templateUrl: './main-nav.component.html',
  styleUrls: ['./main-nav.component.scss']
})
export class MainNavComponent implements OnInit{

  user?: User;
  user$?: Observable<User | undefined>;
  backend: string = environment.backend;

  menuItems: { name: string, url: string }[] = [];

  constructor(private breakpointObserver: BreakpointObserver, private auth: AuthService, private router: Router) { }

  ngOnInit(): void {
    this.user$ = this.auth.getCurrentUser().pipe(share());
    this.user$.subscribe(user=> {
      this.user = user;
      this.buildMenu();
    });
  }

  buildMenu(): void {
    if (this.user)
      this.menuItems = [
        { name:  $localize`Bevölkerung`, url: 'bevoelkerung' },
        { name:  $localize`Infrastrukturplanung`, url: 'planung' },
        { name:  $localize`Grundlagendaten`, url: 'grundlagendaten' },
        { name:  $localize`Administration`, url: 'admin' }
      ];
  }

  logout(): void {
    this.auth.logout();
    this.router.navigate(['/login']);
  }
}
