import { AfterViewInit, Component, OnDestroy, TemplateRef, ViewChild } from '@angular/core';
import { MapControl, MapService } from "../../../map/map.service";
import { Area, AreaLevel, Layer, LayerGroup } from "../../../rest-interfaces";
import { BehaviorSubject, forkJoin, Observable } from "rxjs";
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
import { FileHandle } from "../../../helpers/dragndrop.directive";


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
  legendGroup?: LayerGroup;
  editLevelForm: FormGroup;
  areaLayer?: Layer;
  areas: Area[] = [];
  isLoading$ = new BehaviorSubject<boolean>(false);
  orderIsChanging$ = new BehaviorSubject<boolean>(false);
  Object = Object;
  dataColumns: string[] = [];
  dataRows: any[][] = [];
  file?: File;
  uploadErrors: any = {};

  constructor(private mapService: MapService, private http: HttpClient, private dialog: MatDialog,
              private rest: RestAPI, private formBuilder: FormBuilder, private restService: RestCacheService) {
    this.editLevelForm = this.formBuilder.group({
      name: new FormControl(''),
      labelField: new FormControl(''),
      keyField: new FormControl('')
    });
  }

  ngAfterViewInit(): void {
    this.mapControl = this.mapService.get('base-areas-map');
    this.legendGroup = this.mapControl.addGroup({
      name: 'Auswahl',
      order: -1
    }, false)
    this.isLoading$.next(true);
    this.fetchAreaLevels().subscribe(res => {
      this.selectAreaLevel(this.presetLevels[0]);
      this.colorSelection = this.activeLevel!.symbol?.fillColor || 'black';
      this.isLoading$.next(false);
    })
    this.setupEditLevelCard();
  }

  /**
   * fetch areas
   */
  fetchAreaLevels(): Observable<AreaLevel[]> {
    const query = this.http.get<AreaLevel[]>(this.rest.URLS.arealevels);
    query.subscribe((areaLevels) => {
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
    });
    return query;
  }

  refreshAreaLevel(areaLevel: AreaLevel): Observable<AreaLevel> {
    const query = this.http.get<AreaLevel>(`${this.rest.URLS.arealevels}${areaLevel.id}/`);
    query.subscribe(al => {
      Object.assign(areaLevel, al);
    });
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
      this.editLevelForm.setErrors(null);
    })
    this.editArealevelCard.dialogConfirmed.subscribe((ok)=>{
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
        this.selectAreaLevel(arealevel, true);
      },(error) => {
        this.editLevelForm.setErrors(error.error);
        this.editArealevelCard.setLoading(false);
      });
    })
  }

  selectAreaLevel(areaLevel: AreaLevel, reset: boolean = false): void {
    this.activeLevel = areaLevel;
    if (this.areaLayer) {
      this.mapControl?.removeLayer(this.areaLayer.id!);
      this.areaLayer = undefined;
    }
    if (!areaLevel) return;
    this.isLoading$.next(true);
    this.restService.getAreas(this.activeLevel.id,
      {targetProjection: this.mapControl?.map?.mapProjection, reset: reset}).subscribe(areas => {
        this.areas = areas;
        this.areaLayer = this.mapControl?.addLayer({
          name: this.activeLevel!.name,
          description: '',
          group: this.legendGroup?.id,
          order: 0,
          type: 'vector',
          opacity: 1,
          symbol: {
            fillColor: 'yellow',
            strokeColor: 'orange',
            symbol: 'line'
          }
        }, {
          visible: true,
          tooltipField: 'label',
          mouseOver: {
            fillColor: 'lightblue',
            strokeColor: 'blue'
          }
        });
        this.mapControl?.addFeatures(this.areaLayer!.id!, this.areas);
        this.activeLevel!.areaCount = this.areas.length;
        this.isLoading$.next(false);
        this.dataColumns = this.activeLevel!.areaFields;
        this.dataRows = this.areas.map(area => this.dataColumns.map(
          column => area.properties.attributes[column] || ''));
      })
  }

  onCreateArea(): void {
    let dialogRef = this.dialog.open(ConfirmDialogComponent, {
      panelClass: 'absolute',
      width: '300px',
      disableClose: true,
      data: {
        title: 'Neue benutzerdefinierte Gebietseinteilung',
        template: this.createLevelTemplate,
        closeOnConfirm: false
      }
    });
    dialogRef.afterOpened().subscribe(sth => {
      this.editLevelForm.reset();
      this.editLevelForm.controls['name'].enable();
      this.editLevelForm.setErrors(null);
    });
    dialogRef.componentInstance.confirmed.subscribe(() => {
      // display errors for all fields even if not touched
      this.editLevelForm.markAllAsTouched();
      if (this.editLevelForm.invalid) return;
      dialogRef.componentInstance.isLoading = true;
      let attributes = {
        name: this.editLevelForm.value.name,
        isPreset: false,
        isActive: false,
        order: 100 + this.customAreaLevels.length,
        source: { sourceType: 'FILE' }
      };
      this.http.post<AreaLevel>(this.rest.URLS.arealevels, attributes
      ).subscribe(level => {
        this.customAreaLevels.push(level);
        dialogRef.close();
      },(error) => {
        this.editLevelForm.setErrors(error.error);
        dialogRef.componentInstance.isLoading = false;
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
        this.http.delete(`${this.rest.URLS.arealevels}${this.activeLevel!.id}/`
        ).subscribe(res => {
          const idx = this.customAreaLevels.indexOf(this.activeLevel!);
          if (idx >= 0) {
            this.customAreaLevels.splice(idx, 1);
            this.activeLevel = undefined;
            this.mapControl?.refresh({ internal: true });
          }
        }, error => {
          console.log('there was an error sending the query', error);
        });
      }
    });
  }

  pullWfsAreas(): void {
    if (!this.activeLevel || this.activeLevel.source?.sourceType !== 'WFS')
      return;
    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      width: '450px',
      data: {
        title: `WFS Daten abrufen`, //für Gebietseinheit "${this.activeLevel.name}"`,
        confirmButtonText: 'Daten abrufen',
        closeOnConfirm: false,
        template: this.pullWfsTemplate
      }
    });
    dialogRef.componentInstance.confirmed.subscribe((confirmed: boolean) => {
      dialogRef.componentInstance.isLoading = true;
      this.http.post(`${this.rest.URLS.arealevels}${this.activeLevel!.id}/pull_areas/`,
        { truncate: true, simplify: false }).subscribe(res => {
        dialogRef.close();
        this.selectAreaLevel(this.activeLevel!, true);
      }, error => {
        this.uploadErrors = error.error;
        dialogRef.componentInstance.isLoading = false;
      });
    });
    dialogRef.afterClosed().subscribe(ok => {
      this.uploadErrors = {};
    })
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
      data: {
        title: `Daten hochladen`, //für Gebietseinheit "${this.activeLevel.name}"`,
        confirmButtonText: 'Datei hochladen',
        template: this.fileUploadTemplate
      }
    });
    dialogRef.componentInstance.confirmed.subscribe((confirmed: boolean) => {
      if (!this.file)
        return;
      const formData = new FormData();
      formData.append('file', this.file);
      dialogRef.componentInstance.isLoading = true;
      this.http.post(`${this.rest.URLS.arealevels}${this.activeLevel!.id}/upload_shapefile/`, formData).subscribe(res => {
        dialogRef.close();
        this.refreshAreaLevel(this.activeLevel!).subscribe(al => this.selectAreaLevel(al, true));
      }, error => {
        this.uploadErrors = error.error;
        dialogRef.componentInstance.isLoading = false;
      });
    });
    dialogRef.afterClosed().subscribe(ok => {
      this.uploadErrors = {};
    })
  }

  onDeleteAreas(): void {
    if (!this.activeLevel)
      return;
    const dialogRef = this.dialog.open(RemoveDialogComponent, {
      data: {
        title: $localize`Die Gebiete der Gebietseinheit wirklich entfernen?`,
        confirmButtonText: $localize`Daten löschen`,
        value: this.activeLevel.name,
        message: `Bei Bestätigung werden ${this.activeLevel.areaCount} Gebiete entfernt. `
      }
    });
    dialogRef.afterClosed().subscribe((confirmed: boolean) => {
      if (confirmed) {
        this.http.post(`${this.rest.URLS.arealevels}${this.activeLevel!.id}/clear/`, {}
        ).subscribe(res => {
          this.selectAreaLevel(this.activeLevel!, true);
        }, error => {
          console.log('there was an error sending the query', error);
        });
      }
    });
  }

  setLevelActive(areaLevel: AreaLevel, active: boolean) {
    this.http.patch<AreaLevel>(`${this.rest.URLS.arealevels}${areaLevel.id}/`, { isActive: active }
    ).subscribe(level => {
      areaLevel.isActive = level.isActive;
      this.mapControl?.refresh({ internal: true });
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

  setDefaultAreaLevel(areaLevel: AreaLevel | null): void {
    if (!areaLevel || areaLevel.isDefaultPopLevel) return;
    const attributes = { isDefaultPopLevel: true };
    this.http.patch<AreaLevel>(`${this.rest.URLS.arealevels}${areaLevel.id}/`, attributes
    ).subscribe(al => {
      this.customAreaLevels.concat(this.presetLevels).forEach(l => l.isDefaultPopLevel = false);
      areaLevel.isDefaultPopLevel = al.isDefaultPopLevel;
    })
  }

  showDataTable(): void {
    if (!this.activeLevel) return;
    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      panelClass: 'absolute',
      width: '400',
      disableClose: false,
      autoFocus: false,
      data: {
        title: `Datentabelle Gebiete der Gebietseinheit "${this.activeLevel.name}"`,
        template: this.dataTemplate,
        hideConfirmButton: true,
        cancelButtonText: 'OK'
      }
    });
  }

  ngOnDestroy(): void {
    this.mapControl?.destroy();
  }

}
