import { Component, AfterViewInit, TemplateRef, ViewChild, OnDestroy } from '@angular/core';
import { MatDialog, MatDialogRef } from "@angular/material/dialog";
import { CookieService } from "../../../helpers/cookies.service";
import { PlanningService } from "../planning.service";
import {
  Infrastructure,
  Place,
  Service,
  PlanningProcess,
  Scenario, FieldType, PlaceField, Capacity
} from "../../../rest-interfaces";
import { MapControl, MapService } from "../../../map/map.service";
import { FloatingDialog } from "../../../dialogs/help-dialog/help-dialog.component";
import { forkJoin, Observable, Subscription } from "rxjs";
import { map } from "rxjs/operators";
import { MapLayerGroup, VectorLayer } from "../../../map/layers";
import { PlaceFilterComponent } from "../place-filter/place-filter.component";
import { Geometry, Point } from "ol/geom";
import { transform } from "ol/proj";
import { FormBuilder, FormGroup } from "@angular/forms";
import { HttpClient } from "@angular/common/http";
import { RestAPI } from "../../../rest-api";
import { WKT } from "ol/format";
import { ConfirmDialogComponent } from "../../../dialogs/confirm-dialog/confirm-dialog.component";
import { sortBy } from "../../../helpers/utils";
import { RemoveDialogComponent } from "../../../dialogs/remove-dialog/remove-dialog.component";
import { SimpleDialogComponent } from "../../../dialogs/simple-dialog/simple-dialog.component";

@Component({
  selector: 'app-supply',
  templateUrl: './supply.component.html',
  styleUrls: ['./supply.component.scss']
})
export class SupplyComponent implements AfterViewInit, OnDestroy {
  @ViewChild('placeFilter') placeFilter?: PlaceFilterComponent;
  @ViewChild('filterTemplate') filterTemplate!: TemplateRef<any>;
  @ViewChild('placePreviewTemplate') placePreviewTemplate!: TemplateRef<any>;
  @ViewChild('placeEditTemplate') placeEditTemplate!: TemplateRef<any>;
  @ViewChild('placeCapacitiesEditTemplate') placeCapacitiesEditTemplate!: TemplateRef<any>;
  addPlaceMode: boolean;
  year?: number;
  realYears: number[] = [0];
  prognosisYears?: number[];
  compareSupply = true;
  compareStatus = 'option 1';
  mapControl?: MapControl;
  layerGroup?: MapLayerGroup;
  placesLayer?: VectorLayer;
  places: Place[] = [];
  selectedPlaces: Place[] = [];
  placePreviewDialogRef?: MatDialogRef<any>;
  activeService?: Service;
  activeInfrastructure?: Infrastructure;
  activeScenario?: Scenario;
  subscriptions: Subscription[] = [];
  fieldTypes: FieldType[] = [];
  placeForm?: FormGroup;
  private mapClickSub?: Subscription;
  capacities: Capacity[] = [];
  _editCapacities: Capacity[] = [];

  constructor(private dialog: MatDialog, private cookies: CookieService, private mapService: MapService,
              public planningService: PlanningService, private formBuilder: FormBuilder,
              private http: HttpClient, private rest: RestAPI) {
    this.addPlaceMode = false;
  }

  ngAfterViewInit(): void {
    this.mapControl = this.mapService.get('planning-map');
    this.layerGroup = new MapLayerGroup('Angebot', { order: -1 });
    this.mapControl.addGroup(this.layerGroup);
    this.initData();
  }

