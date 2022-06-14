import { AfterViewInit, Component, OnDestroy, TemplateRef, ViewChild } from '@angular/core';
import { ConfirmDialogComponent } from "../../../dialogs/confirm-dialog/confirm-dialog.component";
import { MatDialog } from "@angular/material/dialog";
import { CookieService } from "../../../helpers/cookies.service";
import { PlanningService } from "../planning.service";
import {
  Infrastructure,
  Layer,
  LayerGroup,
  Place,
  PlanningProcess,
  RasterCell,
  Service, TransportMode
} from "../../../rest-interfaces";
import { MapControl, MapService } from "../../../map/map.service";
import { Subscription } from "rxjs";
import * as d3 from "d3";
import { FilterColumn } from "../../../elements/filter-table/filter-table.component";

@Component({
  selector: 'app-reachabilities',
  templateUrl: './reachabilities.component.html',
  styleUrls: ['./reachabilities.component.scss']
})
export class ReachabilitiesComponent implements AfterViewInit, OnDestroy {
  @ViewChild('filterTemplate') filterTemplate!: TemplateRef<any>;
  selectMode = false;
  rasterCells: RasterCell[] = [];
  mode: TransportMode = TransportMode.WALK;
  indicator = 'option 1';
  selectPlaceMode = false;
  selectCellMode = false;
  infrastructures?: Infrastructure[];
  places?: Place[];
  selectedInfrastructure?: Infrastructure;
  selectedService?: Service;
  activeProcess?: PlanningProcess;
  mapControl?: MapControl;
  legendGroup?: LayerGroup;
  baseRasterLayer?: Layer;
  reachRasterLayer?: Layer;
  subscriptions: Subscription[] = [];
  placesLayer?: Layer;
  placeReachabilityLayer?: Layer;
  TransportMode = TransportMode;

  constructor(private mapService: MapService, private dialog: MatDialog, public cookies: CookieService,
              public planningService: PlanningService) { }

  ngAfterViewInit(): void {
    this.mapControl = this.mapService.get('planning-map');
    this.legendGroup = this.mapControl.addGroup({
      name: 'Erreichbarkeiten',
      order: -1
    }, true);
    this.planningService.getInfrastructures().subscribe(infrastructures => {
      this.infrastructures = infrastructures;
      this.applyUserSettings();
      this.planningService.getRasterCells().subscribe(rasterCells => {
        this.rasterCells = rasterCells;
        this.drawRaster();
      });
    });
    this.subscriptions.push(this.planningService.activeProcess$.subscribe(process => {
      this.activeProcess = process;
    }));
  }

  applyUserSettings(): void {
    this.selectedInfrastructure = this.infrastructures?.find(i => i.id === this.cookies.get('planning-infrastructure', 'number'));
    this.selectedService = this.selectedInfrastructure?.services.find(i => i.id === this.cookies.get('planning-service', 'number'));
    this.updatePlaces();
  }

  drawRaster(): void {
    this.baseRasterLayer = this.mapControl?.addLayer({
        order: 0,
        type: 'vector',
        group: this.legendGroup?.id,
        name: 'Rasterzellen',
        description: 'Zensus-Raster (LAEA)',
        opacity: 1,
        symbol: {
          fillColor: 'rgba(0, 0, 0, 0)',
          strokeColor: 'black',
          symbol: 'line'
        },
        labelField: 'label',
        showLabel: false
      },
      {
        visible: true,
        strokeWidth: 1
      });
    this.mapControl?.clearFeatures(this.baseRasterLayer!.id!);
    this.mapControl?.addFeatures(this.baseRasterLayer!.id!, this.rasterCells,
      { properties: 'properties', geometry: 'geometry' });
  }

  onInfrastructureChange(): void {
    this.cookies.set('planning-infrastructure', this.selectedInfrastructure?.id);
    if (this.selectedInfrastructure!.services.length > 0)
      this.selectedService = this.selectedInfrastructure!.services[0];
    this.updatePlaces();
  }

  onServiceChange(): void {
    this.cookies.set('planning-service', this.selectedService?.id);
    this.updatePlaces();
  }

  updatePlaces(): void {
    if (!this.selectedInfrastructure || !this.selectedService) return;
    this.updateMapDescription();
    this.planningService.getPlaces(this.selectedInfrastructure.id,
      { targetProjection: this.mapControl!.map!.mapProjection }).subscribe(places => {
      this.places = places;
      let showLabel = true;
      if (this.placesLayer){
        showLabel = !!this.placesLayer.showLabel;
        this.mapControl?.removeLayer(this.placesLayer.id!);
      }
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
          showLabel: showLabel
        },
        {
          visible: true,
          tooltipField: 'name',
          selectable: true,
          mouseOver: {
            cursor: ''
          },
          select: {
            fillColor: 'yellow',
            multi: false
          },
        });
      this.mapControl?.clearFeatures(this.placesLayer!.id!);
      this.mapControl?.addFeatures(this.placesLayer!.id!, places,
        { properties: 'properties', geometry: 'geometry' });
      this.mapControl?.setSelect(this.placesLayer!.id!, this.selectPlaceMode);
      this.placesLayer?.featureSelected?.subscribe(evt => {
        if (evt.selected)
          this.showPlaceReachability(evt.feature.get('id'));
        else
          this.removePlaceReachability();
      })
    })
  }

  onFilter(): void {

  }

  updateMapDescription(): void {

  }

  showPlaceReachability(placeId: number): void {
    if (!this.rasterCells) return;
    this.planningService.getPlaceReachability(placeId, this.mode).subscribe(cellResults => {
      if(this.reachRasterLayer) this.mapControl?.removeLayer(this.reachRasterLayer.id!);
      let features: RasterCell[] = [];
      cellResults.forEach(cellResult => {
        const cell = this.rasterCells.find(c => c.properties.cellcode === cellResult.cellCode);
        if (cell) {
          cell.properties.value = Math.round(cellResult.value * 100) / 100;
          features.push(cell);
        }
      })
      const max = Math.max(...cellResults.map(c => c.value));

      const colorFunc = d3.scaleSequential(d3.interpolateRdYlGn).domain([max, 0]);

      this.reachRasterLayer = this.mapControl?.addLayer({
          order: 0,
          type: 'vector',
          group: this.legendGroup?.id,
          name: 'Erreichbarkeiten',
          description: 'Ergebnisse',
          opacity: 1,
          symbol: {
            fillColor: 'rgba(0, 0, 0, 0)',
            strokeColor: 'black',
            symbol: 'line'
          },
          labelField: 'value',
          showLabel: false
        },
        {
          visible: true,
          strokeWidth: 1,
          colorFunc: colorFunc
        });
      this.mapControl?.clearFeatures(this.reachRasterLayer!.id!);
      this.mapControl?.addFeatures(this.reachRasterLayer!.id!, features,
        { properties: 'properties', geometry: 'geometry' });
    })
  }

  removePlaceReachability(): void {

  }

  toggleIndicator(): void {
    this.selectPlaceMode = false;
    this.selectCellMode = false;
  }

  togglePlaceSelection(): void {
    this.selectPlaceMode = !this.selectPlaceMode;
    this.mapControl?.map?.setCursor(this.selectPlaceMode? 'crosshair': '');
    this.mapControl?.setSelect(this.placesLayer?.id!, this.selectPlaceMode);
  }

  ngOnDestroy(): void {
    if (this.legendGroup) {
      this.mapControl?.removeGroup(this.legendGroup.id!);
    }
    this.subscriptions.forEach(subscription => subscription.unsubscribe());
  }
}
