import { AfterViewInit, ChangeDetectorRef, Component, OnDestroy, TemplateRef, ViewChild } from '@angular/core';
import { MapControl, MapService } from "../../../map/map.service";
import { AreaLevel, BasedataSettings, Layer, LayerGroup } from "../../../rest-interfaces";
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


@Component({
  selector: 'app-areas',
  templateUrl: './areas.component.html',
  styleUrls: ['../../../map/legend/legend.component.scss','./areas.component.scss']
})
export class AreasComponent implements AfterViewInit, OnDestroy {
  @ViewChild('editArealevelCard') editArealevelCard!: InputCardComponent;
  @ViewChild('enableLayerCheck') enableLayerCheck?: MatCheckbox;
  @ViewChild('createAreaLevel') createLevelTemplate?: TemplateRef<any>;
  mapControl?: MapControl;
  selectedAreaLevel?: AreaLevel;
  presetLevels: AreaLevel[] = [];
  customAreaLevels: AreaLevel[] = [];
  colorSelection: string = 'black';
  legendGroup?: LayerGroup;
  editLevelForm: FormGroup;
  orderIsChanging$ = new BehaviorSubject<boolean>(false);
  Object = Object;

  constructor(private mapService: MapService, private http: HttpClient, private dialog: MatDialog,
              private rest: RestAPI, private formBuilder: FormBuilder) {
    this.editLevelForm = this.formBuilder.group({
      name: new FormControl(''),
      labelField: new FormControl('')
    });
  }

  ngAfterViewInit(): void {
    this.mapControl = this.mapService.get('base-areas-map');
    this.legendGroup = this.mapControl.addGroup({
      name: 'Auswahl',
      order: -1
    }, false)

    this.fetchAreas().subscribe(res => {
      this.selectAreaLevel(this.presetLevels[0]);
      this.colorSelection = this.selectedAreaLevel!.symbol?.fillColor || 'black';
    })
    this.setupEditLevelCard();
  }

  /**
   * fetch areas
   */
  fetchAreas(): Observable<AreaLevel[]> {
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

  setupEditLevelCard(): void {
    this.editArealevelCard.dialogOpened.subscribe(ok => {
      this.editLevelForm.reset({
        name: this.selectedAreaLevel?.name,
        labelField: this.selectedAreaLevel?.labelField
      });
      if (this.selectedAreaLevel?.isPreset) {
        this.editLevelForm.controls['name'].disable();
        this.editLevelForm.controls['labelField'].disable();
      }
      else {
        this.editLevelForm.controls['name'].enable();
        this.editLevelForm.controls['labelField'].enable();
      }
      this.colorSelection = this.selectedAreaLevel?.symbol?.strokeColor || 'black';
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
      if (!this.selectedAreaLevel?.isPreset) {
        attributes['name'] = this.editLevelForm.value.name;
        attributes['labelField'] = this.editLevelForm.value.labelField;
      }
      this.editArealevelCard.setLoading(true);
      this.http.patch<AreaLevel>(`${this.rest.URLS.arealevels}${this.selectedAreaLevel?.id}/`, attributes
      ).subscribe(arealevel => {
        this.selectedAreaLevel!.name = arealevel.name;
        this.selectedAreaLevel!.labelField = arealevel.labelField;
        this.selectedAreaLevel!.symbol = arealevel.symbol;
        this.editArealevelCard.closeDialog(true);
        this.mapControl?.refresh({ internal: true });
      },(error) => {
        this.editLevelForm.setErrors(error.error);
        this.editArealevelCard.setLoading(false);
      });
    })
  }

  selectAreaLevel(areaLevel: AreaLevel): void {
    this.selectedAreaLevel = areaLevel;
    this.mapControl?.clearGroup(this.legendGroup!.id!);
    if (!areaLevel) return;
    const layer = this.mapControl?.addLayer({
      name: areaLevel.name,
      description: '',
      group: this.legendGroup?.id,
      order: 0,
      url: areaLevel.tileUrl!,
      type: 'vector-tiles',
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

  onDeleteArea(): void {
    if (!this.selectedAreaLevel || this.selectedAreaLevel.isPreset)
      return;
    const dialogRef = this.dialog.open(RemoveDialogComponent, {
      data: {
        title: $localize`Die Gebietseinteilung wirklich entfernen?`,
        confirmButtonText: $localize`Gebietseinteilung entfernen`,
        value: this.selectedAreaLevel.name
      }
    });
    dialogRef.afterClosed().subscribe((confirmed: boolean) => {
      if (confirmed) {
        this.http.delete(`${this.rest.URLS.arealevels}${this.selectedAreaLevel!.id}/`
        ).subscribe(res => {
          const idx = this.customAreaLevels.indexOf(this.selectedAreaLevel!);
          if (idx >= 0) {
            this.customAreaLevels.splice(idx, 1);
            this.selectedAreaLevel = undefined;
            this.mapControl?.refresh({ internal: true });
          }
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
    if (!this.selectedAreaLevel) return;
    const idx = this.customAreaLevels.indexOf(this.selectedAreaLevel);
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

  ngOnDestroy(): void {
    this.mapControl?.destroy();
  }

}