  initData(): void {
    this.subscriptions.push(this.planningService.activeInfrastructure$.subscribe(infrastructure => {
      this.activeInfrastructure = infrastructure;
    }))
    this.subscriptions.push(this.planningService.activeService$.subscribe(service => {
      this.activeService = service;
      this.updatePlaces();
    }))
    this.subscriptions.push(this.planningService.year$.subscribe(year => {
      this.year = year;
      this.updatePlaces();
    }));
    this.subscriptions.push(this.planningService.activeScenario$.subscribe(scenario => {
      this.activeScenario = scenario;
      this.updatePlaces();
    }));
    let observables: Observable<any>[] = [];
    observables.push(this.planningService.getRealYears().pipe(map(years => {
      this.realYears = years;
    })));
    observables.push(this.planningService.getPrognosisYears().pipe(map(years => {
      this.prognosisYears = years;
    })));
    observables.push(this.planningService.getFieldTypes().pipe(map(fieldTypes => {
      this.fieldTypes = fieldTypes;
    })))
    forkJoin(...observables).subscribe(() => {
      this.updatePlaces();
    });
  }

  onFilter(): void {
    this.updatePlaces();
  }

  updatePlaces(options?: { resetScenario?: boolean, selectPlaceId?: number }): void {
    if (!this.activeInfrastructure || !this.activeService || !this.activeScenario) return;
    this.updateMapDescription();
    let placeOptions: any = {
      targetProjection: this.mapControl!.map!.mapProjection,
      addCapacities: true,
      filter: { columnFilter: true, year: this.year },
      reset: !this.activeScenario?.isBase && options?.resetScenario,
      scenario: this.activeScenario
    };
    this.placePreviewDialogRef?.componentInstance?.setLoading(true);
    this.planningService.getCapacities({
      service: this.activeService,
      scenario: this.activeScenario,
      reset: (!this.activeScenario?.isBase) && options?.resetScenario
    }).subscribe(capacities => {
      this.capacities = capacities;
      this.planningService.getPlaces(placeOptions).subscribe(places => {
        console.log(places);
        this.places = places;
        let showLabel = true;
        let legendElapsed = true;
        if (this.placesLayer) {
          showLabel = !!this.placesLayer.showLabel;
          legendElapsed = !!this.placesLayer.legend?.elapsed
          this.layerGroup?.removeLayer(this.placesLayer);
        }
        let max = 0;
        let min = Number.MAX_VALUE;
        this.places?.forEach(place => {
          const capacity = place.capacity || 0;
          max = Math.max(max, capacity);
          if (place.capacity) min = Math.min(min, capacity);
        });
        const desc = `<b>${this.activeService?.facilityPluralUnit} ${this.year}</b><br>
                    mit Anzahl ${this.activeService?.capacityPluralUnit}<br>
                    Minimum: ${min.toLocaleString()}<br>
                    Maximum: ${max.toLocaleString()}`;
        // ToDo description with filter
        this.placesLayer = new VectorLayer(this.activeInfrastructure!.name, {
          order: 0,
          description: desc,
          opacity: 1,
          style: {
            fillColor: '#2171b5',
            strokeWidth: 2,
            strokeColor: 'black',
            symbol: 'circle'
          },
          labelField: 'name',
          showLabel: showLabel,
          tooltipField: 'tooltip',
          select: {
            enabled: true,
            style: {
              strokeWidth: 2,
              fillColor: 'yellow',
            },
            multi: true
          },
          mouseOver: {
            enabled: true,
            cursor: 'pointer'
          },
          valueStyles: {
            radius: {
              range: [5, 20],
              scale: 'linear'
            },
            fillColor: {
              colorFunc: (capacity => (capacity) ? '#2171b5' : 'lightgrey')
            },
            strokeColor: {
              colorFunc: (feat => (feat.get('scenario') !== null) ? '#fc450c' : '#174a79')
            },
            field: 'capacity',
            // min: this.activeService?.minCapacity || 0,
            min: 0,
            max: Math.max(this.activeService?.maxCapacity || 10, 10)
          },
          labelOffset: { y: 15 },
          legend: {
            entries: [
              { label: 'Standort mit Leistung', color: '#2171b5', strokeColor: 'black' },
              { label: 'Standort ohne Leistung', color: 'lightgrey', strokeColor: 'black' },
              { label: 'Szenariostandort', color: 'lightgrey', strokeColor: '#fc450c' },
            ],
            elapsed: legendElapsed
          }
        });
        this.layerGroup?.addLayer(this.placesLayer);
        this.placesLayer.addFeatures(places.map(place => {
          const tooltip = `<b>${place.name}</b><br>
                           ${this.activeService?.hasCapacity? this.getFormattedCapacityString([this.activeService!.id], place.capacity || 0): place.capacity? 'Leistung wird angeboten': 'Leistung wird nicht angeboten'}`
          return {
            id: place.id,
            geometry: place.geom,
            properties: { name: place.name, tooltip: tooltip, capacity: place.capacity, scenario: place.scenario }
          }
        }));
        if (options?.selectPlaceId !== undefined) {
          const place = this.places.find(p => p.id === options.selectPlaceId);
          if (place) {
            this.selectedPlaces = [place];
            this.openPlacePreview();
          }
        }
        if (this.selectedPlaces.length > 0) {
          const ids = this.selectedPlaces.map(p => p.id);
          // after change, places might only be copies with old attributes
          this.selectedPlaces = this.places.filter(p => ids.indexOf(p.id) > -1);
          this.placesLayer?.selectFeatures(ids, { silent: true });
        }
        this.placesLayer?.featureSelected?.subscribe(evt => {
          this.selectPlace(evt.feature.get('id'), evt.selected);
        })
        this.placePreviewDialogRef?.componentInstance?.setLoading(false);
      });
    });
  }

