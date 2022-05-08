import { AfterViewInit, Component, OnDestroy, TemplateRef, ViewChild } from '@angular/core';
import { environment } from "../../../../environments/environment";
import { MapControl, MapService } from "../../../map/map.service";
import { RestCacheService } from "../../../rest-cache.service";
import { Area, AreaLevel, Layer, LayerGroup, Statistic, StatisticsData, Year } from "../../../rest-interfaces";
import { sortBy } from "../../../helpers/utils";
import * as d3 from "d3";
import { SettingsService } from "../../../settings.service";
import { BehaviorSubject } from "rxjs";
import { ConfirmDialogComponent } from "../../../dialogs/confirm-dialog/confirm-dialog.component";
import { MatDialog } from "@angular/material/dialog";
import { HttpClient } from "@angular/common/http";
import { RestAPI } from "../../../rest-api";
import { RemoveDialogComponent } from "../../../dialogs/remove-dialog/remove-dialog.component";

@Component({
  selector: 'app-statistics',
  templateUrl: './statistics.component.html',
  styleUrls: ['./statistics.component.scss']
})
export class StatisticsComponent implements AfterViewInit, OnDestroy {
  @ViewChild('dataTemplate') dataTemplate?: TemplateRef<any>;
  @ViewChild('pullServiceTemplate') pullServiceTemplate?: TemplateRef<any>;
  backend: string = environment.backend;
  mapControl?: MapControl;
  statistics?: Statistic[];
  statisticsData?: StatisticsData[];
  year?: number;
  areaLevel?: AreaLevel;
  theme: 'nature' | 'migration' = 'nature';
  legendGroup?: LayerGroup;
  statisticsLayer?: Layer;
  areas: Area[] = [];
  showBirths: boolean = true;
  showDeaths: boolean = true;
  showImmigration: boolean = true;
  showEmigration: boolean = true;
  isLoading$ = new BehaviorSubject<boolean>(false);
  dataColumns: string[] = ['Gebiet', 'AGS', 'Geburten', 'Sterbefälle', 'Zuzüge', 'Fortzüge'];
  dataRows: any[][] = [];
  pullErrors: any = {};

  constructor(private mapService: MapService, private restService: RestCacheService, private rest: RestAPI,
              private settings: SettingsService, private dialog: MatDialog, private http: HttpClient) { }

  ngAfterViewInit(): void {
    this.mapControl = this.mapService.get('base-statistics-map');
    this.legendGroup = this.mapControl.addGroup({
      name: 'Bevölkerungssalden',
      order: -1
    }, false)
    this.isLoading$.next(true);
    this.settings.baseDataSettings$.subscribe(baseSettings => {
      const baseLevel = baseSettings.popStatisticsAreaLevel;
      // ToDo: warn if areas are empty, disable pull
      this.restService.getAreaLevels({ active: true }).subscribe(areaLevels => {
        this.areaLevel = areaLevels.find(al => al.id === baseLevel);
        this.restService.getAreas(baseLevel,
          { targetProjection: this.mapControl!.map!.mapProjection }).subscribe(areas => {
          this.areas = areas;
          this.fetchData();
        })
      });
    });
  }

  fetchData(): void {
    this.restService.getStatistics({ reset: true }).subscribe(statistics => {
      this.statistics = sortBy(statistics, 'year');
      this.isLoading$.next(false);
      this.year = (this.statistics.length > 0)? this.statistics[0].year: undefined;
      this.onYearChange();
    });
  }

  onYearChange(): void {
    this.dataRows = [];
    if (!this.year) {
      this.statisticsData = undefined;
      this.updateMap();
      return;
    };
    this.isLoading$.next(true);
    this.restService.getStatisticsData({ year: this.year }).subscribe(data => {
      this.statisticsData = data;
      data.forEach(stat => {
        const area = this.areas.find(a => a.id === stat.area);
        if (!area) return;
        this.dataRows.push([area.properties.label, area.properties.attributes.ags || '',
          stat.births, stat.deaths, stat.immigration, stat.emigration])
      });
      this.isLoading$.next(false);
      this.updateMap();
    })
  }

