import { Directive, HostListener, Input, OnInit } from '@angular/core';
import { MatExpansionPanel } from "@angular/material/expansion";
import { CookieService } from "./cookies.service";

@Directive({
  selector: '[cookieExpansion]'
})
export class CookieExpansionDirective implements OnInit {
  @Input() cookieExpansion = '';
  @Input() cookieExpansionInit = false;

  constructor(private host: MatExpansionPanel, private cookies: CookieService) {
  }

  ngOnInit() {
    let expand: any = this.cookieExpansionInit;
    if (!this.cookies.has(this.cookieExpansion)){
      this.cookies.set(this.cookieExpansion, expand);
    }
    else {
      expand = this.cookies.get(this.cookieExpansion);
    }
    if (expand != this.host.expanded)
      this.host.toggle();
  }

  @HostListener('opened') onOpen() {
    this.cookies.set(this.cookieExpansion, true);
  }
  @HostListener('closed') onClose() {
    this.cookies.set(this.cookieExpansion, false);
  }

}
