import { AfterViewInit, Component, OnDestroy, TemplateRef, ViewChild } from '@angular/core';
import { environment } from "../../../../environments/environment";
import { MapControl, MapService } from "../../../map/map.service";
import { RestCacheService } from "../../../rest-cache.service";
import {
  Area,
  AreaLevel, BasedataSettings,
  LogEntry,
  Statistic,
  StatisticsData,
} from "../../../rest-interfaces";
import { showAPIError, sortBy } from "../../../helpers/utils";
import { SettingsService, SiteSettings } from "../../../settings.service";
import { BehaviorSubject, Subscription } from "rxjs";
import { ConfirmDialogComponent } from "../../../dialogs/confirm-dialog/confirm-dialog.component";
import { MatDialog } from "@angular/material/dialog";
import { HttpClient } from "@angular/common/http";
import { RestAPI } from "../../../rest-api";
import { RemoveDialogComponent } from "../../../dialogs/remove-dialog/remove-dialog.component";
import { MapLayerGroup, VectorLayer } from "../../../map/layers";

@Component({
  selector: 'app-statistics',
  templateUrl: './statistics.component.html',
  styleUrls: ['./statistics.component.scss']
})
export class StatisticsComponent implements AfterViewInit, OnDestroy {
  @ViewChild('dataTemplate') dataTemplate?: TemplateRef<any>;
  backend: string = environment.backend;
  mapControl?: MapControl;
  statistics?: Statistic[];
  statisticsData?: StatisticsData[];
  year?: number;
  areaLevel?: AreaLevel;
  theme: 'nature' | 'migration' = 'nature';
  layerGroup?: MapLayerGroup;
  statisticsLayer?: VectorLayer;
  areas: Area[] = [];
  showBirths: boolean = true;
  showDeaths: boolean = true;
  showImmigration: boolean = true;
  showEmigration: boolean = true;
  isLoading$ = new BehaviorSubject<boolean>(false);
  dataColumns: string[] = ['Gebiet', 'AGS', 'Geburten', 'Sterbefälle', 'Zuzüge', 'Fortzüge'];
  dataRows: any[][] = [];
  isProcessing = false;
  subscriptions: Subscription[] = [];
  baseSettings?: BasedataSettings;

  constructor(private mapService: MapService, private restService: RestCacheService, private rest: RestAPI,
              public settings: SettingsService, private dialog: MatDialog, private http: HttpClient) {
    // make sure data requested here is up-to-date
    this.restService.reset();
  }

  ngAfterViewInit(): void {
    this.mapControl = this.mapService.get('base-statistics-map');
    this.layerGroup = new MapLayerGroup('Bevölkerungssalden', { order: -1 });
    this.mapControl.addGroup(this.layerGroup);
    this.isLoading$.next(true);
    this.subscriptions.push(this.settings.baseDataSettings$.subscribe(baseSettings => {
      this.isProcessing = baseSettings.processes?.population || false;
      this.baseSettings = baseSettings;
      this.fetchData();
    }));
    this.settings.fetchBaseDataSettings();
  }

  fetchData(): void {
    const baseLevel = this.baseSettings!.popStatisticsAreaLevel;
    this.restService.getAreaLevels({ active: true }).subscribe(areaLevels => {
      this.areaLevel = areaLevels.find(al => al.id === baseLevel);
      this.restService.getAreas(baseLevel,
        { targetProjection: this.mapControl!.map!.mapProjection }).subscribe(areas => {
        this.areas = areas;
        this.restService.getStatistics({ reset: true }).subscribe(statistics => {
          this.statistics = sortBy(statistics, 'year');
          this.isLoading$.next(false);
          this.year = (this.statistics.length > 0)? this.statistics[0].year: undefined;
          this.onYearChange();
        });
      })
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
      this.layerGroup?.removeLayer(this.statisticsLayer);
      this.statisticsLayer = undefined;
    }
    if (!this.statisticsData ||
      (this.theme === 'nature' && !this.showBirths && !this.showDeaths) ||
      this.theme === 'migration' && !this.showImmigration && !this.showEmigration){
      return;
    }
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
    const colorFunc = function(value: number) {
      return (value > 0)? '#1a9850': (value < 0)? '#d73027': 'grey';
    };
    const unit = (this.theme === 'nature' && this.showBirths && !this.showDeaths)? 'Geburten':
      (this.theme === 'nature' && this.showDeaths && !this.showBirths)? 'Sterbefälle':
        (this.theme === 'migration' && this.showImmigration && !this.showEmigration)? 'Zuzüge':
          (this.theme === 'migration' && this.showEmigration && !this.showImmigration)? 'Fortzüge':
            'Ew.'

    this.statisticsLayer = new VectorLayer(descr, {
      order: 0,
      opacity: 1,
      style: {
        strokeColor: 'white',
        fillColor: color,
        symbol: 'circle'
      },
      labelField: 'value',
      showLabel: true,
      tooltipField: 'description',
      mouseOver: {
        enabled: true,
        style: {
          strokeColor: 'yellow',
          fillColor: 'rgba(255, 255, 0, 0.7)'
        }
      },
      valueStyles: {
        field: 'value',
        fillColor: diffDisplay? { colorFunc: colorFunc }: undefined,
        radius: {
          range: [5, 50],
          scale: 'sqrt'
        },
        min: 0,
        max: max || 1000
      },
      unit: unit,
      forceSign: diffDisplay,
      labelOffset: { y: 15 }
    });
    this.layerGroup?.addLayer(this.statisticsLayer);
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
      let description = `<b>${area.properties.label}</b><br>`;
      description += (diffDisplay && !value)? 'keine Änderung ': `${diffDisplay && value > 0? '+': ''}${area.properties.value.toLocaleString()} ${unit} im Jahr ${this.year}`;
      area.properties.description = description;
    })
    this.statisticsLayer.addFeatures(this.areas,{
      properties: 'properties',
      geometry: 'centroid',
      zIndex: 'value'
    });
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
      panelClass: 'absolute',
      data: {
        title: 'Einwohnerdaten abrufen',
        confirmButtonText: 'Daten abrufen',
        message: '<p> Sollen die Daten aus der Regionalstatistik jetzt abgerufen und in die Datenbank eingespielt werden? </p>' +
                 '<p> Achtung: bereits eingespielte Statistiken werden überschrieben!</p>',
        closeOnConfirm: true
      }
    });
    dialogRef.componentInstance.confirmed.subscribe(() => {
      const url = `${this.rest.URLS.statistics}pull_regionalstatistik/`;
      this.http.post(url, {}).subscribe(() => {
        this.isProcessing = true;
        }, error => {
        showAPIError(error, this.dialog);
      })
    })
  }

  onMessage(log: LogEntry): void {
    if (log?.status?.finished) {
      this.isProcessing = false;
      this.restService.reset();
      this.fetchData();
    }
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
          showAPIError(error, this.dialog);
        });
      }
    });
  }

  ngOnDestroy(): void {
    this.mapControl?.destroy();
    this.subscriptions.forEach(subscription => subscription.unsubscribe());
  }
}
