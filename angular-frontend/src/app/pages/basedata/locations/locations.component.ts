import { AfterViewInit, Component, OnDestroy, TemplateRef, ViewChild } from '@angular/core';
import { MapControl, MapService } from "../../../map/map.service";
import {
  Infrastructure,
  Place,
  Capacity,
  Service,
  FieldType,
  PlaceField, LogEntry
} from "../../../rest-interfaces";
import * as fileSaver from "file-saver";
import { RestAPI } from "../../../rest-api";
import { BehaviorSubject, Subscription } from "rxjs";
import { HttpClient } from "@angular/common/http";
import { ConfirmDialogComponent } from "../../../dialogs/confirm-dialog/confirm-dialog.component";
import { MatDialog, MatDialogRef } from "@angular/material/dialog";
import { FloatingDialog } from "../../../dialogs/help-dialog/help-dialog.component";
import { showAPIError, sortBy } from "../../../helpers/utils";
import { InputCardComponent } from "../../../dash/input-card.component";
import { RemoveDialogComponent } from "../../../dialogs/remove-dialog/remove-dialog.component";
import { SimpleDialogComponent } from "../../../dialogs/simple-dialog/simple-dialog.component";
import { MapLayerGroup, VectorLayer } from "../../../map/layers";
import { PlanningService } from "../../planning/planning.service";
import { SettingsService } from "../../../settings.service";

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
  @ViewChild('fileUploadTemplate') fileUploadTemplate?: TemplateRef<any>;
  infrastructures: Infrastructure[] = [];
  fieldTypes: FieldType[] = [];
  fieldRemoved: boolean = false;
  selectedInfrastructure?: Infrastructure;
  placeFields: PlaceField[] = [];
  editFields: PlaceEditField[] = [];
  mapControl?: MapControl;
  layerGroup?: MapLayerGroup;
  placesLayer?: VectorLayer;
  addPlaceMode = false;
  isLoading$ = new BehaviorSubject<boolean>(false);
  places?: Place[];
  dataColumns: string[] = [];
  dataRows: any[][] = [];
  selectedPlaces: Place[] = [];
  placeDialogRef?: MatDialogRef<any>;
  file?: File;
  isProcessing = false;
  subscriptions: Subscription[] = [];

  constructor(private mapService: MapService, private rest: RestAPI, private http: HttpClient,
              private dialog: MatDialog, private restService: PlanningService, private settings: SettingsService) {
    // make sure data requested here is up-to-date
    this.restService.reset();
  }

  ngAfterViewInit(): void {
    this.mapControl = this.mapService.get('base-locations-map');
    this.layerGroup = new MapLayerGroup('Standorte', { order: -1 });
    this.mapControl.addGroup(this.layerGroup);
    this.isLoading$.next(true);
    this.http.get<FieldType[]>(this.rest.URLS.fieldTypes).subscribe(fieldTypes => {
      this.fieldTypes = fieldTypes;
      this.restService.getInfrastructures().subscribe(infrastructures => {
        this.infrastructures = infrastructures;
        this.isLoading$.next(false);
      })
    })
    this.subscriptions.push(this.settings.baseDataSettings$.subscribe(bs => {
      this.isProcessing = bs.processes?.routing || false;
    }));
    this.setupAttributeCard();
  }

  onInfrastructureChange(options?: {reset?: boolean}): void {
    this.places = [];
    if (this.placesLayer) {
      this.layerGroup?.removeLayer(this.placesLayer);
      this.placesLayer = undefined;
    }
    if (!this.selectedInfrastructure) return;
    this.placeFields = this.selectedInfrastructure.placeFields?.filter(f => !f.isPreset) || [];
    this.editFields = JSON.parse(JSON.stringify(this.placeFields));
    this.editFields.forEach(f => f.removed = false);
    this.isLoading$.next(true);
    this.restService.getPlaces( { infrastructure: this.selectedInfrastructure, reset: options?.reset }).subscribe(places => {
      this.selectedInfrastructure!.placesCount = places.length;
      this.isLoading$.next(false);
      this.dataColumns = ['Standort'];
      this.selectedInfrastructure!.placeFields?.forEach(field => {
        this.dataColumns.push(field.name);
      })
      this.selectedInfrastructure!.services.forEach(service => {
        let columnTitle = (service.hasCapacity)? `${service.name} (Kapazität)`: service.name;
        this.dataColumns.push(columnTitle);
        this.isLoading$.next(true);
        this.restService.getCapacities({ service: service, reset: options?.reset }).subscribe(serviceCapacities => {
          this.places?.forEach(place => {
            if (!place.capacities) place.capacities = [];
            const capacities = serviceCapacities.filter(c => c.place === place.id && c.service === service.id);
            const startCap = capacities.find(c => c.fromYear === 0);
            if (startCap === undefined)
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
    const showLabel = (this.placesLayer?.showLabel !== undefined)? this.placesLayer.showLabel: true;
    if (this.placesLayer) {
      this.layerGroup?.removeLayer(this.placesLayer);
      this.placesLayer = undefined;
    }
    if (!this.places) return;
    this.placesLayer = new VectorLayer(this.selectedInfrastructure!.name, {
        order: 0,
        description: this.selectedInfrastructure!.name,
        opacity: 1,
        style: {
          fillColor: '#2171b5',
          strokeColor: 'black',
          symbol: 'circle'
        },
        labelField: 'name',
        tooltipField: 'name',
        select: {
          style: { fillColor: 'yellow' },
          enabled: true,
          multi: true
        },
        showLabel: showLabel,
        labelOffset: { y: 15 },
      });
    this.layerGroup?.addLayer(this.placesLayer);
    this.placesLayer.addFeatures(this.places.map(place => { return {
      id: place.id, geometry: place.geom, properties: { name: place.name } }}));
    this.placesLayer?.featuresSelected?.subscribe(features => {
      features.forEach(f => this.selectPlace(f.get('id'), true));
    })
    this.placesLayer?.featuresDeselected?.subscribe(features => {
      features.forEach(f => this.selectPlace(f.get('id'), false));
    })
  }

  selectPlace(placeId: number, select: boolean) {
    const place = this.places?.find(p => p.id === placeId);
    if (!place) return;
    if (select) {
      this.selectedPlaces.push(place);
      this.showPlaceDialog();
    }
    else {
      const idx = this.selectedPlaces.indexOf(place);
      if (idx > -1) {
        this.selectedPlaces.splice(idx, 1);
      }
      if (this.selectedPlaces.length === 0) this.placeDialogRef?.close();
    }
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
      this.selectedPlaces = [];
      this.placesLayer?.clearSelection();
    })
  }

  downloadTemplate(): void {
    const url = `${this.rest.URLS.places}create_template/`;
    const dialogRef = SimpleDialogComponent.show('Bereite Template vor. Bitte warten', this.dialog, { showAnimatedDots: true });
    this.http.post(url, { infrastructure: this.selectedInfrastructure?.id }, { responseType: 'blob' }).subscribe((res:any) => {
      const blob: any = new Blob([res],{ type:'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
      dialogRef.close();
      fileSaver.saveAs(blob, 'standorte-'+ this.selectedInfrastructure?.name + '.xlsx');
    },(error) => {
      dialogRef.close();
      showAPIError(error, this.dialog);
    });
  }

  showDataTable(): void {
    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      panelClass: 'absolute',
      width: '400',
      disableClose: false,
      autoFocus: false,
      data: {
        title: 'Standorte des Infrastrukturbereichs ' + this.selectedInfrastructure?.name,
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
      let row: any = [place.name];
      this.selectedInfrastructure!.placeFields?.forEach(field => {
        row.push(place.attributes[field.name]);
      })
      this.selectedInfrastructure!.services?.forEach(service => {
        const capacity = place.capacities?.find(capacity => capacity.service === service.id && capacity.fromYear === 0)?.capacity;
        const entry = (capacity === undefined)? '': (service.hasCapacity)? capacity: (capacity)? 'Ja': 'Nein';
        row.push(entry);
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
      this.editFields = JSON.parse(JSON.stringify(this.placeFields || []));
      this.editFields.forEach(f => f.removed = false);
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
        // all fields are being sent to API, fields not in body will autmatically be removed
        const body = { place_fields: _this.editFields.filter(f => !f.removed) };
        _this.http.patch<Infrastructure>(`${_this.rest.URLS.infrastructures}${_this.selectedInfrastructure!.id}/`, body).subscribe(infrastructure => {
          Object.assign(_this.selectedInfrastructure!, infrastructure);
          _this.isLoading$.next(false);
          _this.editAttributesCard?.closeDialog();
          _this.onInfrastructureChange({ reset: true });
        }, error => {
          showAPIError(error, _this.dialog);
          _this.isLoading$.next(false);
        });
      }
    })
  }

  addField(): void {
    this.editFields?.push({
      name: '', label: '', unit: '',// sensitive: false,
      fieldType: (this.fieldTypes.find(ft => ft.ftype == 'NUM') || this.fieldTypes[0]).id,
      new: true, removed: false
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
        infoText: "<p>Sie können eigene Klassifikationen (z.B. Klassifikation „Bewertung“ mit den Klassen „gut“, „mittel“, „schlecht“) definieren, um diese danach einzelnen Standorteigenschaften (z.B. „Gebäudezustand“) zuordnen. </p> " +
          "<p>Klassifikationen erleichtern zum einen eine strukturierte Dateneingabe. Zum anderen können Sie in daviplan später als Grundlage für Sortier- und Filterfunktionen verwendet werden.</p>" +
          "<p>Klicken Sie auf die Schaltfläche „Hinzufügen“ unter der linken Liste „Klassifikationen“, um eine Klassifikation hinzuzufügen. Klicken Sie anschließen auf die Schaltfläche „Hinzufügen“ unter der rechten Liste „Klassen“, um dieser Klassifikation einzelne Klassen zuzufügen.</p>" +
          "<p>Klicken Sie auf „OK“, wenn Sie fertig sind. Achtung: Dieser Eingabebereich hat keinen Entwurfsmodus mit “Abbrechen” und “Speichern”. Alle Eintragungen und Änderungen an den Klassifikationen und Klassen werden daher sofort in die Datenbank übernommen. </p>"
      }
    });
  }

  getFieldType(id: number): FieldType {
    return this.fieldTypes.find(f => f.id === id) || this.fieldTypes[0];
  }

  uploadTemplate(): void {
    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      width: '450px',
      panelClass: 'absolute',
      data: {
        title: `Template hochladen`,
        confirmButtonText: 'Datei hochladen',
        template: this.fileUploadTemplate,
        closeOnConfirm: true
      }
    });
    dialogRef.componentInstance.confirmed.subscribe((confirmed: boolean) => {
      if (!this.file)
        return;
      const formData = new FormData();
      formData.append('infrastructure', this.selectedInfrastructure!.id.toString());
      formData.append('excel_file', this.file);
      const url = `${this.rest.URLS.places}upload_template/`;
      this.isProcessing = true;
      this.http.post(url, formData).subscribe(res => {
      }, error => {
        showAPIError(error, this.dialog);
        this.isProcessing = false;
      });
    });
  }

  setFiles(event: Event){
    const element = event.currentTarget as HTMLInputElement;
    const files: FileList | null = element.files;
    this.file =  (files && files.length > 0)? files[0]: undefined;
  }

  onDeletePlaces(): void {
    if (!this.selectedInfrastructure)
      return;
    const dialogRef = this.dialog.open(RemoveDialogComponent, {
      data: {
        title: $localize`Die Standorte wirklich entfernen?`,
        confirmButtonText: $localize`Daten löschen`,
        value: this.selectedInfrastructure.name,
        message: `Bei Bestätigung werden ${this.selectedInfrastructure.placesCount} Standorte entfernt. `
      }
    });
    dialogRef.afterClosed().subscribe((confirmed: boolean) => {
      if (confirmed) {
        this.http.post(`${this.rest.URLS.places}clear/`, { infrastructure: this.selectedInfrastructure!.id }
        ).subscribe(res => {
          this.onInfrastructureChange({ reset: true });
        }, error => {
          showAPIError(error, this.dialog);
        });
      }
    });
  }

  onMessage(log: LogEntry): void {
    if (log?.status?.finished) {
      this.isProcessing = false;
      this.onInfrastructureChange({ reset: true });
    }
  }

  ngOnDestroy(): void {
    this.mapControl?.destroy();
    this.subscriptions.forEach(subscription => subscription.unsubscribe());
  }
}
