import { Component, AfterViewInit, OnDestroy } from '@angular/core';
import { MapService } from "../../../map/map.service";
import { OlMap } from "../../../map/map";
import { StackedData } from "../../../diagrams/stacked-barchart/stacked-barchart.component";

const mockdata: StackedData[] = [
  { year: 2000, values: [200, 300, 280] },
  { year: 2001, values: [190, 310, 290] },
  { year: 2002, values: [192, 335, 293] },
  { year: 2003, values: [195, 340, 295] },
  { year: 2004, values: [189, 342, 293] },
  { year: 2005, values: [182, 345, 300] },
  { year: 2006, values: [176, 345, 298] },
]

@Component({
  selector: 'app-pop-development',
  templateUrl: './pop-development.component.html',
  styleUrls: ['./pop-development.component.scss']
})
export class PopDevelopmentComponent implements AfterViewInit, OnDestroy {
  map?: OlMap;
  data: StackedData[] = mockdata;

  constructor(private mapService: MapService) { }

  ngAfterViewInit(): void {
    this.map = this.mapService.create('pop-map');
  }

  ngOnDestroy(): void {
    this.mapService.remove('pop-map');
  }

}
