import { ViewContainerRef, Directive, HostListener, Input, OnInit, Component, EventEmitter } from '@angular/core';
import { MatExpansionPanel } from "@angular/material/expansion";
import { CookieService } from "./cookies.service";
import { SideToggleComponent } from "../elements/side-toggle/side-toggle.component";

@Directive({
  selector: '[cookieExpansion]'
})
export class CookieExpansionDirective implements OnInit {
  @Input() cookieExpansion = '';
  @Input() initiallyExpanded = false;
  component!: MatExpansionPanel | SideToggleComponent;

  constructor(private host: ViewContainerRef , private cookies: CookieService) {
    // @ts-ignore
    this.component = this.host._hostLView[this.host._hostTNode.directiveStart];
  }

  ngOnInit() {
    let expand: any = this.initiallyExpanded;
    if (!this.cookies.has(this.cookieExpansion)){
      this.cookies.set(this.cookieExpansion, expand);
    }
    else {
      expand = this.cookies.get(this.cookieExpansion);
    }
    if (expand != this.component.expanded)
      this.component.toggle();
    this.component.opened.subscribe(x => {
      this.cookies.set(this.cookieExpansion, true)
    });
    this.component.closed.subscribe(x => {
      this.cookies.set(this.cookieExpansion, false)
    });
  }

}
