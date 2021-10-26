import { AfterViewInit, Component, OnDestroy, OnInit } from '@angular/core';
import { environment } from "../../../../environments/environment";
import { MapControl, MapService } from "../../../map/map.service";

@Component({
  selector: 'app-statistics',
  templateUrl: './statistics.component.html',
  styleUrls: ['./statistics.component.scss']
})
export class StatisticsComponent implements AfterViewInit, OnDestroy {
  backend: string = environment.backend;
  mapControl?: MapControl;
  years = [2013, 2014, 2015];
  selectedYear = 2013;
  theme = 'wanderung';

  constructor(private mapService: MapService) {
  }

  ngAfterViewInit(): void {
    this.mapControl = this.mapService.get('base-statistics-map');
  }

  ngOnDestroy(): void {
    this.mapControl?.destroy();
  }
}
