import { Component, AfterViewInit, TemplateRef, ViewChild, OnDestroy } from '@angular/core';
import { ConfirmDialogComponent } from "../../../dialogs/confirm-dialog/confirm-dialog.component";
import { MatDialog, MatDialogRef } from "@angular/material/dialog";
import { CookieService } from "../../../helpers/cookies.service";
import { PlanningService } from "../planning.service";
import {
  Infrastructure,
  Layer,
  LayerGroup,
  Place,
  Service,
  Capacity,
  PlanningProcess,
  Scenario
} from "../../../rest-interfaces";
import { MapControl, MapService } from "../../../map/map.service";
import { FloatingDialog } from "../../../dialogs/help-dialog/help-dialog.component";
import * as d3 from "d3";

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
  infrastructures?: Infrastructure[];
  activeInfrastructure?: Infrastructure;
  mapControl?: MapControl;
  legendGroup?: LayerGroup;
  placesLayer?: Layer;
  places?: Place[];
  capacities?: Capacity[];
  selectedPlaces: Place[] = [];
  placeDialogRef?: MatDialogRef<any>;
  Object = Object;
  activeService?: Service;
  activeProcess?: PlanningProcess;
  activeScenario?: Scenario;

  constructor(private dialog: MatDialog, private cookies: CookieService, private mapService: MapService,
              public planningService: PlanningService) {
    this.planningService.getInfrastructures().subscribe(infrastructures => {
      this.infrastructures = infrastructures;
    })
  }

  ngAfterViewInit(): void {
    this.mapControl = this.mapService.get('planning-map');

    this.legendGroup = this.mapControl.addGroup({
      name: 'Angebot',
      order: -1
    }, false);

    if (this.planningService.isReady)
      this.initData();
    else {
      this.planningService.ready.subscribe(() => {
        this.initData();
      });
    }
  }

  initData(): void {
    this.planningService.year$.subscribe(year => {
      this.year = year;
      this.updatePlaces();
    })
    this.planningService.activeProcess$.subscribe(process => {
      this.activeProcess = process;
    })
    this.planningService.activeScenario$.subscribe(scenario => {
      this.activeScenario = scenario;
    })
    this.planningService.getRealYears().subscribe( years => {
      this.realYears = years;
    })
    this.planningService.getPrognosisYears().subscribe( years => {
      this.prognosisYears = years;
    })
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
    dialogRef.componentInstance.confirmed.subscribe(() => {  });
  }

  updatePlaces(): void {
    if (!this.activeInfrastructure || this.activeInfrastructure.services.length === 0) return;
    this.planningService.getPlaces(this.activeInfrastructure.id,
      { targetProjection: this.mapControl!.map!.mapProjection }).subscribe(places => {
      this.places = places;
      let showLabel = true;
      if (this.placesLayer){
        showLabel = !!this.placesLayer.showLabel;
        this.mapControl?.removeLayer(this.placesLayer.id!);
      }
      if (!this.activeService) this.activeService = this.activeInfrastructure!.services[0];
      this.planningService.getCapacities(this.year!, this.activeService.id).subscribe(capacities => {
        this.capacities = capacities;
        let displayedPlaces: Place[] = [];
        this.places?.forEach(place => {
          const capacity = this.getCapacity(this.activeService!.id, place.id);
          if (!capacity) return;
          place.properties.capacity = capacity;
          place.properties.label = this.getFormattedCapacityString([this.activeService!.id], capacity);
          displayedPlaces.push(place);
        })
        const radiusFunc = d3.scaleLinear().domain(
          [this.activeService?.minCapacity || 0, this.activeService?.maxCapacity || 1000]
        ).range([1, 20]);
        this.placesLayer = this.mapControl?.addLayer({
          order: 0,
          type: 'vector',
          group: this.legendGroup?.id,
          name: this.activeInfrastructure!.name,
          description: this.activeInfrastructure!.name,
          opacity: 1,
          symbol: {
            fillColor: '#2171b5',
            strokeColor: 'black',
            symbol: 'circle'
          },
          labelField: 'label',
          showLabel: showLabel
        },
        {
          visible: true,
          tooltipField: 'name',
          selectable: true,
          select: {
            fillColor: 'yellow',
            multi: true
          },
          mouseOver: {
            cursor: 'help'
          },
          radiusFunc: radiusFunc,
          valueField: 'capacity'
        });
        this.mapControl?.clearFeatures(this.placesLayer!.id!);
        this.mapControl?.addFeatures(this.placesLayer!.id!, displayedPlaces,
          { properties: 'properties', geometry: 'geometry' });
        this.placesLayer?.featureSelected?.subscribe(evt => {
          if (evt.selected)
            this.selectPlace(evt.feature.get('id'));
          else
            this.deselectPlace(evt.feature.get('id'));
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
      this.mapControl?.deselectAllFeatures(this.placesLayer!.id!);
    })
  }

  ngOnDestroy(): void {
    if (this.legendGroup) {
      this.mapControl?.removeGroup(this.legendGroup.id!);
    }
  }
}
