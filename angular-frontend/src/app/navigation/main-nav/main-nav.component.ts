import { Component, OnInit } from '@angular/core';
import { BreakpointObserver, Breakpoints } from '@angular/cdk/layout';
import { Observable } from 'rxjs';
import { map, share, shareReplay } from 'rxjs/operators';
import { User } from "../../login/users";
import { AuthService } from "../../auth.service";
import {Router} from "@angular/router";

@Component({
  selector: 'app-main-nav',
  templateUrl: './main-nav.component.html',
  styleUrls: ['./main-nav.component.scss']
})
export class MainNavComponent implements OnInit{

  user?: User;
  user$?: Observable<User>;

  menuItems = [
    {name:  $localize`Bevölkerung`, url: 'bevoelkerung'},
    {name:  $localize`Infrastrukturplanung`, url: 'planung'},
    {name:  $localize`Grundlagendaten`, url: 'daten'},
    {name:  $localize`Administration`, url: 'admin'}
  ];

  isHandset$: Observable<boolean> = this.breakpointObserver.observe(Breakpoints.Handset)
    .pipe(
      map(result => result.matches),
      shareReplay()
    );

  constructor(private breakpointObserver: BreakpointObserver, private auth: AuthService,
              private router: Router) {}

  ngOnInit(): void {
    this.user$ = this.auth.getCurrentUser().pipe(share());
    this.user$.subscribe(user=> {
      this.user = user
    });
  }

  logout(): void {
    this.auth.logout();
    this.router.navigate(['/login']);
  }
}
