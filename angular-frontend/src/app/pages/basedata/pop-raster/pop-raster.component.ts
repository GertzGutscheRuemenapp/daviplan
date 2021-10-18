import { AfterViewInit, Component, OnDestroy } from '@angular/core';
import { MapControl, MapService } from "../../../map/map.service";

@Component({
  selector: 'app-pop-raster',
  templateUrl: './pop-raster.component.html',
  styleUrls: ['./pop-raster.component.scss']
})
export class PopRasterComponent implements AfterViewInit, OnDestroy {
  mapControl?: MapControl;

  constructor(private mapService: MapService) { }

  ngAfterViewInit(): void {
    this.mapControl = this.mapService.get('base-raster-map');
    this.mapControl.setBackground(this.mapControl.getBackgroundLayers()[0].id)
  }

  ngOnDestroy(): void {
    this.mapControl?.destroy();
  }

}
