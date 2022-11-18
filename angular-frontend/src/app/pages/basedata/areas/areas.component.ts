import { AfterViewInit, Component, OnDestroy, TemplateRef, ViewChild } from '@angular/core';
import { MapControl, MapService } from "../../../map/map.service";
import { Area, AreaLevel, LogEntry } from "../../../rest-interfaces";
import { BehaviorSubject, forkJoin, Observable, Subscription } from "rxjs";
import { arrayMove, sortBy } from "../../../helpers/utils";
import { HttpClient } from "@angular/common/http";
import { MatDialog } from "@angular/material/dialog";
import { RestAPI } from "../../../rest-api";
import { InputCardComponent } from "../../../dash/input-card.component";
import { FormBuilder, FormControl, FormGroup } from "@angular/forms";
import { MatCheckbox } from "@angular/material/checkbox";
import { environment } from "../../../../environments/environment";
import { ConfirmDialogComponent } from "../../../dialogs/confirm-dialog/confirm-dialog.component";
import { RemoveDialogComponent } from "../../../dialogs/remove-dialog/remove-dialog.component";
import { RestCacheService } from "../../../rest-cache.service";
import { tap } from "rxjs/operators";
import { showAPIError } from "../../../helpers/utils";
import { MapLayerGroup, VectorLayer } from "../../../map/layers";
import { SettingsService } from "../../../settings.service";

@Component({
  selector: 'app-areas',
  templateUrl: './areas.component.html',
  styleUrls: ['../../../map/legend/legend.component.scss','./areas.component.scss']
})
export class AreasComponent implements AfterViewInit, OnDestroy {
  @ViewChild('editArealevelCard') editArealevelCard!: InputCardComponent;
  @ViewChild('enableLayerCheck') enableLayerCheck?: MatCheckbox;
  @ViewChild('createAreaLevel') createLevelTemplate?: TemplateRef<any>;
  @ViewChild('dataTemplate') dataTemplate?: TemplateRef<any>;
  @ViewChild('pullWfsTemplate') pullWfsTemplate?: TemplateRef<any>;
  @ViewChild('fileUploadTemplate') fileUploadTemplate?: TemplateRef<any>;
  @ViewChild('fileInput') fileInput?: HTMLInputElement;
  mapControl?: MapControl;
  activeLevel?: AreaLevel;
  presetLevels: AreaLevel[] = [];
  customAreaLevels: AreaLevel[] = [];
  colorSelection: string = 'black';
  layerGroup?: MapLayerGroup;
  editLevelForm: FormGroup;
  areaLayer?: VectorLayer;
  areas: Area[] = [];
  isLoading$ = new BehaviorSubject<boolean>(false);
  orderIsChanging$ = new BehaviorSubject<boolean>(false);
  dataColumns: string[] = [];
  dataRows: any[][] = [];
  file?: File;
  isProcessing = false;
  subscriptions: Subscription[] = [];
  projectArea?: string;

  constructor(private mapService: MapService, private http: HttpClient, private dialog: MatDialog,
              private rest: RestAPI, private formBuilder: FormBuilder, private restService: RestCacheService,
              private settings: SettingsService) {
    this.editLevelForm = this.formBuilder.group({
      name: new FormControl(''),
      labelField: new FormControl(''),
      keyField: new FormControl('')
    });
  }

  ngAfterViewInit(): void {
    this.mapControl = this.mapService.get('base-areas-map');
    this.layerGroup = new MapLayerGroup('Auswahl', { order: -1 });
    this.mapControl.addGroup(this.layerGroup);
    this.isLoading$.next(true);
    this.fetchAreaLevels().subscribe(res => {
      this.selectAreaLevel(this.presetLevels[0]);
      this.colorSelection = this.activeLevel!.symbol?.fillColor || 'black';
      this.isLoading$.next(false);
    })
    this.setupEditLevelCard();
    this.subscriptions.push(this.settings.baseDataSettings$.subscribe(bs => this.isProcessing = bs.processes?.areas || false));
    this.subscriptions.push(this.settings.projectSettings$.subscribe(ps => {
      this.projectArea = (ps.projectArea.indexOf('EMPTY') >= 0)? '': ps.projectArea;
    }));
    this.settings.fetchBaseDataSettings();
    this.settings.fetchProjectSettings();
  }