  getFormattedCapacityString(services: number[], capacity: number): string {
    if (!this.activeInfrastructure) return '';
    let units = new Set<string>();
    this.activeInfrastructure.services.filter(service => services.indexOf(service.id) >= 0).forEach(service => {
      units.add((capacity === 1)? service.capacitySingularUnit: service.capacityPluralUnit);
    })
    return `${capacity} ${Array.from(units).join('/')}`
  }

  selectPlace(placeId: number, select: boolean) {
    const place = this.places?.find(p => p.id === placeId);
    if (!place) return;
    if (select) {
      this.selectedPlaces.push(place);
      this.openPlacePreview();
    }
    else {
      const idx = this.selectedPlaces.indexOf(place);
      if (idx > -1) {
        this.selectedPlaces.splice(idx, 1);
      }
      if (this.selectedPlaces.length === 0) this.placePreviewDialogRef?.close();
    }
  }

  getCapacities(place: Place): Capacity[] {
    return sortBy(this.capacities.filter(c => c.place === place.id), 'fromYear')
  }

  openPlacePreview(): void {
    if (this.placePreviewDialogRef && this.placePreviewDialogRef.getState() === 0)
      return;
    const template = this.placePreviewTemplate;
    this.placePreviewDialogRef = this.dialog.open(FloatingDialog, {
      panelClass: 'help-container',
      hasBackdrop: false,
      autoFocus: false,
      data: {
        title: 'Ausgewählte Einrichtungen',
        template: template,
        context: { edit: true },
        resizable: true,
        dragArea: 'header',
        minWidth: '400px'
      }
    });
    this.placePreviewDialogRef.afterClosed().subscribe(() => {
      this.selectedPlaces = [];
      this.placesLayer?.clearSelection();
    })
  }

  updateMapDescription(): void {
    const desc = `${this.activeScenario?.name}<br>
                  Angebot für Leistung "${this.activeService?.name}"<br>
                  <b>${this.activeService?.facilityPluralUnit} ${this.year} mit Anzahl ${this.activeService?.capacityPluralUnit}</b>`
    this.mapControl?.setDescription(desc);
  }

