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
  realYears?: number[];
  prognosisYears?: number[];
  compareSupply = true;
  compareStatus = 'option 1';
  mapControl?: MapControl;
  layerGroup?: MapLayerGroup;
  placesLayer?: VectorLayer;
  // displayedPlaces: Place[] = [];
  places: Place[] = [];
  // scenarioPlaces: Place[] = [];
  selectedPlace?: Place;
  placePreviewDialogRef?: MatDialogRef<any>;
  activeService?: Service;
  activeProcess?: PlanningProcess;
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
    this.subscriptions.push(this.planningService.activeProcess$.subscribe(process => {
      this.activeProcess = process;
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

  updatePlaces(resetScenario?: boolean): void {
    if (!this.activeInfrastructure || !this.activeService || !this.activeProcess) return;
    this.updateMapDescription();
    const options: any = {
        targetProjection: this.mapControl!.map!.mapProjection,
        addCapacities: true,
        filter: { columnFilter: true }
    };
    this.places = [];
    let observables: Observable<any>[] = [];
    observables.push(this.planningService.getCapacities({ service: this.activeService.id }).pipe(map(capacities => {
      this.capacities = capacities;
    })))
    observables.push(this.planningService.getPlaces(this.activeInfrastructure.id, options).pipe(map(places => {
      this.places = this.places.concat(places);
    })));
    if (this.activeScenario && !this.activeScenario.isBase) {
      // always reload scenario places
      const scenOptions = {...options, reset: resetScenario, scenario: this.activeScenario.id};
      observables.push(this.planningService.getPlaces(this.activeInfrastructure.id, scenOptions).pipe(map(places => {
        this.places = this.places.concat(places);
      })));
    }
    forkJoin(...observables).subscribe(() => {
      let showLabel = true;
      if (this.placesLayer){
        showLabel = !!this.placesLayer.showLabel;
        this.layerGroup?.removeLayer(this.placesLayer);
      }
      this.places?.forEach(place => {
        place.label = this.getFormattedCapacityString(
          [this.activeService!.id], place.capacity || 0);
      });
      this.placesLayer = new VectorLayer(this.activeInfrastructure!.name, {
        order: 0,
        description: this.activeInfrastructure!.name,
        opacity: 1,
        style: {
          fillColor: '#2171b5',
          strokeWidth: 2,
          strokeColor: 'black',
          symbol: 'circle'
        },
        labelField: 'label',
        showLabel: showLabel,
        tooltipField: 'name',
        select: {
          enabled: true,
          style: {
            strokeWidth: 2,
            fillColor: 'yellow',
          },
          multi: false
        },
        mouseOver: {
          enabled: true,
          cursor: 'help'
        },
        valueStyles: {
          radius: {
            range: [5, 20],
            scale: 'linear'
          },
          strokeColor: {
            colorFunc: (feat => (feat.get('scenario') !== null)? '#fc450c': '#174a79')
          },
          field: 'capacity',
          min: this.activeService?.minCapacity || 0,
          max: this.activeService?.maxCapacity || 1000
        }
      });
      this.layerGroup?.addLayer(this.placesLayer);
      this.placesLayer.addFeatures(this.places.map(place => {
        return { id: place.id, geometry: place.geom, properties: { name: place.name, label: place.label, capacity: place.capacity, scenario: place.scenario } }
      }));
      if (this.selectedPlace) {
        this.placesLayer?.selectFeatures([this.selectedPlace.id], { silent: true });
      }
      this.placesLayer?.featureSelected?.subscribe(evt => {
        if (evt.selected)
          this.selectPlace(evt.feature.get('id'));
        else {
          this.selectedPlace = undefined;
          this.placePreviewDialogRef?.close();
        }
      })
    })
  }

  getFormattedCapacityString(services: number[], capacity: number): string {
    if (!this.activeInfrastructure) return '';
    let units = new Set<string>();
    this.activeInfrastructure.services.filter(service => services.indexOf(service.id) >= 0).forEach(service => {
      units.add((capacity === 1)? service.capacitySingularUnit: service.capacityPluralUnit);
    })
    return `${capacity} ${Array.from(units).join('/')}`
  }

  selectPlace(placeId: number) {
    this.selectedPlace = this.places?.find(p => p.id === placeId);
/*    if (this.selectedPlace?.scenario)
      this.openFullEdit*/
    this.openPlacePreview();
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
      this.placesLayer?.clearSelection();
    })
  }

  updateMapDescription(): void {
    const desc = `Planungsprozess: ${this.activeProcess?.name} > ${this.activeScenario?.name} | ${this.year} <br>
                  Angebot an ${this.activeService?.name}`
    this.mapControl!.mapDescription = desc;
  }

  togglePlaceMode(): void {
    this.addPlaceMode = !this.addPlaceMode;
    this.mapControl?.map?.setCursor(this.addPlaceMode? 'crosshair': '');
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
    this.selectedPlace = place;
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
      }
    });
    dialogRef.afterClosed().subscribe(ok => {
      this.placesLayer?.setSelectable(true);
      this.placesLayer?.removeFeature(features[0]);
      if (ok) {
        const attributes: any = { };
        fieldNames.forEach(field => {
          const value = this.placeForm!.value[field];
          if (value !== null) attributes[field] = value;
        });
        const format = new WKT();
        let wkt = `SRID=${this.mapControl?.map?.mapProjection.replace('EPSG:', '')};${format.writeGeometry(place.geom as Geometry)}`;
        this.http.post<Place>(this.rest.URLS.places, {
          name: this.placeForm!.value.name,
          infrastructure: this.activeService?.infrastructure,
          scenario: this.activeScenario!.id,
          geom: wkt,
          attributes: attributes
        }).subscribe(place => {
          dialogRef.close();
          this.updatePlaces(true);
        }, error => {
          // ToDo: show error
          console.log(error)
        })
      }
    })
  }

  showEditPlace(): void {
    if (!this.selectedPlace) return;
    let fields: any = { name: this.selectedPlace.name };
    const fieldNames = this.activeInfrastructure?.placeFields?.map(f => f.name) || [];
    fieldNames.forEach(field => {
      fields[field] = this.selectedPlace?.attributes[field];
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
      }
    });
    dialogRef.componentInstance.confirmed.subscribe(ok => {
      const attributes: any = { };
      fieldNames.forEach(field => {
        const value = this.placeForm!.value[field];
        if (value !== null) attributes[field] = value;
      });
      this.http.patch<Place>(`${this.rest.URLS.places}${this.selectedPlace!.id}/`, {
        name: this.placeForm!.value.name,
        attributes: attributes
      }).subscribe(place => {
        dialogRef.close();
        this.selectedPlace = place;
        this.updatePlaces(true);
      }, error => {
        // ToDo: show error
        console.log(error)
      })
    })
  }

  showEditCapacities(): void {
    if (!this.activeService || !this.selectedPlace) return;
    this._editCapacities = sortBy(this.capacities.filter(c => c.place === this.selectedPlace!.id), 'fromYear');
    if (this._editCapacities.length === 0 || this._editCapacities[0].fromYear !== 0) {
      const startCap: Capacity = {
        id: -1,
        place: this.selectedPlace.id,
        service: this.activeService.id,
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
      }
    });
    // ToDo: reset scenario
    // this.planningService.resetCapacities(this.activeService.id);
  }

  removeEditCap(i: number): void {
    this._editCapacities.splice(i, 1);
  }

  insertEditCap(i: number): void {
    const capacity: Capacity = {
      id: -1,
      place: this.selectedPlace!.id,
      service: this.activeService!.id,
      fromYear: (i === 1)? ((this._editCapacities.length === 1)? 2000: this._editCapacities[i].fromYear - 1): this._editCapacities[i-1].fromYear + 1,
      capacity: 0,
    }
    this._editCapacities.splice(i, 0, capacity);
  }

  getFieldType(field: PlaceField): FieldType | undefined {
    return this.fieldTypes.find(ft => ft.id === field.fieldType);
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