  /**
   * fetch areas
   */
  fetchAreaLevels(): Observable<AreaLevel[]> {
    const query = this.http.get<AreaLevel[]>(this.rest.URLS.arealevels).pipe(tap(areaLevels => {
      this.presetLevels = [];
      this.customAreaLevels = [];
      areaLevels.forEach(level => {
        if (environment.production) {
          level.tileUrl = level.tileUrl?.replace('http:', 'https:');
        }
        if (level.isPreset)
          this.presetLevels.push(level);
        else
          this.customAreaLevels.push(level);
      })
      this.presetLevels = sortBy(this.presetLevels, 'order');
      this.customAreaLevels = sortBy(this.customAreaLevels, 'order');
    }));
    return query;
  }

  setupEditLevelCard(): void {
    this.editArealevelCard.dialogOpened.subscribe(ok => {
      this.editLevelForm.reset({
        name: this.activeLevel?.name,
        labelField: this.activeLevel?.labelField,
        keyField: this.activeLevel?.keyField
      });
      if (this.activeLevel?.isPreset) {
        this.editLevelForm.controls['name'].disable();
      }
      else {
        this.editLevelForm.controls['name'].enable();
      }
      this.colorSelection = this.activeLevel?.symbol?.strokeColor || 'black';
    })
    this.editArealevelCard.dialogConfirmed.subscribe((ok)=>{
      this.editLevelForm.markAllAsTouched();
      if (this.editLevelForm.invalid) return;
      let attributes: any = this.enableLayerCheck!.checked? {
        symbol: {
          strokeColor: this.colorSelection
        }
      }: {
        symbol: null
      }
      if (!this.activeLevel?.isPreset) {
        attributes['name'] = this.editLevelForm.value.name;
        attributes['labelField'] = this.editLevelForm.value.labelField;
        attributes['keyField'] = this.editLevelForm.value.keyField;
      }
      this.editArealevelCard.setLoading(true);
      this.http.patch<AreaLevel>(`${this.rest.URLS.arealevels}${this.activeLevel?.id}/`, attributes
      ).subscribe(arealevel => {
        Object.assign(this.activeLevel!, arealevel);
        this.editArealevelCard.closeDialog(true);
        this.mapControl?.refresh({ internal: true });
        this.selectAreaLevel(arealevel);
      },(error) => {
        showAPIError(error, this.dialog);
        this.editArealevelCard.setLoading(false);
      });
    })
  }

  selectAreaLevel(areaLevel: AreaLevel): void {
    this.activeLevel = areaLevel;
    if (this.areaLayer) {
      this.layerGroup?.removeLayer(this.areaLayer);
      this.areaLayer = undefined;
    }
    if (!areaLevel) return;
    this.isLoading$.next(true);
    this.restService.getAreas(this.activeLevel.id,
      {targetProjection: this.mapControl?.map?.mapProjection, reset: true}).subscribe(areas => {
        this.areas = areas;
        this.areaLayer = new VectorLayer(this.activeLevel!.name, {
          description: 'Gebiete der ausgewählten Gebietseinheit',
          order: 0,
          opacity: 0.7,
          style: {
            fillColor: 'yellow',
            strokeColor: 'orange'
          },
          tooltipField: 'label',
          mouseOver: {
            enabled: true,
            style: {
              fillColor: 'lightblue',
              strokeColor: 'blue'
            }
          }
        })
        this.layerGroup?.addLayer(this.areaLayer);
        this.areaLayer.addFeatures(this.areas);
        this.activeLevel!.areaCount = this.areas.length;
        this.isLoading$.next(false);
        this.dataColumns = this.activeLevel!.areaFields;
        this.dataRows = this.areas.map(area => this.dataColumns.map(
          column => area.properties.attributes[column] || ''));
      })
  }