  // ToDo: reusable statistics map view, atm mostly copy/paste from pop-statistics due to pressing time
  updateMap(): void {
    if (this.statisticsLayer) {
      this.mapControl?.removeLayer(this.statisticsLayer.id!);
      this.statisticsLayer = undefined;
    }
    if (!this.statisticsData ||
      (this.theme === 'nature' && !this.showBirths && !this.showDeaths) ||
      this.theme === 'migration' && !this.showImmigration && !this.showEmigration){
      return;
    }
    this.isLoading$.next(true);
    let descr = '';
    let max: number;
    let color: string;
    const diffDisplay = ((this.theme ==='nature' && this.showBirths && this.showDeaths) || (this.theme ==='migration' && this.showEmigration && this.showImmigration));
    const mvs = this.areaLevel?.maxValues!;
    if (this.theme === 'nature') {
      descr = diffDisplay? 'Natürlicher Saldo' : (this.showBirths) ? 'Geburten' : 'Sterbefälle';
      color = this.showBirths? '#1a9850': '#d73027';
      max = (diffDisplay)? Math.max(mvs.natureDiff!): this.showBirths? mvs.births!: mvs.deaths!;
    }
    else {
      descr = diffDisplay? 'Wanderungssaldo' : (this.showImmigration) ? 'Zuzüge' : 'Fortzüge';
      color = this.showImmigration? '#1a9850': '#d73027';
      max = (diffDisplay)? Math.max(mvs.migrationDiff!): this.showImmigration? mvs.immigration!: mvs.emigration!;
    }
    const radiusFunc = d3.scaleLinear().domain([0, max || 1000]).range([5, 50]);
    const colorFunc = function(value: number) {
      return (value > 0)? '#1a9850': (value < 0)? '#d73027': 'grey';
    };

    this.statisticsLayer = this.mapControl?.addLayer({
        order: 0,
        type: 'vector',
        group: this.legendGroup?.id,
        name: descr,
        description: 'ToDo',
        opacity: 1,
        symbol: {
          strokeColor: 'white',
          fillColor: color,
          symbol: 'circle'
        },
        labelField: 'value',
        showLabel: true
      },
      {
        visible: true,
        tooltipField: 'description',
        mouseOver: {
          strokeColor: 'yellow',
          fillColor: 'rgba(255, 255, 0, 0.7)',
        },
        selectable: false,
        select: {
          strokeColor: 'rgb(180, 180, 0)',
          fillColor: 'rgba(255, 255, 0, 0.9)'
        },
        colorFunc: diffDisplay? colorFunc: undefined,
        radiusFunc: radiusFunc
      });
    this.areas.forEach(area => {
      const data = this.statisticsData!.find(d => d.area == area.id);
      let value = 0;
      if (data) {
        if (this.theme === 'nature') {
          value = (this.showBirths && this.showDeaths) ? data.births - data.deaths : (this.showBirths) ? data.births : data.deaths;
        } else {
          value = (this.showImmigration && this.showEmigration) ? data.immigration - data.emigration : (this.showImmigration) ? data.immigration : data.emigration;
        }
      }
      area.properties.value = value;
      area.properties.description = `<b>${area.properties.label}</b><br>${descr}: ${area.properties.value}`
    })
    this.mapControl?.addFeatures(this.statisticsLayer!.id!, this.areas,
      { properties: 'properties', geometry: 'centroid', zIndex: 'value' });
    this.isLoading$.next(false);
  }

  showDataTable(): void {
    if (!this.year) return;
    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      panelClass: 'absolute',
      width: '400',
      disableClose: false,
      autoFocus: false,
      data: {
        title: `Datentabelle Statistiken im Jahr "${this.year}"`,
        template: this.dataTemplate,
        hideConfirmButton: true,
        cancelButtonText: 'OK'
      }
    });
  }

  pullService(): void {
    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      width: '400px',
      data: {
        title: 'Einwohnerdaten abrufen',
        confirmButtonText: 'Daten abrufen',
        template: this.pullServiceTemplate,
        closeOnConfirm: false
      }
    });
    dialogRef.componentInstance.confirmed.subscribe(() => {
      const url = `${this.rest.URLS.statistics}pull_regionalstatistik/`;
      dialogRef.componentInstance.isLoading$.next(true);
      this.http.post(url, {}).subscribe(() => {
        this.restService.reset();
        this.fetchData();
        dialogRef.close();
      }, error => {
        this.pullErrors = error.error;
        dialogRef.componentInstance.isLoading$.next(false);
      })
    })
  }

  onRemoveStatistics(): void {
    if (!this.year) return;
    const statistics = this.statistics?.find(s => s.year === this.year);
    if (!statistics) return;
    const dialogRef = this.dialog.open(RemoveDialogComponent, {
      width: '350px',
      data: {
        title: 'Entfernung von Statistikdaten',
        message: 'Sollen die Statistikdaten dieses Jahres wirklich entfernt werden?',
        confirmButtonText: 'Daten entfernen',
        value: this.year
      }
    });
    dialogRef.afterClosed().subscribe((confirmed: boolean) => {
      if (confirmed) {
        this.http.delete(`${this.rest.URLS.statistics}${statistics.id}/`
        ).subscribe(() => {
          const idx = this.statistics!.indexOf(statistics);
          if (idx > -1) this.statistics!.splice(idx, 1);
          this.year = undefined;
          this.onYearChange();
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
