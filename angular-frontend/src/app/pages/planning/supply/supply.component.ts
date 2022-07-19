import { Component, AfterViewInit, TemplateRef, ViewChild, OnDestroy } from '@angular/core';
import { MatDialog, MatDialogRef } from "@angular/material/dialog";
import { CookieService } from "../../../helpers/cookies.service";
import { PlanningService } from "../planning.service";
import {
  Infrastructure,
  Place,
  Service,
  PlanningProcess,
  Scenario, FieldType, PlaceField
} from "../../../rest-interfaces";
import { MapControl, MapService } from "../../../map/map.service";
import { FloatingDialog } from "../../../dialogs/help-dialog/help-dialog.component";
import { forkJoin, Observable, Subscription } from "rxjs";
import { map } from "rxjs/operators";
import { MapLayerGroup, VectorLayer } from "../../../map/layers";
import { PlaceFilterComponent } from "../place-filter/place-filter.component";
import { Point } from "ol/geom";
import { transform } from "ol/proj";
import { FormBuilder, FormGroup } from "@angular/forms";

@Component({
  selector: 'app-supply',
  templateUrl: './supply.component.html',
  styleUrls: ['./supply.component.scss']
})
export class SupplyComponent implements AfterViewInit, OnDestroy {
  @ViewChild('placeFilter') placeFilter?: PlaceFilterComponent;
  @ViewChild('filterTemplate') filterTemplate!: TemplateRef<any>;
  @ViewChild('placeCapEditTemplate') placeCapEditTemplate!: TemplateRef<any>;
  @ViewChild('placeFullEditTemplate') placeFullEditTemplate!: TemplateRef<any>;
  addPlaceMode: boolean;
  year?: number;
  realYears?: number[];
  prognosisYears?: number[];
  compareSupply = true;
  compareStatus = 'option 1';
  mapControl?: MapControl;
  layerGroup?: MapLayerGroup;
  placesLayer?: VectorLayer;
  places: Place[] = [];
  scenarioPlaces: Place[] = [];
  selectedPlace?: Place;
  placeDialogRef?: MatDialogRef<any>;
  activeService?: Service;
  activeProcess?: PlanningProcess;
  activeInfrastructure?: Infrastructure;
  activeScenario?: Scenario;
  subscriptions: Subscription[] = [];
  fieldTypes: FieldType[] = [];
  placeForm?: FormGroup;
  private mapClickSub?: Subscription;

  constructor(private dialog: MatDialog, private cookies: CookieService, private mapService: MapService,
              public planningService: PlanningService, private formBuilder: FormBuilder) {
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

  updatePlaces(): void {
    if (!this.activeInfrastructure || !this.activeService || !this.activeProcess) return;
    this.updateMapDescription();
    this.planningService.getPlaces(this.activeInfrastructure.id,
      {
        targetProjection: this.mapControl!.map!.mapProjection,
        addCapacities: true,
        filter: { columnFilter: true, hasCapacity: true }
      }).subscribe(places => {
      this.places = places;
      let showLabel = true;
      if (this.placesLayer){
        showLabel = !!this.placesLayer.showLabel;
        this.layerGroup?.removeLayer(this.placesLayer);
      }
      places?.forEach(place => {
        place.label = this.getFormattedCapacityString(
          [this.activeService!.id], place.capacity || 0);
      });
      this.placesLayer = new VectorLayer(this.activeInfrastructure!.name, {
        order: 0,
        description: this.activeInfrastructure!.name,
        opacity: 1,
        style: {
          fillColor: '#2171b5',
          strokeColor: 'black',
          symbol: 'circle'
        },
        labelField: 'label',
        showLabel: showLabel,
        tooltipField: 'name',
        select: {
          enabled: true,
          style: {
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
            range: [3, 20],
            scale: 'linear'
          },
          field: 'capacity',
          min: this.activeService?.minCapacity || 0,
          max: this.activeService?.maxCapacity || 1000
        }
      });
      this.layerGroup?.addLayer(this.placesLayer);
      this.placesLayer.addFeatures(places.map(place => {
        return { id: place.id, geometry: place.geom, properties: { name: place.name, label: place.label, capacity: place.capacity } }
      }));
      this.placesLayer?.featureSelected?.subscribe(evt => {
        if (evt.selected)
          this.selectPlace(evt.feature.get('id'));
        else {
          this.selectedPlace = undefined;
          this.placeDialogRef?.close();
        }
      })
    })
  }

  updateCapacities(): void {
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
    this.openPlacePreview(true);
  }

  openPlacePreview(editable?: boolean): void {
    if (this.placeDialogRef && this.placeDialogRef.getState() === 0)
      return;
    if (editable) {
      let attributes: any = { name: this.selectedPlace?.name };
      this.activeInfrastructure?.placeFields?.forEach(field => {
        attributes[field.name] = this.selectedPlace?.attributes[field.name];
      })
      this.placeForm = this.formBuilder.group(attributes);
    }
    const template = editable? this.placeFullEditTemplate: this.placeCapEditTemplate;
    this.placeDialogRef = this.dialog.open(FloatingDialog, {
      panelClass: 'help-container',
      hasBackdrop: false,
      autoFocus: false,
      data: {
        title: 'Ausgewählte Einrichtungen',
        template: template,
        resizable: true,
        dragArea: 'header',
        minWidth: '400px'
      }
    });
    this.placeDialogRef.afterClosed().subscribe(() => {
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
    if (!this.activeService) return;
    this.placeDialogRef?.close();
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
    const features = this.placesLayer?.addFeatures([place]);
    if (!features) return;
    this.placeDialogRef = this.dialog.open(FloatingDialog, {
      panelClass: 'help-container',
      hasBackdrop: false,
      autoFocus: false,
      data: {
        title: 'Einrichtung hinzufügen',
        template: this.placeFullEditTemplate,
        resizable: true,
        dragArea: 'header',
        minWidth: '400px'
      }
    });
    this.placeDialogRef.afterClosed().subscribe(ok => {
      this.placesLayer?.setSelectable(true);
      this.placesLayer?.removeFeature(features[0]);
      if (ok) {
        // ToDo: post place
      }
    })
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