  onCreateAreaLevel(): void {
    let dialogRef = this.dialog.open(ConfirmDialogComponent, {
      panelClass: 'absolute',
      width: '500px',
      disableClose: true,
      data: {
        title: 'Neue benutzerdefinierte Gebietseinteilung',
        template: this.createLevelTemplate,
        closeOnConfirm: false,
        showCloseButton: false
      }
    });
    dialogRef.afterOpened().subscribe(sth => {
      this.editLevelForm.reset();
      this.editLevelForm.controls['name'].enable();
    });
    dialogRef.componentInstance.confirmed.subscribe(() => {
      // display errors for all fields even if not touched
      this.editLevelForm.markAllAsTouched();
      if (this.editLevelForm.invalid) return;
      dialogRef.componentInstance.isLoading$.next(true);
      let attributes = {
        name: this.editLevelForm.value.name,
        isPreset: false,
        isActive: true,
        order: 100 + this.customAreaLevels.length,
        source: { sourceType: 'FILE' }
      };
      this.http.post<AreaLevel>(this.rest.URLS.arealevels, attributes
      ).subscribe(level => {
        this.customAreaLevels.push(level);
        this.selectAreaLevel(level);
        dialogRef.close();
      },error => {
        showAPIError(error, this.dialog);
        dialogRef.componentInstance.isLoading$.next(false);
      });
    });
  }

  onDeleteAreaLevel(): void {
    if (!this.activeLevel || this.activeLevel.isPreset)
      return;
    const dialogRef = this.dialog.open(RemoveDialogComponent, {
      data: {
        title: $localize`Die Gebietseinteilung wirklich entfernen?`,
        confirmButtonText: $localize`Gebietseinteilung entfernen`,
        value: this.activeLevel.name
      }
    });
    dialogRef.afterClosed().subscribe((confirmed: boolean) => {
      if (confirmed) {
        this.http.delete(`${this.rest.URLS.arealevels}${this.activeLevel!.id}/`,
          { params: { force: true }}).subscribe(res => {
          const idx = this.customAreaLevels.indexOf(this.activeLevel!);
          if (idx >= 0) {
            this.customAreaLevels.splice(idx, 1);
            this.activeLevel = undefined;
            this.mapControl?.refresh({ internal: true });
          }
        }, error => {
          showAPIError(error, this.dialog);
        });
      }
    });
  }

