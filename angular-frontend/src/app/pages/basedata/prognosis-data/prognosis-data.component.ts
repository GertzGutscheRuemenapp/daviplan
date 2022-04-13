import { AfterViewInit, Component, OnDestroy, ViewChild } from '@angular/core';
import { MapControl, MapService } from "../../../map/map.service";
import { StackedData } from "../../../diagrams/stacked-barchart/stacked-barchart.component";
import { MultilineChartComponent } from "../../../diagrams/multiline-chart/multiline-chart.component";
import { Year } from "../../../rest-interfaces";
import { InputCardComponent } from "../../../dash/input-card.component";
import { SelectionModel } from "@angular/cdk/collections";
import { SettingsService } from "../../../settings.service";
import { RestAPI } from "../../../rest-api";
import { HttpClient } from "@angular/common/http";
import { RemoveDialogComponent } from "../../../dialogs/remove-dialog/remove-dialog.component";
import { MatDialog } from "@angular/material/dialog";

export const mockPrognoses = ['Trendfortschreibung', 'mehr Zuwanderung', 'mehr Abwanderung'];

const mockdata: StackedData[] = [
  { group: '2000', values: [200, 300, 280] },
  { group: '2001', values: [190, 310, 290] },
  { group: '2002', values: [192, 335, 293] },
  { group: '2003', values: [195, 340, 295] },
  { group: '2004', values: [189, 342, 293] },
  { group: '2005', values: [182, 345, 300] },
  { group: '2006', values: [176, 345, 298] },
  { group: '2007', values: [195, 330, 290] },
  { group: '2008', values: [195, 340, 295] },
  { group: '2009', values: [192, 335, 293] },
  { group: '2010', values: [195, 340, 295] },
  { group: '2012', values: [189, 342, 293] },
  { group: '2013', values: [200, 300, 280] },
  { group: '2014', values: [195, 340, 295] },
]

@Component({
  selector: 'app-prognosis-data',
  templateUrl: './prognosis-data.component.html',
  styleUrls: ['./prognosis-data.component.scss']
})
export class PrognosisDataComponent implements AfterViewInit, OnDestroy {
  @ViewChild('yearCard') yearCard?: InputCardComponent;
  @ViewChild('lineChart') lineChart?: MultilineChartComponent;
  mapControl?: MapControl;
  prognoses = mockPrognoses;
  selectedPrognosis = 'Trendfortschreibung';
  years: Year[] = [];
  yearSelection = new SelectionModel<number>(true);
  prognosisYears: number[] = [];
  data: StackedData[] = mockdata;
  labels: string[] = ['65+', '19-64', '0-18']
  xSeparator = {
    leftLabel: $localize`Realdaten`,
    rightLabel: $localize`Prognose (Basisjahr: 2003)`,
    x: '2003',
    highlight: false
  }

  constructor(private mapService: MapService,private settings: SettingsService, private dialog: MatDialog,
              private rest: RestAPI, private http: HttpClient) { }

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
    this.http.get<Year[]>(this.rest.URLS.years).subscribe(years => {
      years.forEach(year => {
        if (year.isPrognosis) {
          this.prognosisYears.push(year.year);
        }
        this.years.push(year);
      })
      this.setupYearCard();
    });
  }

  setupYearCard(): void {
    this.yearCard?.dialogOpened.subscribe(ok => {
      this.yearSelection.clear();
      this.prognosisYears.forEach(year => this.yearSelection.select(year));
    })
    this.yearCard?.dialogConfirmed.subscribe((ok)=>{
      this.yearCard?.setLoading(true);
      const progYears = this.yearSelection.selected;
      this.http.post<Year[]>(`${this.rest.URLS.years}set_prognosis_years/`, { years: progYears }
      ).subscribe(years => {
        this.prognosisYears = [];
        years.forEach(ry => {
          this.prognosisYears.push(ry.year);
          const year = this.years.find(y => y.id === ry.id);
          if (year)
            Object.assign(year, ry);
        })
        this.prognosisYears.sort();
        this.yearCard?.closeDialog(true);
      });
    })
  }

  deleteData(year: Year): void {
    if (!year.hasPrognosisData) return;
    const dialogRef = this.dialog.open(RemoveDialogComponent, {
      width: '350px',
      data: {
        title: 'Entfernung von Prognosedaten',
        message: 'Sollen die Prognosedaten dieses Jahres wirklich entfernt werden?',
        confirmButtonText: 'Prognosedaten entfernen',
        value: year.year
      }
    });
    dialogRef.afterClosed().subscribe((confirmed: boolean) => {
    });
  }

  ngOnDestroy(): void {
    this.mapControl?.destroy();
  }
}