  togglePlaceMode(): void {
    this.addPlaceMode = !this.addPlaceMode;
    this.mapControl?.setCursor(this.addPlaceMode? 'marker': 'default');
    this.placesLayer?.setSelectable(!this.addPlaceMode);
    if (this.mapClickSub) {
      this.mapClickSub.unsubscribe();
      this.mapClickSub = undefined;
    }
    if (this.addPlaceMode) {
      this.mapClickSub = this.mapControl?.map?.mapClicked.subscribe(coords => {
        this.addPlace(coords);
      })
    }
  }

  private addPlace(coords: number[]): void {
    if (!this.activeService || !this.activeScenario) return;
    const geometry = new Point(transform(coords, 'EPSG:4326', this.mapControl?.map?.mapProjection));
    const place: Place = {
      id: -1,
      name: 'Neue Einrichtung',
      infrastructure: this.activeService.infrastructure,
      attributes: {},
      geom: geometry
    };
    this.selectedPlaces = [place];
    this.placesLayer?.setSelectable(false);
    const features = this.placesLayer?.addFeatures([{ geometry: place.geom, scenario: this.activeScenario.id }]);
    if (!features) return;
    let fields: any = { name: place.name };
    const fieldNames = this.activeInfrastructure?.placeFields?.map(f => f.name) || [];
    fieldNames.forEach(field => {
      fields[field] = undefined;
    })
    this.placeForm = this.formBuilder.group(fields);
    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      panelClass: 'absolute',
      width: '400px',
      disableClose: true,
      autoFocus: false,
      data: {
        title: 'Standort hinzufügen',
        template: this.placeEditTemplate,
        context: { place: place }
      }
    });
    dialogRef.afterClosed().subscribe(ok => {
      this.placesLayer?.setSelectable(true);
      this.placesLayer?.removeFeature(features[0]);
    })
    dialogRef.componentInstance.confirmed.subscribe(() => {
      const attributes: any = { };
      fieldNames.forEach(field => {
        const value = this.placeForm!.value[field];
        if (value !== null) attributes[field] = value;
      });
      const format = new WKT();
      let wkt = `SRID=${this.mapControl?.map?.mapProjection.replace('EPSG:', '')};${format.writeGeometry(place.geom as Geometry)}`;
      const dialogRefWait = SimpleDialogComponent.show('Füge Ort hinzu und berechne Erreichbarkeiten. Bitte warten', this.dialog, { showAnimatedDots: true });
      this.http.post<Place>(this.rest.URLS.places, {
        name: this.placeForm!.value.name,
        infrastructure: this.activeService?.infrastructure,
        scenario: this.activeScenario!.id,
        geom: wkt,
        attributes: attributes
      }).subscribe(place => {
        dialogRef.close();
        dialogRefWait.close();
        this.togglePlaceMode();
        // this.precalcTraveltime(place);
        this.updatePlaces({ resetScenario: true, selectPlaceId: place.id });
      }, error => {
        this.placeForm?.setErrors(error.error);
        dialogRefWait.close();
      })
    })
  }

