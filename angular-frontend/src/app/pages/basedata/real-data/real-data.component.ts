import { AfterViewInit, Component, OnDestroy, TemplateRef, ViewChild } from '@angular/core';
import { MapControl, MapService } from "../../../map/map.service";
import { environment } from "../../../../environments/environment";
import { PopulationService } from "../../population/population.service";
import * as fileSaver from 'file-saver';
import {
  AgeGroup,
  Area,
  AreaLevel, Gender,
  ExtLayer,
  ExtLayerGroup,
  PopEntry,
  Population,
  Year, LogEntry
} from "../../../rest-interfaces";
import { SettingsService } from "../../../settings.service";
import { SelectionModel } from "@angular/cdk/collections";
import { RestAPI } from "../../../rest-api";
import { HttpClient } from "@angular/common/http";
import { RemoveDialogComponent } from "../../../dialogs/remove-dialog/remove-dialog.component";
import { MatDialog } from "@angular/material/dialog";
import { InputCardComponent } from "../../../dash/input-card.component";
import * as d3 from "d3";
import { AgeTreeComponent, AgeTreeData } from "../../../diagrams/age-tree/age-tree.component";
import { sortBy } from "../../../helpers/utils";
import { ConfirmDialogComponent } from "../../../dialogs/confirm-dialog/confirm-dialog.component";
import { Router } from "@angular/router";
import { BehaviorSubject, Subscription } from "rxjs";
import { SimpleDialogComponent } from "../../../dialogs/simple-dialog/simple-dialog.component";
import { MapLayer, MapLayerGroup, VectorLayer } from "../../../map/layers";

@Component({
  selector: 'app-real-data',
  templateUrl: './real-data.component.html',
  styleUrls: ['./real-data.component.scss']
})
export class RealDataComponent implements AfterViewInit, OnDestroy {
  @ViewChild('yearCard') yearCard?: InputCardComponent;
  @ViewChild('ageTree') ageTree?: AgeTreeComponent;
  @ViewChild('pullServiceTemplate') pullServiceTemplate?: TemplateRef<any>;
  @ViewChild('dataTemplate') dataTemplate?: TemplateRef<any>;
  @ViewChild('fileUploadTemplate') fileUploadTemplate?: TemplateRef<any>;
  isLoading$ = new BehaviorSubject<boolean>(false);
  backend: string = environment.backend;
  mapControl?: MapControl;
  ageGroupsRegStatValid = false;
  years: Year[] = [];
  popLevel?: AreaLevel;
  popLevelMissing = false;
  defaultPopLevel?: AreaLevel;
  areas: Area[] = [];
  realYears: number[] = [];
  previewYear?: Year;
  previewArea?: Area;
  previewLayer?: VectorLayer;
  layerGroup?: MapLayerGroup;
  popEntries: Record<number, PopEntry[]> = {};
  populations: Population[] = [];
  genders: Gender[] = [];
  ageGroups: AgeGroup[] = [];
  yearSelection = new SelectionModel<number>(true);
  maxYear = new Date().getFullYear() - 1;
  Object = Object;
  dataTableColumns: string[] = [];
  dataTableRows: any[][] = [];
  dataTableYear?: Year;
  file?: File;
  isProcessing = false;
  subscriptions: Subscription[] = [];
  uploadErrors: any = {};

  constructor(private mapService: MapService, public popService: PopulationService,
              private dialog: MatDialog, private settings: SettingsService,
              private rest: RestAPI, private http: HttpClient, private router: Router) {}

  ngAfterViewInit(): void {
    this.mapControl = this.mapService.get('base-real-data-map');
    this.layerGroup = new MapLayerGroup('Bevölkerungsentwicklung', { order: -1 })
    this.mapControl.addGroup(this.layerGroup);
    this.popService.getAreaLevels({ reset: true }).subscribe(areaLevels => {
      this.defaultPopLevel = areaLevels.find(al => al.isDefaultPopLevel);
      this.popLevel = areaLevels.find(al => al.isPopLevel);
      if (this.popLevel) {
        this.popService.getAreas(this.popLevel.id, { reset: true }).subscribe(areas => this.areas = areas);
      }
    })
    this.subscriptions.push(this.settings.baseDataSettings$.subscribe(baseSettings => {
      this.isProcessing = baseSettings.processes?.population || false;
    }));
    this.settings.fetchBaseDataSettings();
    this.fetchData();
    this.setupYearCard();
  }

