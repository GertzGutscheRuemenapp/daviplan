import {AfterViewInit, Component, OnDestroy} from '@angular/core';
import { OlMap } from "../../../map/map";
import { MapService } from "../../../map/map.service";

@Component({
  selector: 'app-pop-statistics',
  templateUrl: './pop-statistics.component.html',
  styleUrls: ['./pop-statistics.component.scss']
})
export class PopStatisticsComponent implements AfterViewInit, OnDestroy {
  map?: OlMap;

  constructor(private mapService: MapService) { }

  ngAfterViewInit(): void {
    this.map = this.mapService.create('stat-map');
  }

  ngOnDestroy(): void {
    this.mapService.remove('stat-map');
  }
}
