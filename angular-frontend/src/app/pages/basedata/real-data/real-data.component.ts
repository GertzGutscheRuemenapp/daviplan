import { AfterViewInit, Component, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { MapControl, MapService } from "../../../map/map.service";
import { environment } from "../../../../environments/environment";
import { PopulationService } from "../../population/population.service";
import { AreaLevel, Infrastructure, Population, Year } from "../../../rest-interfaces";
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
  popLevel?: AreaLevel;
  defaultPopLevel?: AreaLevel;
  realYears: number[] = [];
  // dataYears: number[] = [];
  yearSelection = new SelectionModel<number>(true);
  populations: Population[] = [];
  maxYear = new Date().getFullYear() - 1;

  constructor(private mapService: MapService, private popService: PopulationService, private dialog: MatDialog,
              private settings: SettingsService, private rest: RestAPI, private http: HttpClient) { }

  ngAfterViewInit(): void {
    this.mapControl = this.mapService.get('base-real-data-map');
    this.popService.getAreaLevels({reset: true}).subscribe(areaLevels => {
      this.defaultPopLevel = areaLevels.find(al => al.isDefaultPopLevel);
      this.popLevel = areaLevels.find(al => al.isPopLevel);
    })
    this.http.get<Year[]>(this.rest.URLS.years).subscribe(years => {
      years.forEach(year => {
        if (year.year > this.maxYear) return;
        if (year.isReal) {
          this.realYears.push(year.year);
        }
        this.years.push(year);
      })
      this.popService.fetchPopulations().subscribe(populations => {
 /*       this.populations.forEach(population => {
          const year = this.years.find(y => y.id == population.year);
          if (year) this.dataYears.push(year.year);
        });*/
        this.setupYearCard();
      });
    });
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
        this.realYears.sort();
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
      const population = this.populations.find(p => p.year === year.id);
      if (!population) return;
      if (confirmed) {
        this.http.delete(`${this.rest.URLS.populations}${population.id}/`
        ).subscribe(res => {
          const idx = this.populations.indexOf(population);
          if (idx > -1) this.populations.splice(idx, 1);
          year.hasRealData = false;
        },(error) => {
          console.log('there was an error sending the query', error);
        });
      }
    });
  }

  ngOnDestroy(): void {
    this.mapControl?.destroy();
  }
}
