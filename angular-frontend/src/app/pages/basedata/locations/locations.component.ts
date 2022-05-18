import { AfterViewInit, Component, OnDestroy, TemplateRef, ViewChild } from '@angular/core';
import { MapControl, MapService } from "../../../map/map.service";
import {
  Infrastructure,
  Place,
  LayerGroup,
  Layer,
  Capacity,
  Service,
  FieldType,
  PlaceField
} from "../../../rest-interfaces";
import { RestCacheService } from "../../../rest-cache.service";
import * as fileSaver from "file-saver";
import { RestAPI } from "../../../rest-api";
import { BehaviorSubject, forkJoin, Observable } from "rxjs";
import { HttpClient } from "@angular/common/http";
import { ConfirmDialogComponent } from "../../../dialogs/confirm-dialog/confirm-dialog.component";
import { MatDialog, MatDialogRef } from "@angular/material/dialog";
import { FloatingDialog } from "../../../dialogs/help-dialog/help-dialog.component";
import { sortBy } from "../../../helpers/utils";
import { InputCardComponent } from "../../../dash/input-card.component";
import { RemoveDialogComponent } from "../../../dialogs/remove-dialog/remove-dialog.component";

interface PlaceEditField extends PlaceField {
  edited?: boolean;
  new?: boolean;
  removed?: boolean;
}

@Component({
  selector: 'app-locations',
  templateUrl: './locations.component.html',
  styleUrls: ['./locations.component.scss']
})
export class LocationsComponent implements AfterViewInit, OnDestroy {
  @ViewChild('dataTemplate') dataTemplate?: TemplateRef<any>;
  @ViewChild('placePreviewTemplate') placePreviewTemplate!: TemplateRef<any>;
  @ViewChild('editAttributesCard') editAttributesCard!: InputCardComponent;
  @ViewChild('editClassificationsTemplate') editClassificationsTemplate!: TemplateRef<any>;
  infrastructures: Infrastructure[] = [];
  fieldTypes: FieldType[] = [];
  fieldRemoved: boolean = false;
  selectedInfrastructure?: Infrastructure;
  editFields: PlaceEditField[] = [];
  editErrors?: any;
  mapControl?: MapControl;
  legendGroup?: LayerGroup;
  placesLayer?: Layer;
  addPlaceMode = false;
  isLoading$ = new BehaviorSubject<boolean>(false);
  places?: Place[];
  dataColumns: string[] = [];
  dataRows: any[][] = [];
  selectedPlace?: Place;
  placeDialogRef?: MatDialogRef<any>;

  constructor(private mapService: MapService, private rest: RestAPI, private http: HttpClient,
              private dialog: MatDialog, private restService: RestCacheService) { }

  ngAfterViewInit(): void {
    this.mapControl = this.mapService.get('base-locations-map');
    this.legendGroup = this.mapControl.addGroup({
      name: 'Standorte',
      order: -1
    }, false);
    this.isLoading$.next(true);
    this.http.get<FieldType[]>(this.rest.URLS.fieldTypes).subscribe(fieldTypes => {
      this.fieldTypes = fieldTypes;
      this.restService.getInfrastructures().subscribe(infrastructures => {
        this.infrastructures = infrastructures;
        this.isLoading$.next(false);
      })
    })
    this.setupAttributeCard();
  }

  onInfrastructureChange(reset: boolean = false): void {
    this.places = [];
    this.mapControl?.removeLayer(this.placesLayer?.id!);
    if (!this.selectedInfrastructure) return;
    this.editFields = JSON.parse(JSON.stringify(this.selectedInfrastructure.placeFields));
    this.isLoading$.next(true);
    this.restService.getPlaces(this.selectedInfrastructure.id, { reset: reset }).subscribe(places => {
      this.isLoading$.next(false);
      this.dataColumns = ['Standort'];
      this.selectedInfrastructure!.placeFields?.forEach(field => {
        this.dataColumns.push(field.name);
      })
      this.selectedInfrastructure!.services.forEach(service => {
        this.dataColumns.push(`Kapazitäten ${service.name}`);
        this.isLoading$.next(true);
        this.restService.getCapacities({ service: service.id! }).subscribe(serviceCapacities => {
          this.places?.forEach(place => {
            if (!place.capacities) place.capacities = [];
            const capacities = serviceCapacities.filter(c => c.place === place.id && c.service === service.id);
            const startCap = capacities.find(c => c.fromYear === 0);
            if (!startCap)
              place.capacities.push({
                id: -1, place: place.id, service: service.id,
                fromYear: 0, scenario: undefined, capacity: 0
              })
            place.capacities.push(...capacities);
          })
          this.isLoading$.next(false);
        })
      })
      this.places = places;
      this.updateMap();
    })
  }

  updateMap(): void {
    this.mapControl?.removeLayer(this.placesLayer?.id!);
    if (!this.places) return;
    this.placesLayer = this.mapControl?.addLayer({
        order: 0,
        type: 'vector',
        group: this.legendGroup?.id,
        name: this.selectedInfrastructure!.name,
        description: this.selectedInfrastructure!.name,
        opacity: 1,
        symbol: {
          fillColor: '#2171b5',
          strokeColor: 'black',
          symbol: 'circle'
        },
        labelField: 'name',
        showLabel: true
      },
      {
        visible: true,
        tooltipField: 'name',
        selectable: true,
        select: {
          fillColor: 'yellow',
          multi: false
        },
      });
    this.mapControl?.clearFeatures(this.placesLayer!.id!);
    this.mapControl?.addFeatures(this.placesLayer!.id!, this.places);
    this.placesLayer?.featureSelected?.subscribe(evt => {
      const placeId = evt.feature.get('id');
      if (evt.selected){
        const place = this.places?.find(p => p.id === placeId);
        if (place) {
          this.selectedPlace = place;
          this.showPlaceDialog();
        }
      }
      else if (this.selectedPlace?.id === placeId) {
        this.selectedPlace = undefined;
        if (this.placeDialogRef) this.placeDialogRef.close();
      }
    })
  }

