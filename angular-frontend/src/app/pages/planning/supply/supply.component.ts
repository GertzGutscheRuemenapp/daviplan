import { Component, AfterViewInit, TemplateRef, ViewChild } from '@angular/core';
import { ConfirmDialogComponent } from "../../../dialogs/confirm-dialog/confirm-dialog.component";
import { MatDialog, MatDialogRef } from "@angular/material/dialog";
import { CookieService } from "../../../helpers/cookies.service";
import { PlanningService } from "../planning.service";
import { Infrastructure, Layer, LayerGroup, Place, Service, Capacity } from "../../../rest-interfaces";
import { MapControl, MapService } from "../../../map/map.service";
import { FloatingDialog } from "../../../dialogs/help-dialog/help-dialog.component";
import { forkJoin, Observable } from "rxjs";
import { tap } from "rxjs/operators";
import * as d3 from "d3";

@Component({
  selector: 'app-supply',
  templateUrl: './supply.component.html',
  styleUrls: ['./supply.component.scss']
})
export class SupplyComponent implements AfterViewInit{
  @ViewChild('filterTemplate') filterTemplate!: TemplateRef<any>;
  @ViewChild('placePreviewTemplate') placePreviewTemplate!: TemplateRef<any>;
  addPlaceMode = false;
  year?: number;
  realYears?: number[];
  prognosisYears?: number[];
  compareSupply = true;
  compareStatus = 'option 1';
  infrastructures?: Infrastructure[];
  selectedInfrastructure?: Infrastructure;
  showScenarioMenu: any = false;
  mapControl?: MapControl;
  legendGroup?: LayerGroup;
  placesLayer?: Layer;
  places?: Place[];
  capacities: Record<number, Capacity[]> = {};
  selectedPlaces: Place[] = [];
  placeDialogRef?: MatDialogRef<any>;
  Object = Object;
  serviceCheckMap: Record<number, boolean> = {};

  constructor(private dialog: MatDialog, private cookies: CookieService, private mapService: MapService,
              private planningService: PlanningService) {
    this.planningService.infrastructures$.subscribe(infrastructures => {
      this.infrastructures = infrastructures;
    })
  }

  ngAfterViewInit(): void {
    this.mapControl = this.mapService.get('planning-map');
    this.showScenarioMenu = this.cookies.get('exp-planning-scenario');

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
      this.updateCapacities();
    })
    this.planningService.realYears$.subscribe( years => {
      this.realYears = years;
    })
    this.planningService.prognosisYears$.subscribe( years => {
      this.prognosisYears = years;
    })
  }

  onFilter(): void {
    let dialogRef = this.dialog.open(ConfirmDialogComponent, {
      panelClass: 'absolute',
      width: '1400px',
      disableClose: false,
      data: {
        // title: 'Standortfilter',
        template: this.filterTemplate,
        closeOnConfirm: true,
        infoText: '<p>Mit dem Schieberegler rechts oben können Sie das Jahr wählen für das die Standortstruktur in der Tabelle angezeigt werden soll. Die Einstellung wird für die Default-Kartendarstellung übernommen.</p>' +
          '<p>Mit einem Klick auf das Filtersymbol in der Tabelle können Sie Filter auf die in der jeweiligen Spalte Indikatoren definieren. Die Filter werden grundsätzlich auf alle Jahre angewendet. In der Karte werden nur die gefilterten Standorte angezeigt.</p>'+
          '<p>Sie können einmal gesetzte Filter bei Bedarf im Feld „Aktuell verwendete Filter“ unter der Tabelle wieder löschen.</p>'
      }
    });
    dialogRef.afterClosed().subscribe((ok: boolean) => {  });
    dialogRef.componentInstance.confirmed.subscribe(() => {  });
  }

  updateServices(): void {
    this.serviceCheckMap = {};
    if (!this.selectedInfrastructure) return;
    this.selectedInfrastructure.services.forEach(service => {
      this.serviceCheckMap[service.id] = false;
    })
  }

  updatePlaces(): void {
    if (!this.selectedInfrastructure) return;
    this.planningService.getPlaces(this.selectedInfrastructure.id).subscribe(places => {
      if (this.placesLayer)
        this.mapControl?.removeLayer(this.placesLayer.id!)
      const checkedServices = this.selectedInfrastructure?.services.filter(service => this.serviceCheckMap[service.id]) || [];
      const maxCap = checkedServices.reduce((sum, service) => sum + service.maxCapacity, 0);
      if (!this.year || checkedServices.length === 0) {
        places?.forEach(place => {
          place.properties.capacity = 0;
          place.properties.label = '';
        })
      }
      const colorFunc = d3.scaleSequential().domain([0, maxCap || 1000])
        .interpolator(d3.interpolateCool);
      this.placesLayer = this.mapControl?.addLayer({
          order: 0,
          type: 'vector',
          group: this.legendGroup?.id,
          name: this.selectedInfrastructure!.name,
          description: this.selectedInfrastructure!.name,
          opacity: 1,
          symbol: {
            fillColor: colorFunc(0),
            strokeColor: 'black',
            symbol: 'circle'
          },
          labelField: 'label'
        },
        {
          visible: true,
          tooltipField: 'name',
          selectable: true,
          select: {
            fillColor: 'yellow'
          },
          mouseOver: {
            cursor: 'help'
          },
          colorFunc: colorFunc,
          valueField: 'capacity'
        });
      this.places = places;
      this.mapControl?.clearFeatures(this.placesLayer!.id!);
      this.mapControl?.addWKTFeatures(this.placesLayer!.id!, this.places!, true);
      this.placesLayer?.featureSelected?.subscribe(evt => {
        if (evt.selected)
          this.selectPlace(evt.feature.get('id'));
        else
          this.deselectPlace(evt.feature.get('id'));
      })
    })
  }

  updateCapacities(): void {
    const checkedServices = Object.keys(this.serviceCheckMap).filter((serviceId: string) => this.serviceCheckMap[Number(serviceId)]);
    if (!this.places) return;
    const observables: Observable<Capacity[]>[] = [];
    checkedServices.forEach(serviceId => {
      const query = this.planningService.getCapacities(this.year!, Number(serviceId));
      query.subscribe(capacities => {
        this.capacities[Number(serviceId)] = capacities;
      })
      observables.push(query);
    })
    forkJoin(...observables).subscribe((merged: Array<LayerGroup[]>) => {
      this.places?.forEach(place => {
        let summedCapacity = 0;
        checkedServices.forEach(serviceId => {
          summedCapacity += this.getCapacity(Number(serviceId), place.id);
        })
        place.properties.capacity = summedCapacity;
        place.properties.label = this.getFormattedCapacityString(checkedServices.map(id => Number(id)), summedCapacity);
      })
      this.updatePlaces();
    })
  }

  getFormattedCapacityString(services: number[], capacity: number): string {
    if (!this.selectedInfrastructure) return '';
    let units = new Set<string>();
    this.selectedInfrastructure.services.filter(service => services.indexOf(service.id) >= 0).forEach(service => {
      units.add((capacity === 1)? service.capacitySingularUnit: service.capacityPluralUnit);
    })
    return `${capacity} ${Array.from(units).join('/')}`
  }

  getCapacity(serviceId: number, placeId: number): number{
    const cap = this.capacities[serviceId].find(capacity => capacity.place === placeId);
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
  }
}
