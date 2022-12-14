import { Component, AfterViewInit, TemplateRef, ViewChild, OnDestroy } from '@angular/core';
import { MatDialog, MatDialogRef } from "@angular/material/dialog";
import { CookieService } from "../../../helpers/cookies.service";
import { PlanningService } from "../planning.service";
import {
  Infrastructure,
  Place,
  Service,
  Scenario, FieldType, PlaceField, Capacity, User
} from "../../../rest-interfaces";
import { MapControl, MapLayerGroup, MapService } from "../../../map/map.service";
import { FloatingDialog } from "../../../dialogs/help-dialog/help-dialog.component";
import { forkJoin, Observable, Subscription } from "rxjs";
import { map } from "rxjs/operators";
import { VectorLayer } from "../../../map/layers";
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
import { AuthService } from "../../../auth.service";

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
  addPlaceMode: boolean = false;
  year?: number;
  realYears: number[] = [0];
  prognosisYears?: number[];
  mapControl?: MapControl;
  layerGroup?: MapLayerGroup;
  placesLayer?: VectorLayer;
  scenarioMarkerLayer?: VectorLayer;
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
  // capacities over all years (depending on scenario)
  capacities: Capacity[] = [];
  _editCapacities: Capacity[] = [];
  ignoreCapacities = false;
  processEditable = false;
  user?: User;

  constructor(private dialog: MatDialog, private cookies: CookieService, private mapService: MapService,
              public planningService: PlanningService, private formBuilder: FormBuilder,
              private http: HttpClient, private rest: RestAPI, private auth: AuthService) {
    this.auth.getCurrentUser().subscribe(user => {
      this.user = user;
      this.subscriptions.push(this.planningService.activeProcess$.subscribe(process => {
        this.processEditable = (process?.owner === this.user?.id) || !!process?.allowSharedChange;
      }));
    })
  }


  ngAfterViewInit(): void {
    this.mapControl = this.mapService.get('planning-map');
    this.layerGroup = this.mapControl.addGroup('Angebot', { order: -1 });
    this.applyUserSettings();
    this.initData();
  }

  initData(): void {
    this.planningService.getRealYears().subscribe(years => {
      this.realYears = years;
    });
    this.planningService.getPrognosisYears().subscribe(years => {
      this.prognosisYears = years;
    });
    this.planningService.getFieldTypes().subscribe(fieldTypes => {
      this.fieldTypes = fieldTypes;
    });
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
  }
  applyUserSettings(): void {
    this.ignoreCapacities = this.cookies.get('planning-ignore-capacities', 'boolean') || false;
  }

  onIgnoreCapacitiesChange(): void {
    this.cookies.set('planning-ignore-capacities', this.ignoreCapacities);
    this.updatePlaces();
  }

  onFilter(): void {
    this.updatePlaces();
  }

  updatePlaces(options?: { resetScenario?: boolean, selectPlaceId?: number }): void {
    this.layerGroup?.clear();
    if (!this.activeInfrastructure || !this.activeService || !this.activeScenario || !this.year) return;
    this.updateMapDescription();
    let placeOptions: any = {
      targetProjection: this.mapControl!.map!.mapProjection,
      addCapacities: true,
      filter: { columnFilter: true, year: this.year },
      reset: !this.activeScenario?.isBase && options?.resetScenario,
      scenario: this.activeScenario
    };
    this.placePreviewDialogRef?.componentInstance?.setLoading(true);

    let observables: Observable<any>[] = [];
    // fetch capacities over all years for place edit (and preview)
    observables.push(this.planningService.getCapacities({
      service: this.activeService,
      scenario: this.activeScenario,
      reset: (!this.activeScenario?.isBase) && options?.resetScenario
    }).pipe(map(capacities => {
      this.capacities = capacities;
    })));
    observables.push(this.planningService.getPlaces(placeOptions).pipe(map(places => this.places = places)));

    forkJoin(...observables).subscribe(() => {
      let legendElapsed = true;
      if (this.placesLayer) {
        legendElapsed = !!this.placesLayer.legend?.elapsed
        this.layerGroup?.removeLayer(this.placesLayer);
      }
      let mapPlaces: any[] = [];
      this.places?.forEach(place => {
        const tooltip = `<b>${place.name}</b><br>${this.activeService?.hasCapacity? this.getFormattedCapacityString(
          [this.activeService!.id], place.capacity || 0): place.capacity? 'Leistung wird angeboten': 'Leistung wird nicht angeboten'}`
        const doCompare = (place.capacity !== undefined) && (place.baseCapacity !== undefined);
        if (this.ignoreCapacities || place.capacity || place.scenario) {
          mapPlaces.push({
            id: place.id,
            geometry: place.geom,
            properties: {
              name: place.name, tooltip: tooltip, capacity: place.capacity || 0,
              scenarioPlace: place.scenario !== null,
              capDecreased: doCompare && (place.capacity! < place.baseCapacity!),
              capIncreased: doCompare && (place.capacity! > place.baseCapacity!)
            }
          });
        }
      });
      const values = mapPlaces.map(p => p.properties.capacity);
      const max = (mapPlaces.length === 0)? 0: Math.max(...values);
      const min = (mapPlaces.length === 0)? 0: Math.min(...values);
      const desc = `<b>${this.activeService?.facilityPluralUnit} ${this.year}</b><br>
                  mit Anzahl ${this.activeService?.capacityPluralUnit}<br>
                  Minimum: ${min.toLocaleString()}<br>
                  Maximum: ${max.toLocaleString()}`;
      // ToDo description with filter
      this.placesLayer = this.layerGroup?.addVectorLayer(this.activeInfrastructure!.name, {
        order: 0,
        description: desc,
        style: {
          fillColor: '#2171b5',
          strokeWidth: 1,
          strokeColor: 'black',
          symbol: 'circle'
        },
        labelField: 'name',
        tooltipField: 'tooltip',
        select: {
          enabled: true,
          style: {
            strokeWidth: 1,
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
          field: 'capacity',
          // min: this.activeService?.minCapacity || 0,
          min: 0,
          max: Math.max(this.activeService?.maxCapacity || 10, 10)
        },
        labelOffset: { y: 15 },
        legend: {
          entries: [
            { label: `mit Leistung "${this.activeService?.name}"`, color: '#2171b5', strokeColor: 'black' },
            { label: `ohne Leistung "${this.activeService?.name}"`, color: 'lightgrey', strokeColor: 'black' }
          ],
          elapsed: legendElapsed
        }
      });

      this.placesLayer?.addFeatures(mapPlaces);
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
      this.placesLayer?.featuresSelected?.subscribe(features => {
        // on map selection deselect the previously selected ones by just setting empty list
        this.selectedPlaces = [];
        features.forEach(f => this.selectPlace(f.get('id'), true));
      })
      this.placesLayer?.featuresDeselected?.subscribe(features => {
        features.forEach(f => this.selectPlace(f.get('id'), false));
      })

      // add layer for marking changes in scenario
      if (!this.activeScenario?.isBase) {
        this.scenarioMarkerLayer = this.layerGroup?.addVectorLayer('Änderungen zu Status Quo', {
          order: 1,
          zIndex: (this.placesLayer?.getZIndex() || 0) + 1,
          description: 'im Szenario verändert',
          style: {
            strokeWidth: 3,
            symbol: 'circle'
          },
          valueStyles: {
            radius: {
              range: [5, 20],
              scale: 'linear'
            },
            strokeColor: {
              colorFunc: (feat => feat.get('scenarioPlace')? '#00c4ff': feat.get('capDecreased')? '#fc450c' : feat.get('capIncreased')? '#00ff28': '')
            },
            field: 'capacity',
            // min: this.activeService?.minCapacity || 0,
            min: 0,
            max: Math.max(this.activeService?.maxCapacity || 10, 10)
          },
          legend: {
            entries: [
              { label: 'Kapazität verringert', color: 'rgba(0,0,0,0)', strokeColor: '#fc450c' },
              { label: 'Kapazität erhöht', color: 'rgba(0,0,0,0)', strokeColor: '#00ff28' },
              { label: 'Zusätzlicher Standort', color: 'rgba(0,0,0,0)', strokeColor: '#00c4ff' },
            ],
            elapsed: legendElapsed
          }
        });
        // only add places with changes (compared to status quo) to marker layer
        this.scenarioMarkerLayer?.addFeatures(mapPlaces.filter(
          place => place.properties.scenarioPlace || place.properties.capDecreased || place.properties.capIncreased
        ));
      }

      this.placePreviewDialogRef?.componentInstance?.setLoading(false);
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
        title: 'Ausgewählte Einrichtung(en)',
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
                  <b>${this.activeService?.facilityPluralUnit} ${this.year} mit Anzahl ${this.activeService?.capacityPluralUnit}
                  ${(this.planningService.getPlaceFilters(this.activeInfrastructure).length > 0)? ' (gefiltert)': ''}</b>`
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
        // clear scenario cache (to force update on rating page)
        this.planningService.clearCache(this.activeScenario!.id.toString());
        this.planningService.scenarioChanged.emit(this.activeScenario);
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
          this.planningService.scenarioChanged.emit(this.activeScenario);
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
        // clear scenario cache (to force update on rating page)
        this.planningService.clearCache(this.activeScenario!.id.toString());
        this.planningService.resetCapacities(this.activeScenario!.id, this.activeService!.id);
        this.updatePlaces({ resetScenario: true });
        this.planningService.scenarioChanged.emit(this.activeScenario);
        dialogRef.componentInstance.setLoading(false);
        dialogRef.close();
      }, error => {
        dialogRef.componentInstance.setLoading(false);
        // ToDo: error
      })
    })
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
