import { Component, ElementRef, AfterViewInit, Renderer2, ViewChild } from '@angular/core';

@Component({
  selector: 'app-planning',
  templateUrl: './planning.component.html',
  styleUrls: ['./planning.component.scss']
})
export class PlanningComponent implements AfterViewInit {

  constructor(private renderer: Renderer2, private elRef: ElementRef) {  }

  ngAfterViewInit(): void {
    // there is no parent css selector yet but we only want to hide the overflow in the planning pages
    let wrapper = this.elRef.nativeElement.closest('mat-sidenav-container');
    this.renderer.setStyle(wrapper.nativeElement, 'overflow', 'hidden');
  }

  public onMapReady(event:any) {
    console.log("Map Ready")
  }
}