/*  precalcTraveltime(place: Place): void {
    this.http.post<any>(`${this.rest.URLS.matrixCellPlaces}precalculate_traveltime/`,
      {places: [place.id], verbose: false}).subscribe(() => {
    },(error) => {
    })
  }*/

  showEditPlace(place: Place): void {
    let fields: any = { name: place.name };
    const fieldNames = this.activeInfrastructure?.placeFields?.map(f => f.name) || [];
    fieldNames.forEach(field => {
      fields[field] = place.attributes[field];
    })
    this.placeForm = this.formBuilder.group(fields);
    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      panelClass: 'absolute',
      width: '400px',
      disableClose: true,
      autoFocus: false,
      data: {
        title: 'Standort bearbeiten',
        template: this.placeEditTemplate,
        context: { place: place },
        showCloseButton: true
      }
    });
    dialogRef.componentInstance.confirmed.subscribe(ok => {
      const attributes: any = { };
      fieldNames.forEach(field => {
        const value = this.placeForm!.value[field];
        if (value !== null) attributes[field] = value;
      });
      this.http.patch<Place>(`${this.rest.URLS.places}${place.id}/`, {
        name: this.placeForm!.value.name,
        attributes: attributes
      }).subscribe(p => {
        dialogRef.close();
        this.selectedPlaces = [p];
        this.updatePlaces({ resetScenario: true });
      }, error => {
        // ToDo: show error
        console.log(error)
      })
    })
  }

  removePlace(place: Place): void {
    const dialogRef = this.dialog.open(RemoveDialogComponent, {
      data: {
        title: $localize`Den Standort wirklich aus dem Szenario entfernen?`,
        confirmButtonText: $localize`Standort entfernen`,
        value: place.name
      }
    });
    dialogRef.afterClosed().subscribe((confirmed: boolean) => {
      if (confirmed) {
        this.http.delete<Place>(`${this.rest.URLS.places}${place.id}/`).subscribe(p => {
          this.placePreviewDialogRef?.close();
          this.selectedPlaces = [];
          this.updatePlaces({ resetScenario: true });
        }, error => {
          // ToDo: show error
          console.log(error)
        })
      }
    });
  }

  showEditCapacities(place: Place): void {
    if (!this.activeService) return;
    this._editCapacities = this.getCapacities(place).map(cap => Object.assign({}, cap));
    if (this._editCapacities.length === 0 || this._editCapacities[0].fromYear !== 0) {
      const startCap: Capacity = {
        id: -1,
        place: place.id,
        service: this.activeService.id,
        scenario: (this.activeScenario?.isBase)? undefined: this.activeScenario!.id,
        fromYear: 0,
        capacity: 0,
      };
      this._editCapacities.splice(0, 0, startCap);
    }
    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      panelClass: 'absolute',
      width: '650px',
      disableClose: true,
      autoFocus: false,
      data: {
        title: 'Kapazitäten editieren',
        template: this.placeCapacitiesEditTemplate,
        context: { place: place },
        showCloseButton: true
      }
    });
    dialogRef.componentInstance.confirmed.subscribe(() => {
      dialogRef.componentInstance.setLoading(true);
      this.http.post<Capacity[]>(`${this.rest.URLS.capacities}replace/`, {
        scenario: this.activeScenario!.id,
        service: this.activeService!.id,
        place: place.id,
        capacities: this._editCapacities
      }).subscribe(capacities => {
        this.planningService.resetCapacities(this.activeScenario!.id, this.activeService!.id);
        this.updatePlaces({ resetScenario: true });
        dialogRef.componentInstance.setLoading(false);
        dialogRef.close();
      }, error => {
        dialogRef.componentInstance.setLoading(false);
        // ToDo: error
      })
    })
    // ToDo: reset scenario
    // this.planningService.resetCapacities(this.activeService.id);
  }

  removeEditCap(i: number): void {
    const cap = this._editCapacities[i];
    this._editCapacities.splice(i, 1);
  }

  insertEditCap(i: number, place: Place): void {
    const capacity: Capacity = {
      id: -1,
      place: place.id,
      service: this.activeService!.id,
      scenario: this.activeScenario?.id,
      fromYear: (i === 1)? ((this._editCapacities.length === 1)? this.realYears[0] + 1: this._editCapacities[i].fromYear - 1): this._editCapacities[i-1].fromYear + 1,
      capacity: 0,
    }
    this._editCapacities.splice(i, 0, capacity);
  }

  getFieldType(field: PlaceField): FieldType | undefined {
    return this.fieldTypes.find(ft => ft.id === field.fieldType);
  }

  zoomToPlaceExtent(): void {
    this.placesLayer?.zoomTo();
  }

  ngOnDestroy(): void {
    if (this.layerGroup) {
      this.mapControl?.removeGroup(this.layerGroup);
    }
    this.subscriptions.forEach(subscription => subscription.unsubscribe());
    this.mapControl?.map?.setCursor('');
    this.mapClickSub?.unsubscribe();
  }
}
