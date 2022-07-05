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
import * as d3 from "d3";
import { FilterColumn } from "../../../elements/filter-table/filter-table.component";
import { forkJoin, Observable, Subscription } from "rxjs";
import { map } from "rxjs/operators";
import { MapLayerGroup, VectorLayer } from "../../../map/layers";

@Component({
  selector: 'app-supply',
  templateUrl: './supply.component.html',
  styleUrls: ['./supply.component.scss']
})
export class SupplyComponent implements AfterViewInit, OnDestroy {
  @ViewChild('filterTemplate') filterTemplate!: TemplateRef<any>;
  @ViewChild('placePreviewTemplate') placePreviewTemplate!: TemplateRef<any>;
  addPlaceMode = false;
  year?: number;
  realYears?: number[];
  prognosisYears?: number[];
  compareSupply = true;
  compareStatus = 'option 1';
  infrastructures: Infrastructure[] = [];
  activeInfrastructure?: Infrastructure;
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
  activeScenario?: Scenario;
  _filterColumnsTemp: FilterColumn[] = [];
  filterColumns: FilterColumn[] = [];
  subscriptions: Subscription[] = [];

  constructor(private dialog: MatDialog, private cookies: CookieService, private mapService: MapService,
              public planningService: PlanningService) { }

  ngAfterViewInit(): void {
    this.mapControl = this.mapService.get('planning-map');
    this.layerGroup = new MapLayerGroup('Angebot', { order: -1 });
    this.mapControl.addGroup(this.layerGroup);
    if (this.planningService.isReady)
      this.initData();
    else {
      this.planningService.ready.subscribe(() => {
        this.initData();
      });
    }
  }

  initData(): void {
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
      this.applyUserSettings();
    });
  }

  applyUserSettings(): void {
    this.activeInfrastructure = this.infrastructures?.find(i => i.id === this.cookies.get('planning-infrastructure', 'number')) || ((this.infrastructures.length > 0)? this.infrastructures[0]: undefined);
    this.activeService = this.activeInfrastructure?.services.find(i => i.id === this.cookies.get('planning-service', 'number')) || ((this.activeInfrastructure && this.activeInfrastructure.services.length > 0)? this.activeInfrastructure.services[0]: undefined);
    this.updatePlaces();
  }

  onFilter(): void {
    if (!this.activeInfrastructure) return;
    let dialogRef = this.dialog.open(ConfirmDialogComponent, {
      panelClass: 'absolute',
      // width: '100%',
      maxWidth: '90vw',
      disableClose: false,
      data: {
        template: this.filterTemplate,
        closeOnConfirm: true,
        infoText: '<p>Mit dem Schieberegler rechts oben können Sie das Jahr wählen für das die Standortstruktur in der Tabelle angezeigt werden soll. Die Einstellung wird für die Default-Kartendarstellung übernommen.</p>' +
          '<p>Mit einem Klick auf das Filtersymbol in der Tabelle können Sie Filter auf die in der jeweiligen Spalte Indikatoren definieren. Die Filter werden grundsätzlich auf alle Jahre angewendet. In der Karte werden nur die gefilterten Standorte angezeigt.</p>'+
          '<p>Sie können einmal gesetzte Filter bei Bedarf im Feld „Aktuell verwendete Filter“ unter der Tabelle wieder löschen.</p>',
        context: {
          // services: [this.activeService],
          places: this.places,
          scenario: this.activeScenario,
          year: this.year,
          infrastructure: this.activeInfrastructure
        }
      }
    });
    dialogRef.afterClosed().subscribe((ok: boolean) => {  });
    dialogRef.componentInstance.confirmed.subscribe(() => {
      this.filterColumns = this._filterColumnsTemp;
      this.updatePlaces();
    });
  }

  onFilterChange(columns: FilterColumn[]): void {
    this._filterColumnsTemp = columns;
  }

  onInfrastructureChange(): void {
    this.cookies.set('planning-infrastructure', this.activeInfrastructure?.id);
    this.filterColumns = [];
    if (this.activeInfrastructure!.services.length > 0)
      this.activeService = this.activeInfrastructure!.services[0];
    this.updatePlaces();
  }

  onServiceChange(): void {
    this.cookies.set('planning-service', this.activeService?.id);
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
        this.capacities = capacities;
        let displayedPlaces: Place[] = [];
        this.places?.forEach(place => {
          if (!this.filter(place)) return;
          const capacity = this.getCapacity(this.activeService!.id, place.id);
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
              range: [1, 20],
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
  }

  private filter(place: Place): boolean {
    if (this.filterColumns.length === 0) return true;
    let match = false;
    this.filterColumns.forEach((filterColumn, i) => {
      const filter = filterColumn.filter!;
      if (filterColumn.service) {
        const cap = this.getCapacity(filterColumn.service.id, place.id);
        if (!filter.filter(cap)) return;
      }
      else if (filterColumn.attribute) {
        const value = place.properties.attributes[filterColumn.attribute];
        if (!filter.filter(value)) return;
      }
      if (i === this.filterColumns.length - 1) match = true;
    })
    return match;
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

  getCapacity(serviceId: number, placeId: number): number{
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
