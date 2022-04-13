import { AfterViewInit, Component, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { MapControl, MapService } from "../../../map/map.service";
import { environment } from "../../../../environments/environment";
import { PopulationService } from "../../population/population.service";
import { Infrastructure, Population, Year } from "../../../rest-interfaces";
import { sortBy } from "../../../helpers/utils";
import { SettingsService } from "../../../settings.service";
import { SelectionModel } from "@angular/cdk/collections";
import { RestAPI } from "../../../rest-api";
import { HttpClient } from "@angular/common/http";
import { RemoveDialogComponent } from "../../../dialogs/remove-dialog/remove-dialog.component";
import { MatDialog } from "@angular/material/dialog";
import { InputCardComponent } from "../../../dash/input-card.component";

@Component({
  selector: 'app-real-data',
  templateUrl: './real-data.component.html',
  styleUrls: ['./real-data.component.scss']
})
export class RealDataComponent implements AfterViewInit, OnDestroy {
  @ViewChild('yearCard') yearCard?: InputCardComponent;
  backend: string = environment.backend;
  mapControl?: MapControl;
  years: Year[] = [];
  realYears: number[] = [];
  yearSelection = new SelectionModel<number>(true);
  populations: Population[] = [];
  maxYear = new Date().getFullYear() - 1;

  constructor(private mapService: MapService, private popService: PopulationService, private dialog: MatDialog,
              private settings: SettingsService, private rest: RestAPI, private http: HttpClient) { }

  ngAfterViewInit(): void {
    this.mapControl = this.mapService.get('base-real-data-map');
    this.popService.fetchPopulations().subscribe(populations => {
      this.populations = sortBy(populations,'year');
      // this.populations.forEach(pop => this.yearSelection.select(pop.year))
    });
    this.http.get<Year[]>(this.rest.URLS.years).subscribe(years => {
      years.forEach(year => {
        if (year.year > this.maxYear) return;
        if (year.isReal) {
          this.realYears.push(year.year);
        }
        this.years.push(year);
        this.setupYearCard();
      })
    });
    // this.settings.projectSettings$.subscribe(settings => {
    //   this.availableYears = Array.from({ length: settings.endYear - settings.startYear + 1 }, (_, i) => i + settings.startYear)
    // })
  }

  setupYearCard(): void {
    this.yearCard?.dialogOpened.subscribe(ok => {
      this.yearSelection.clear();
      this.realYears.forEach(year => this.yearSelection.select(year));
    })
    this.yearCard?.dialogConfirmed.subscribe((ok)=>{
      this.yearCard?.setLoading(true);
      const realYears = this.yearSelection.selected;
      this.http.post<Year[]>(`${this.rest.URLS.years}set_real_years/`, { years: realYears }
      ).subscribe(years => {
        this.realYears = [];
        years.forEach(ry => {
          this.realYears.push(ry.year);
          const year = this.years.find(y => y.id === ry.id);
          if (year)
            Object.assign(year, ry);
        })
        this.yearCard?.closeDialog(true);
      });
    })
  }

  deleteData(year: Year): void {
    if (!year.hasRealData) return;
    const dialogRef = this.dialog.open(RemoveDialogComponent, {
      width: '350px',
      data: {
        title: 'Entfernung von Realdaten',
        message: 'Sollen die Realdaten dieses Jahres wirklich entfernt werden?',
        confirmButtonText: 'Realdaten entfernen',
        value: year.year
      }
    });
    dialogRef.afterClosed().subscribe((confirmed: boolean) => {
      // ToDo: route for deletion of real data (population?)
/*      if (confirmed) {
        this.http.delete(`${this.rest.URLS.years}${year.id}/`
        ).subscribe(res => {
          year.hasRealData = false;
        },(error) => {
          console.log('there was an error sending the query', error);
        });
      }*/
    });
  }

  ngOnDestroy(): void {
    this.mapControl?.destroy();
  }
}
