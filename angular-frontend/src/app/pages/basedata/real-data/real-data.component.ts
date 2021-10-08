import { AfterViewInit, Component, OnDestroy, OnInit } from '@angular/core';
import { mockAreaLevels, mockPresetLevels } from "../areas/areas";
import { MapControl, MapService } from "../../../map/map.service";

@Component({
  selector: 'app-real-data',
  templateUrl: './real-data.component.html',
  styleUrls: ['./real-data.component.scss']
})
export class RealDataComponent implements AfterViewInit, OnDestroy {
  mapControl?: MapControl;
  years = [2013, 2014, 2015];
  selectedYear = 2013;

  constructor(private mapService: MapService) { }

  ngAfterViewInit(): void {
    this.mapControl = this.mapService.get('base-real-data-map');
  }

  ngOnDestroy(): void {
    this.mapControl?.destroy();
  }
}