  fetchData(): void {
    this.previewYear = undefined;
    this.previewArea = undefined;
    this.ageTree?.clear();
    this.updatePreview();
    this.dataTableColumns = ['Gebiet']
    this.popService.getGenders().subscribe(genders => {
      this.genders = genders;
      this.popService.getAgeGroups().subscribe(ageGroups => {
        this.checkAgeGroups(ageGroups);
        this.genders.forEach(gender => {
          this.dataTableColumns = this.dataTableColumns.concat(ageGroups.map(ag => `${ag.label} (${gender.name})`));
        })
        this.ageGroups = sortBy(ageGroups, 'fromAge');
        this.http.get<Year[]>(this.rest.URLS.years).subscribe(years => {
          this.years = [];
          this.realYears = [];
          years.forEach(year => {
            if (year.year > this.maxYear) return;
            if (year.isReal) {
              this.realYears.push(year.year);
            }
            this.years.push(year);
          })
          this.popService.fetchPopulations().subscribe(populations => {
            this.populations = populations;
          });
        });
      })
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
        this.years.forEach(y => y.isReal = false);
        this.realYears = [];
        years.forEach(ry => {
          if (ry.isReal) this.realYears.push(ry.year);
          const year = this.years.find(y => y.id === ry.id);
          if (year)
            Object.assign(year, ry);
        })
        this.realYears.sort();
        this.previewYear = undefined;
        this.dataTableYear = undefined;
        this.ageTree?.clear();
        this.updatePreview();
        this.yearCard?.closeDialog(true);
      });
    })
  }

  checkAgeGroups(ageGroups: AgeGroup[]){
    this.http.post(`${this.rest.URLS.ageGroups}check/`, ageGroups).subscribe(res => {
      this.ageGroupsRegStatValid = true;
    }, error => {
      this.ageGroupsRegStatValid = false;
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
        this.yearCard?.setLoading(true);
        this.http.delete(`${this.rest.URLS.populations}${population.id}/?force=true/`
        ).subscribe(res => {
          const idx = this.populations.indexOf(population);
          if (idx > -1) this.populations.splice(idx, 1);
          year.hasRealData = false;
          if(year === this.previewYear) {
            this.previewYear = undefined;
            this.ageTree?.clear();
            this.dataTableRows = [];
            this.updatePreview();
          }
          this.yearCard?.setLoading(false);
        },(error) => {
          console.log('there was an error sending the query', error);
          this.yearCard?.setLoading(false);
        });
      }
    });
  }

  updatePreview(): void {
    if (this.previewLayer) {
      this.layerGroup?.removeLayer(this.previewLayer);
      this.previewLayer = undefined;
    }
    if (!this.previewYear) return;
    const population = this.populations.find(p => p.year === this.previewYear!.id);
    if (!population) return;
    this.popService.getPopEntries(population.id).subscribe(popEntries => {
      this.popEntries = {};
      popEntries.forEach(pe => {
        if (!this.popEntries[pe.area]) this.popEntries[pe.area] = [];
        this.popEntries[pe.area].push(pe);
      })
      let max = 1000;
      this.dataTableRows = [];
      this.areas.forEach(area => {
        const entries = this.popEntries[area.id];
        if (!entries) return;
        // map data
        const value = entries.reduce((p: number, e: PopEntry) => p + e.value, 0);
        area.properties.value = value;
        area.properties.description = `<b>${area.properties.label}</b><br>Bevölkerung: ${area.properties.value}`
        max = Math.max(max, value);
      })
      this.previewLayer = new VectorLayer(this.popLevel!.name, {
        order: 0,
        description: this.popLevel!.name,
        opacity: 1,
        style: {
          strokeColor: 'white',
          fillColor: 'rgba(165, 15, 21, 0.9)',
          symbol: 'circle'
        },
        labelField: 'value',
        showLabel: true,
        tooltipField: 'description',
        labelOffset: { y: 10 },
        mouseOver: {
          enabled: true,
          style: {
            strokeColor: 'yellow',
            fillColor: 'rgba(255, 255, 0, 0.7)'
          }
        },
        select: {
          enabled: true,
          style: {
            strokeColor: 'rgb(180, 180, 0)',
            fillColor: 'rgba(255, 255, 0, 0.9)'
          }
        },
        valueStyles: {
          field: 'value',
          // fillColor: diffDisplay? colorFunc: undefined,
          radius: {
            range: [5, 50],
            scale: 'linear'
          },
          min: 0,
          max: max
        }
      });
      this.layerGroup?.addLayer(this.previewLayer);
      this.previewLayer?.addFeatures(this.areas, {
        properties: 'properties',
        geometry: 'centroid',
        zIndex: 'value'
      });
      this.updateAgeTree();
      this.previewLayer!.featuresSelected.subscribe(features => {
        this.previewArea = this.areas.find(area => area.id === features[0].get('id'));
        this.updateAgeTree();
      })
      this.previewLayer!.featuresDeselected.subscribe(features => {
        if (this.previewArea?.id === features[0].get('id')) {
          this.previewArea = undefined;
          this.updateAgeTree();
        }
      })
    })
  }

  onAreaChange(): void {
    if (!this.previewLayer) return;
    this.previewLayer?.selectFeatures([this.previewArea!.id], { silent: true, clear: true });
    this.updateAgeTree();
  }

  downloadTemplate(): void {
    if (!this.popLevel) return;
    const url = `${this.rest.URLS.popEntries}create_template/`;
    const dialogRef = SimpleDialogComponent.show('Bereite Template vor. Bitte warten', this.dialog, { showAnimatedDots: true });
    this.http.post(url, { area_level: this.popLevel.id, years: this.realYears }, { responseType: 'blob' }).subscribe((res:any) => {
      const blob: any = new Blob([res],{ type:'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
      dialogRef.close();
      fileSaver.saveAs(blob, 'realdaten-template.xlsx');
    },(error) => {
      dialogRef.close();
    });
  }

  updateAgeTree(): void {
    this.ageTree?.clear();
    if (!this.previewArea || !this.previewYear) return;
    const areaData = this.popEntries[this.previewArea.id];
    const maleId = this.genders.find(g => g.name === 'männlich')?.id || 1;
    const femaleId = this.genders.find(g => g.name === 'weiblich')?.id || 2;
    const ageTreeData: AgeTreeData[] = [];
    this.ageGroups.forEach(ageGroup => {
      const ad = areaData.filter(d => d.ageGroup === ageGroup.id);
      ageTreeData.push({
        male: ad.find(d => d.gender === maleId)?.value || 0,
        fromAge: ageGroup.fromAge,
        toAge: ageGroup.toAge,
        female: ad.find(d => d.gender === femaleId)?.value || 0,
        label: ageGroup.label || ''
      })
    })
    this.ageTree!.subtitle = `${this.previewArea?.properties.label!} ${this.previewYear?.year}`;
    this.ageTree!.draw(ageTreeData);
  }

  pullService(): void {
    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      width: '400px',
      panelClass: 'absolute',
      data: {
        title: 'Einwohnerdaten abrufen',
        confirmButtonText: 'Daten abrufen',
        template: this.pullServiceTemplate,
        closeOnConfirm: true
      }
    });
    dialogRef.componentInstance.confirmed.subscribe(() => {
      const url = `${this.rest.URLS.populations}pull_regionalstatistik/`;
      this.http.post(url, {}).subscribe(() => {
        this.isProcessing = true;
      }, error => {
      })
    })
  }

  showDataTable(): void {
    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      panelClass: 'absolute',
      width: '400',
      disableClose: false,
      autoFocus: false,
      data: {
        title: `Datentabelle Realdaten`,
        template: this.dataTemplate,
        hideConfirmButton: true,
        cancelButtonText: 'OK'
      }
    });
    dialogRef.afterOpened().subscribe(()=> this.updateTableData())
  }

  updateTableData(): void {
    this.dataTableRows = [];
    if (!this.dataTableYear) return;
    const population = this.populations.find(p => p.year === this.dataTableYear!.id);
    if (!population) return;
    let rows: any[][] = [];
    this.isLoading$.next(true);
    this.popService.getPopEntries(population.id).subscribe(popEntries => {
      this.areas.forEach(area => {
        const entries = popEntries.filter(e => e.area === area.id);
        const row: any[] = [area.properties.label]
        if (!entries) return;
        // table data
        this.genders.forEach(gender => {
          const gEntries = entries.filter(e => e.gender === gender.id);
          this.ageGroups.forEach(ageGroup => {
            const entry = gEntries.find(e => e.ageGroup === ageGroup.id);
            row.push(entry?.value || 0);
          })
        })
        rows.push(row);
      })
      this.dataTableRows = rows;
      this.isLoading$.next(false);
    })
  }

  uploadTemplate(): void {
    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      width: '450px',
      panelClass: 'absolute',
      data: {
        title: `Template hochladen`,
        confirmButtonText: 'Datei hochladen',
        closeOnConfirm: false,
        template: this.fileUploadTemplate
      }
    });
    dialogRef.componentInstance.confirmed.subscribe(() => {
      if (!this.file)
        return;
      dialogRef.componentInstance.isLoading$.next(true);
      const formData = new FormData();
      formData.append('excel_file', this.file);
      const url = `${this.rest.URLS.popEntries}upload_template/`;
      this.http.post(url, formData).subscribe(res => {
        this.isProcessing = true;
        dialogRef.close();
      }, error => {
        this.uploadErrors = error.error;
        dialogRef.componentInstance.isLoading$.next(false);
      });
    });
    dialogRef.afterClosed().subscribe(ok => {
      this.uploadErrors = {};
    })
  }

  onMessage(log: LogEntry): void {
    if (log?.status?.finished) {
      this.isProcessing = false;
      this.popService.reset();
      this.fetchData();
    }
  }

  setFiles(event: Event){
    const element = event.currentTarget as HTMLInputElement;
    const files: FileList | null = element.files;
    this.file =  (files && files.length > 0)? files[0]: undefined;
  }

  ngOnDestroy(): void {
    this.mapControl?.destroy();
    this.subscriptions.forEach(subscription => subscription.unsubscribe());
  }
}
