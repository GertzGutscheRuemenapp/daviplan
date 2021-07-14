import { Component } from '@angular/core';
import { BreakpointObserver, Breakpoints } from '@angular/cdk/layout';
import { Observable } from 'rxjs';
import { map, shareReplay } from 'rxjs/operators';

@Component({
  selector: 'app-main-nav',
  templateUrl: './main-nav.component.html',
  styleUrls: ['./main-nav.component.scss']
})
export class MainNavComponent {

  menuItems = [
    {name:  $localize`Bevölkerung`, url: 'bevoelkerung'},
    {name:  $localize`Infrastrukturplanung`, url: 'infrastruktur'},
    {name:  $localize`Grundlagendaten`, url: 'daten'},
    {name:  $localize`Administration`, url: 'admin'}
  ];

  isHandset$: Observable<boolean> = this.breakpointObserver.observe(Breakpoints.Handset)
    .pipe(
      map(result => result.matches),
      shareReplay()
    );

  constructor(private breakpointObserver: BreakpointObserver) {}

}