  pullWfsAreas(): void {
    if (!this.activeLevel || !(this.activeLevel.source?.sourceType === 'WFS' || this.activeLevel.isPreset))
      return;
    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      width: '450px',
      panelClass: 'absolute',
      data: {
        title: `WFS Daten abrufen`, //für Gebietseinheit "${this.activeLevel.name}"`,
        confirmButtonText: 'Daten abrufen',
        closeOnConfirm: true,
        template: this.pullWfsTemplate
      }
    });
    dialogRef.componentInstance.confirmed.subscribe((confirmed: boolean) => {
      this.http.post(`${this.rest.URLS.arealevels}${this.activeLevel!.id}/pull_areas/`, { area_level: this.activeLevel!.id, truncate: true, simplify: false }).subscribe(res => {
        this.isProcessing = true;
      }, error => {
        showAPIError(error, this.dialog);
      });
    });
  }

  setFiles(event: Event){
    const element = event.currentTarget as HTMLInputElement;
    const files: FileList | null = element.files;
    this.file =  (files && files.length > 0)? files[0]: undefined;
  }

  uploadFile(): void {
    if (!this.activeLevel || this.activeLevel.source?.sourceType !== 'FILE')
      return;
    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      width: '450px',
      panelClass: 'absolute',
      data: {
        title: `Daten hochladen`, //für Gebietseinheit "${this.activeLevel.name}"`,
        confirmButtonText: 'Datei hochladen',
        closeOnConfirm: true,
        template: this.fileUploadTemplate
      }
    });
    dialogRef.componentInstance.confirmed.subscribe((confirmed: boolean) => {
      if (!this.file)
        return;
      const formData = new FormData();
      formData.append('file', this.file);
      this.http.post(`${this.rest.URLS.arealevels}${this.activeLevel!.id}/upload_shapefile/`, formData).subscribe(res => {
        this.isProcessing = true;
      }, error => {
        showAPIError(error, this.dialog);
      });
    });
  }

  onDeleteAreas(): void {
    if (!this.activeLevel)
      return;
    const dialogRef = this.dialog.open(RemoveDialogComponent, {
      data: {
        title: $localize`Die Gebiete der Gebietseinteilung wirklich entfernen?`,
        confirmButtonText: $localize`Daten löschen`,
        value: this.activeLevel.name,
        message: `Bei Bestätigung werden ${this.activeLevel.areaCount} Gebiete entfernt. `
      }
    });
    dialogRef.afterClosed().subscribe((confirmed: boolean) => {
      if (confirmed) {
        this.http.post(`${this.rest.URLS.arealevels}${this.activeLevel!.id}/clear/`, {}
        ).subscribe(res => {
          this.selectAreaLevel(this.activeLevel!);
        }, error => {
          showAPIError(error, this.dialog);
        });
      }
    });
  }

  setLevelActive(areaLevel: AreaLevel, active: boolean) {
    this.isLoading$.next(true);
    this.http.patch<AreaLevel>(`${this.rest.URLS.arealevels}${areaLevel.id}/`, { isActive: active }
    ).subscribe(level => {
      areaLevel.isActive = level.isActive;
      this.mapControl?.refresh({ internal: true });
      this.isLoading$.next(false);
    });
  }

  /**
   * patches layer-order of area-levels to their current place in the array
   *
   */
  patchOrder(areaLevels: AreaLevel[]): void {
    if (areaLevels.length === 0) return;
    let observables: Observable<any>[] = [];
    this.orderIsChanging$.next(true);
    for ( let i = 0; i < areaLevels.length; i += 1){
      const areaLevel = areaLevels[i];
      const request = this.http.patch<any>(`${this.rest.URLS.arealevels}${areaLevel.id}/`,
        { order: 100 + i + 1 });
      request.subscribe(res => {
        areaLevel.order = res.order;
      });
      // ToDo: chain - refresh and fetchlayers at the end
      observables.push(request);
    }
    forkJoin(...observables).subscribe(next => {
      this.mapControl?.refresh({ internal: true });
      this.customAreaLevels = sortBy(this.customAreaLevels, 'order');
      this.orderIsChanging$.next(false);
    })
  }

  /**
   * move currently selected custom area-level up or down
   *
   * @param direction - 'up' or 'down'
   */
  moveSelected(direction: string): void {
    if (!this.activeLevel) return;
    const idx = this.customAreaLevels.indexOf(this.activeLevel);
    if (direction === 'up'){
      if (idx <= 0) return;
      arrayMove(this.customAreaLevels, idx, idx - 1);
    }
    else if (direction === 'down'){
      if (idx === -1 || idx === this.customAreaLevels.length - 1) return;
      arrayMove(this.customAreaLevels, idx, idx + 1);
    }
    else return;

    this.patchOrder(this.customAreaLevels);
  }

  setPopAreaLevel(areaLevel: AreaLevel | null): void {
    if (!areaLevel || areaLevel.isPopLevel) return;
    const attributes = { isPopLevel: true };
    this.isLoading$.next(true);
    this.http.patch<AreaLevel>(`${this.rest.URLS.arealevels}${areaLevel.id}/`, attributes
    ).subscribe(al => {
      this.customAreaLevels.concat(this.presetLevels).forEach(l => l.isPopLevel = false);
      areaLevel.isPopLevel = al.isPopLevel;
      this.isLoading$.next(false);
    })
  }

  showDataTable(): void {
    if (!this.activeLevel) return;
    this.dialog.open(ConfirmDialogComponent, {
      panelClass: 'absolute',
      width: '400',
      disableClose: false,
      autoFocus: false,
      data: {
        title: `Datentabelle Gebiete der Gebietseinteilung "${this.activeLevel.name}"`,
        template: this.dataTemplate,
        hideConfirmButton: true,
        cancelButtonText: 'OK'
      }
    });
  }

  onMessage(log: LogEntry): void {
    if (log?.status?.finished) {
      this.isProcessing = false;
      this.fetchAreaLevels().subscribe(res => {
        if (this.activeLevel) this.selectAreaLevel(this.activeLevel);
      });
    }
  }

  ngOnDestroy(): void {
    this.mapControl?.destroy();
    this.subscriptions.forEach(subscription => subscription.unsubscribe());
  }
}
