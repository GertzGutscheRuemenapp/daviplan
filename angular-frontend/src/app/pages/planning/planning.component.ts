import { Component, ElementRef, AfterViewInit, Renderer2, OnDestroy } from '@angular/core';
import { MapService } from "../../map/map.service";

@Component({
  selector: 'app-planning',
  templateUrl: './planning.component.html',
  styleUrls: ['./planning.component.scss']
})
export class PlanningComponent implements AfterViewInit, OnDestroy {

  constructor(private renderer: Renderer2, private elRef: ElementRef, private mapService: MapService) {  }

  ngAfterViewInit(): void {
    // there is no parent css selector yet but we only want to hide the overflow in the planning pages
    let wrapper = this.elRef.nativeElement.closest('mat-sidenav-content');
    this.renderer.setStyle(wrapper, 'overflow', 'hidden');
    this.mapService.create('planning-map');
  }

  ngOnDestroy(): void {
    this.mapService.remove('planning-map');
  }

}
