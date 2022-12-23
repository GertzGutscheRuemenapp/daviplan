import { Component, Input } from '@angular/core';
import { BreakpointObserver, Breakpoints } from '@angular/cdk/layout';
import { Observable } from 'rxjs';
import { map, shareReplay } from 'rxjs/operators';
import { CookieService } from "../../helpers/cookies.service";

type Link = {
  name: string;
  url: string;
  icon?: string;
  davicon?: string;
  children: Link[];
}

@Component({
  selector: 'app-side-nav',
  templateUrl: './side-nav.component.html',
  styleUrls: ['./side-nav.component.scss']
})

export class SideNavComponent {
  @Input() menuItems: Link[] = [];
  @Input() marginRight: string = '20px';
  @Input() marginTop: string = '100px';
  @Input() width: string = '300px';
  prefix = 'exp-nav-';
  isHandset$: Observable<boolean> = this.breakpointObserver.observe(Breakpoints.Handset)
    .pipe(
      map(result => result.matches),
      shareReplay()
    );

  constructor(private breakpointObserver: BreakpointObserver) {}

}
