import { Component, AfterViewInit, TemplateRef, ViewChild, OnDestroy } from '@angular/core';
import { ConfirmDialogComponent } from "../../../dialogs/confirm-dialog/confirm-dialog.component";
import { MatDialog, MatDialogRef } from "@angular/material/dialog";
import { CookieService } from "../../../helpers/cookies.service";
import { PlanningService } from "../planning.service";
import {
  Infrastructure,
  ExtLayer,
  ExtLayerGroup,
  Place,
  Service,
  Capacity,
  PlanningProcess,
  Scenario
} from "../../../rest-interfaces";
import { MapControl, MapService } from "../../../map/map.service";
import { FloatingDialog } from "../../../dialogs/help-dialog/help-dialog.component";
import { FilterColumn } from "../../../elements/filter-table/filter-table.component";
import { forkJoin, Observable, Subscription } from "rxjs";
import { map } from "rxjs/operators";
import { MapLayerGroup, VectorLayer } from "../../../map/layers";
import { PlaceFilterComponent } from "../place-filter/place-filter.component";

@Component({
  selector: 'app-supply',
  templateUrl: './supply.component.html',
  styleUrls: ['./supply.component.scss']
})
export class SupplyComponent implements AfterViewInit, OnDestroy {
  @ViewChild('placeFilter') placeFilter?: PlaceFilterComponent;
  @ViewChild('filterTemplate') filterTemplate!: TemplateRef<any>;
  @ViewChild('placePreviewTemplate') placePreviewTemplate!: TemplateRef<any>;
  addPlaceMode = false;
  year?: number;
  realYears?: number[];
  prognosisYears?: number[];
  compareSupply = true;
  compareStatus = 'option 1';
  infrastructures: Infrastructure[] = [];
  mapControl?: MapControl;
  layerGroup?: MapLayerGroup;
  placesLayer?: VectorLayer;
  places?: Place[];
  capacities?: Capacity[];
  selectedPlaces: Place[] = [];
  placeDialogRef?: MatDialogRef<any>;
  Object = Object;
  activeService?: Service;
  activeProcess?: PlanningProcess;
  activeInfrastructure?: Infrastructure;
  activeScenario?: Scenario;
  subscriptions: Subscription[] = [];

  constructor(private dialog: MatDialog, private cookies: CookieService, private mapService: MapService,
              public planningService: PlanningService) { }

  ngAfterViewInit(): void {
    this.mapControl = this.mapService.get('planning-map');
    this.layerGroup = new MapLayerGroup('Angebot', { order: -1 });
    this.mapControl.addGroup(this.layerGroup);
/*    if (this.planningService.isReady)
      this.initData();
    else {
      this.planningService.ready.subscribe(() => {
        this.initData();
      });
    }*/
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
    observables.push(this.planningService.getInfrastructures().pipe(map(infrastructures => {
      this.infrastructures = infrastructures;
    })));
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
      { targetProjection: this.mapControl!.map!.mapProjection }).subscribe(places => {
      this.places = places;
      let showLabel = true;
      if (this.placesLayer){
        showLabel = !!this.placesLayer.showLabel;
        this.layerGroup?.removeLayer(this.placesLayer);
      }
      this.planningService.getCapacities({ year: this.year!, service: this.activeService!.id }).subscribe(capacities => {
        this.placeFilter?.filterPlaces(this.places!).subscribe(filteredPlaces => {
          this.capacities = capacities;
          let displayedPlaces: Place[] = [];
          filteredPlaces?.forEach(place => {
            const capacity = this.getCapacity(place.id);
            if (!capacity) return;
            place.properties.capacity = capacity;
            place.properties.label = this.getFormattedCapacityString([this.activeService!.id], capacity);
            displayedPlaces.push(place);
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
              multi: true
            },
            mouseOver: {
              enabled: true,
              cursor: 'help'
            },
            valueMapping: {
              radius: {
                range: [5, 20],
                scale: 'linear'
              },
              field: 'capacity',
              min: this.activeService?.minCapacity || 0,
              max: this.activeService?.maxCapacity || 1000
            }
          });
          this.layerGroup?.addLayer(this.placesLayer);
          this.placesLayer.addFeatures(displayedPlaces,{
            properties: 'properties',
            geometry: 'geometry'
          });
          this.placesLayer?.featureSelected?.subscribe(evt => {
            if (evt.selected)
              this.selectPlace(evt.feature.get('id'));
            else
              this.deselectPlace(evt.feature.get('id'));
          })
        })
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

  getCapacity(placeId: number): number{
    const cap = this.capacities?.find(capacity => capacity.place === placeId);
    return cap?.capacity || 0;
  }

  selectPlace(placeId: number) {
    const place = this.places?.find(p => p.id === placeId);
    if (place) {
      this.selectedPlaces = [place, ...this.selectedPlaces];
      this.togglePlaceDialog(true);
    }
  }

  deselectPlace(placeId: number) {
    this.selectedPlaces = this.selectedPlaces.filter(p => p.id !== placeId);
    if (this.selectedPlaces.length === 0)
      this.togglePlaceDialog(false);
  }

  togglePlaceDialog(open: boolean): void {
    if (!open){
      this.placeDialogRef?.close();
      return;
    }
    if (this.placeDialogRef && this.placeDialogRef.getState() === 0)
      return;
    else
      this.placeDialogRef = this.dialog.open(FloatingDialog, {
        panelClass: 'help-container',
        hasBackdrop: false,
        autoFocus: false,
        data: {
          title: 'Ausgewählte Einrichtungen',
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

  updateMapDescription(): void {
    const desc = `Planungsprozess: ${this.activeProcess?.name} > ${this.activeScenario?.name} | ${this.year} <br>
                  Angebot an ${this.activeService?.name}`
    this.mapControl!.mapDescription = desc;
  }

  ngOnDestroy(): void {
    if (this.layerGroup) {
      this.mapControl?.removeGroup(this.layerGroup);
    }
    this.subscriptions.forEach(subscription => subscription.unsubscribe());
  }
}
