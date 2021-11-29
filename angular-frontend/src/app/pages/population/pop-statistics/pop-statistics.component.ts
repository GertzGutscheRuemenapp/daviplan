import {AfterViewInit, Component, OnDestroy} from '@angular/core';
import { OlMap } from "../../../map/map";
import { MapControl, MapService } from "../../../map/map.service";
import { PopService } from "../population.component";
import { environment } from "../../../../environments/environment";
import { Observable } from "rxjs";
import { map, shareReplay } from "rxjs/operators";
import { BreakpointObserver } from "@angular/cdk/layout";
import { MultilineData } from "../../../diagrams/multiline-chart/multiline-chart.component";

export const mockTotalData: MultilineData[] = [
  { group: '2000', values: [0] },
  { group: '2001', values: [-10] },
  { group: '2002', values: [-50] },
  { group: '2003', values: [-12] },
  { group: '2004', values: [-40] },
  { group: '2005', values: [-21] },
  { group: '2006', values: [2] },
  { group: '2007', values: [32] },
  { group: '2008', values: [12] },
  { group: '2009', values: [3] },
  { group: '2010', values: [-4] },
  { group: '2011', values: [15] },
  { group: '2012', values: [12] },
  { group: '2013', values: [-6] },
  { group: '2014', values: [21] },
  { group: '2015', values: [-23] }
]

@Component({
  selector: 'app-pop-statistics',
  templateUrl: './pop-statistics.component.html',
  styleUrls: ['./pop-statistics.component.scss']
})
export class PopStatisticsComponent implements AfterViewInit {
  mapControl?: MapControl;
  backend: string = environment.backend;
  theme = 'wanderung';
  isSM$: Observable<boolean> = this.breakpointObserver.observe('(max-width: 50em)')
    .pipe(
      map(result => result.matches),
      shareReplay()
    );
  totalData: MultilineData[] = mockTotalData;

  constructor(private breakpointObserver: BreakpointObserver, private mapService: MapService, private popService: PopService) {
  }

  ngAfterViewInit(): void {
    this.mapControl = this.mapService.get('population-map');
    this.mapControl.mapDescription = 'Bevölkerungsstatistik > Gemeinden | Wanderung';
    if (this.popService.timeSlider)
      this.setSlider();
    else
      this.popService.ready.subscribe(r => this.setSlider());
  }

  setSlider(): void {
    let slider = this.popService.timeSlider!;
    slider.prognosisEnd = 0;
    slider.years = [2012, 2013, 2014, 2015, 2016];
    slider.value = 2012;
    slider.draw();
  }
}
