import { Component, AfterViewInit, OnDestroy } from '@angular/core';
import { MapService } from "../../../map/map.service";
import { OlMap } from "../../../map/map";
import { BarData } from "../../../diagrams/stacked-barchart/stacked-barchart.component";

const mockdata: BarData[] = [
  { year: 2000, count: 100 },
  { year: 2001, count: 200 },
  { year: 2002, count: 300 },
]

@Component({
  selector: 'app-pop-development',
  templateUrl: './pop-development.component.html',
  styleUrls: ['./pop-development.component.scss']
})
export class PopDevelopmentComponent implements AfterViewInit, OnDestroy {
  map?: OlMap;
  data: BarData[] = mockdata;

  constructor(private mapService: MapService) { }

  ngAfterViewInit(): void {
    this.map = this.mapService.create('pop-map');
  }

  ngOnDestroy(): void {
    this.mapService.remove('pop-map');
  }

}
