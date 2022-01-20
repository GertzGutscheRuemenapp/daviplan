import { AfterViewInit, Component, Input, OnInit, ViewChild } from '@angular/core';
import { EcoFabSpeedDialComponent } from "@ecodev/fab-speed-dial";
import { MapControl, MapService } from "../map.service";

@Component({
  selector: 'app-map-controls',
  templateUrl: './map-controls.component.html',
  styleUrls: ['./map-controls.component.scss']
})
export class MapControlsComponent implements AfterViewInit {
  @Input() target!: string;
  @Input() showOnHover?: boolean = false;

  @ViewChild('leftDial') leftDial?: EcoFabSpeedDialComponent;
  @ViewChild('rightDial') rightDial?: EcoFabSpeedDialComponent;
  @ViewChild('leftDialBack') leftDialBack?: HTMLElement;

  mapControl!: MapControl;
  expanded: boolean = false;

  constructor(private mapService: MapService) { }

  ngAfterViewInit (): void {
    this.mapControl = this.mapService.get(this.target);
  }

  action(a: string): void {}

  zoomIn(): void {
    this.mapControl?.map?.zoom(1);
  }

  zoomOut(): void {
    this.mapControl?.map?.zoom(-1);
  }

  toggleFullscreen(): void {
    this.mapControl?.map?.toggleFullscreen();
  }

  savePNG(): void {
    this.mapControl?.map?.savePNG();
  }

  toggle(): void {
    this.leftDial?.toggle();
    this.rightDial?.toggle();
    this.expanded = !this.expanded;
  }

}
