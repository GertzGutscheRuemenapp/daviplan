import { AfterViewInit, Component, OnDestroy, ViewChild } from '@angular/core';
import { MapControl, MapService } from "../../../map/map.service";
import { StackedData } from "../../../diagrams/stacked-barchart/stacked-barchart.component";
import { mockdata } from "../../population/pop-development/pop-development.component"
import { MultilineChartComponent } from "../../../diagrams/multiline-chart/multiline-chart.component";


export const mockPrognoses = ['Trendfortschreibung', 'mehr Zuwanderung', 'mehr Abwanderung'];

@Component({
  selector: 'app-prognosis-data',
  templateUrl: './prognosis-data.component.html',
  styleUrls: ['./prognosis-data.component.scss']
})
export class PrognosisDataComponent implements AfterViewInit, OnDestroy {
  @ViewChild('lineChart') lineChart?: MultilineChartComponent;
  mapControl?: MapControl;
  prognoses = mockPrognoses;
  selectedPrognosis = 'Trendfortschreibung';
  data: StackedData[] = mockdata;
  labels: string[] = ['65+', '19-64', '0-18']
  xSeparator = {
    leftLabel: $localize`Realdaten`,
    rightLabel: $localize`Prognose (Basisjahr: 2003)`,
    x: '2003',
    highlight: true
  }

  constructor(private mapService: MapService) { }

  ngAfterViewInit(): void {
    this.mapControl = this.mapService.get('base-prog-data-map');
    let first = mockdata[0].values;
    let relData = mockdata.map(d => { return {
      group: d.group,
      values: d.values.map((v, i) => Math.round(10000 * v / first[i]) / 100 )
    }})
    let max = Math.max(...relData.map(d => Math.max(...d.values))),
      min = Math.min(...relData.map(d => Math.min(...d.values)));
    this.lineChart!.min = Math.floor(min / 10) * 10;
    this.lineChart!.max = Math.ceil(max / 10) * 10;
    this.lineChart?.draw(relData);
  }

  ngOnDestroy(): void {
    this.mapControl?.destroy();
  }
}
