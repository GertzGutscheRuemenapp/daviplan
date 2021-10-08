import { AfterViewInit, Component, OnDestroy } from '@angular/core';
import { MapControl, MapService } from "../../../map/map.service";
import { mockAreaLevels, mockPresetLevels } from "../areas/areas";

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
  }

  ngOnDestroy(): void {
    this.mapControl?.destroy();
  }

}
