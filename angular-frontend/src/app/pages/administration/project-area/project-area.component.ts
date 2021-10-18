import { AfterViewInit, Component, OnDestroy, OnInit } from '@angular/core';
import { MapControl, MapService } from "../../../map/map.service";

@Component({
  selector: 'app-project-area',
  templateUrl: './project-area.component.html',
  styleUrls: ['./project-area.component.scss']
})
export class ProjectAreaComponent implements AfterViewInit, OnDestroy {
  mapControl?: MapControl;

  constructor(private mapService: MapService) { }

  ngAfterViewInit(): void {
    this.mapControl = this.mapService.get('project-area-map');
    this.mapControl.setBackground(this.mapControl.getBackgroundLayers()[0].id)
  }

  ngOnDestroy(): void {
    this.mapControl?.destroy();
  }

}