  showPlaceDialog(): void {
    if (this.placeDialogRef && this.placeDialogRef.getState() === 0)
      return;
    this.placeDialogRef = this.dialog.open(FloatingDialog, {
      panelClass: 'help-container',
      hasBackdrop: false,
      autoFocus: false,
      data: {
        title: 'Ausgewählte Einrichtung',
        template: this.placePreviewTemplate,
        resizable: true,
        dragArea: 'header',
        minWidth: '400px'
      }
    });
    this.placeDialogRef.afterClosed().subscribe(() => {
      this.selectedPlace = undefined;
      this.mapControl?.deselectAllFeatures(this.placesLayer!.id!);
    })
  }

  downloadTemplate(): void {
    const url = `${this.rest.URLS.places}create_template/`;
    this.isLoading$.next(true);
    this.http.post(url, { infrastructure: this.selectedInfrastructure?.id }, { responseType: 'blob' }).subscribe((res:any) => {
      const blob: any = new Blob([res],{ type:'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
      this.isLoading$.next(false);
      fileSaver.saveAs(blob, 'standorte-template.xlsx');
    },(error) => {
      this.isLoading$.next(false);
    });
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
    this.dataRows = [];
    let rows: any[][] = [];
    if (!(this.places && this.selectedInfrastructure)) return;
    this.isLoading$.next(true);
    this.places.forEach(place => {
      let row: any = [place.properties.name];
      this.selectedInfrastructure!.placeFields?.forEach(field => {
        row.push(place.properties.attributes[field.name]);
      })
      this.selectedInfrastructure!.services?.forEach(service => {
        row.push(place.capacities?.find(capacity => capacity.service === service.id && capacity.fromYear === 0)?.capacity || '');
      })
      rows.push(row);
    })
    this.dataRows = rows;
    this.isLoading$.next(false);
  }

  getPlaceCapacities(place: Place, service: Service): Capacity[]{
    return sortBy(place.capacities!.filter(c => c.service === service.id), 'fromYear');
  }

  setupAttributeCard(): void {
    this.editAttributesCard.dialogClosed.subscribe(() => {
      this.fieldRemoved = false;
      this.editErrors = undefined;
      this.editFields = JSON.parse(JSON.stringify(this.selectedInfrastructure?.placeFields || []));
    })
    this.editAttributesCard.dialogConfirmed.subscribe((ok)=> {
      const removeFields = this.editFields.filter(f => f.removed && !f.new);
      const _this = this;
      if (removeFields.length > 0) {
        const dialogRef = this.dialog.open(RemoveDialogComponent, {
          width: '500px',
          data: {
            title: 'Änderungen an den Attributen',
            confirmButtonText: 'Änderungen bestätigen',
            message: 'Die Änderungen enthalten Löschungen von bestehenden Attributen. Damit verbundene Daten werden ebenfalls gelöscht.',
            value: removeFields.map(r => r.name).join(', ')
          }
        });
        dialogRef.afterClosed().subscribe((confirmed: boolean) => {
          patch();
        });
      }
      else
        patch();

      function patch(){
        const changedFields = _this.editFields.filter(f => f.removed || f.new || f.edited);
        if (changedFields.length === 0) {
          _this.editAttributesCard?.closeDialog();
          return;
        }
        _this.isLoading$.next(true);
        const body = { place_fields: _this.editFields.filter(f => !f.removed) }
        _this.http.patch<Infrastructure>(`${_this.rest.URLS.infrastructures}${_this.selectedInfrastructure!.id}/`, body).subscribe(infrastructure => {
          Object.assign(_this.selectedInfrastructure!, infrastructure);
          _this.isLoading$.next(false);
          _this.editAttributesCard?.closeDialog();
          _this.onInfrastructureChange(true);
        }, error => {
          _this.isLoading$.next(false);
          _this.editErrors = error.error
        });
      }
    })
  }

  addField(): void {
    this.editFields?.push({
      name: '', unit: '', sensitive: false,
      fieldType: (this.fieldTypes.find(ft => ft.ftype == 'NUM') || this.fieldTypes[0]).id,
      new: true
    })
  }

  editClassifications(): void {
    this.dialog.open(ConfirmDialogComponent, {
      panelClass: 'absolute',
      width: '700px',
      disableClose: true,
      data: {
        title: 'Klassifikationen (Attributtypen)',
        template: this.editClassificationsTemplate,
        closeOnConfirm: true,
        hideConfirmButton: true,
        infoText: 'ToDo: Reihenfolge der Klassen erklären (je weiter oben, desto "besser"), Änderungen erfolgen sofort'
      }
    });
  }

  getFieldType(id: number): FieldType {
    return this.fieldTypes.find(f => f.id === id) || this.fieldTypes[0];
  }

  ngOnDestroy(): void {
    this.mapControl?.destroy();
  }
}
