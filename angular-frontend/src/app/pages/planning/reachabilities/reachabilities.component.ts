import { AfterViewInit, Component, OnDestroy, TemplateRef, ViewChild } from '@angular/core';
import { MatDialog } from "@angular/material/dialog";
import { CookieService } from "../../../helpers/cookies.service";
import { PlanningService } from "../planning.service";
import {
  Capacity,
  Infrastructure,
  Place,
  PlanningProcess,
  RasterCell, Scenario,
  Service,
  TransportMode
} from "../../../rest-interfaces";
import { MapControl, MapService } from "../../../map/map.service";
import { Subscription } from "rxjs";
import * as d3 from "d3";
import { Geometry } from "ol/geom";
import { MapLayerGroup, VectorLayer } from "../../../map/layers";

@Component({
  selector: 'app-reachabilities',
  templateUrl: './reachabilities.component.html',
  styleUrls: ['./reachabilities.component.scss']
})
export class ReachabilitiesComponent implements AfterViewInit, OnDestroy {
  @ViewChild('filterTemplate') filterTemplate!: TemplateRef<any>;
  rasterCells: RasterCell[] = [];
  mode: TransportMode = TransportMode.WALK;
  indicator = 'option 1';
  selectPlaceMode = false;
  placeMarkerMode = false;
  infrastructures: Infrastructure[] = [];
  places: Place[] = [];
  activeInfrastructure?: Infrastructure;
  activeService?: Service;
  activeScenario?: Scenario;
  activeProcess?: PlanningProcess;
  mapControl?: MapControl;
  placesLayerGroup?: MapLayerGroup;
  reachLayerGroup?: MapLayerGroup;
  baseRasterLayer?: VectorLayer;
  reachRasterLayer?: VectorLayer;
  private subscriptions: Subscription[] = [];
  private mapClickSub?: Subscription;
  placesLayer?: VectorLayer;
  capacities?: Capacity[];
  year?: number;
  placeReachabilityLayer?: VectorLayer;
  TransportMode = TransportMode;
  selectedPlaceId?: number;
  pickedCoords?: number[];

  constructor(private mapService: MapService, private dialog: MatDialog, public cookies: CookieService,
              public planningService: PlanningService) { }

  ngAfterViewInit(): void {
    this.mapControl = this.mapService.get('planning-map');
    this.placesLayerGroup = new MapLayerGroup('Standorte', { order: -1 })
    this.reachLayerGroup = new MapLayerGroup('Erreichbarkeiten', { order: -1 })
    this.mapControl.addGroup(this.placesLayerGroup);
    this.mapControl.addGroup(this.reachLayerGroup);
    this.planningService.getInfrastructures().subscribe(infrastructures => {
      this.infrastructures = infrastructures;
      this.planningService.getRasterCells().subscribe(rasterCells => {
        this.rasterCells = rasterCells;
        // this.drawRaster();
        this.applyUserSettings();
      });
    });
    this.subscriptions.push(this.planningService.activeInfrastructure$.subscribe(infrastructure => {
      this.activeInfrastructure = infrastructure;
    }))
    this.subscriptions.push(this.planningService.activeService$.subscribe(service => {
      this.activeService = service;
      this.updatePlaces();
    }))
    this.subscriptions.push(this.planningService.activeScenario$.subscribe(scenario => {
      this.activeScenario = scenario;
      this.updatePlaces();
    }));
    this.subscriptions.push(this.planningService.activeProcess$.subscribe(process => {
      this.activeProcess = process;
      this.updatePlaces();
    }));
    this.subscriptions.push(this.planningService.year$.subscribe(year => {
      this.year = year;
      this.updatePlaces();
    }));
  }

  applyUserSettings(): void {
    this.mode = this.cookies.get('planning-mode', 'number') || TransportMode.WALK;
    this.updatePlaces();
  }

  drawRaster(): void {
    this.baseRasterLayer = new VectorLayer( 'Rasterzellen', {
        order: 0,
        description: 'Zensus-Raster (LAEA)',
        opacity: 1,
        style: {
          fillColor: 'rgba(0, 0, 0, 0)',
          strokeWidth: 1,
          strokeColor: 'black',
          symbol: 'line'
        },
        labelField: 'label',
        showLabel: false
      });
    this.baseRasterLayer?.clearFeatures(this.baseRasterLayer!.id!);
    this.baseRasterLayer?.addFeatures( this.rasterCells, {
      properties: 'properties',
      geometry: 'geometry'
    });
  }

  updatePlaces(): void {
    if (!this.activeInfrastructure || !this.activeService || !this.activeProcess) return;
    this.updateMapDescription();
    this.planningService.getPlaces(this.activeInfrastructure.id,
      {
        targetProjection: this.mapControl!.map!.mapProjection, filter: { columnFilter: true, hasCapacity: true }
      }).subscribe(places => {
      this.places = places;
      this.planningService.getCapacities({ year: this.year!, service: this.activeService!.id }).subscribe(capacities => {
        let showLabel = true;
        if (this.placesLayer) {
          this.placesLayerGroup?.removeLayer(this.placesLayer);
          this.placesLayer = undefined;
        }
        this.placesLayer = new VectorLayer(this.activeInfrastructure!.name, {
          order: 0,
          description: this.activeInfrastructure!.name,
          opacity: 1,
          style: {
            fillColor: '#2171b5',
            strokeColor: 'black',
            symbol: 'circle'
          },
          labelField: 'name',
          showLabel: showLabel,
          tooltipField: 'name',
          mouseOver: {
            enabled: true,
            cursor: ''
          },
          select: {
            enabled: true,
            style: { fillColor: 'yellow' },
            multi: false
          }
        });
        this.placesLayerGroup?.addLayer(this.placesLayer);
        this.placesLayer.addFeatures(places,{ properties: 'properties', geometry: 'geometry' });
        this.placesLayer?.setSelectable(this.selectPlaceMode);
        this.placesLayer?.featureSelected?.subscribe(evt => {
          if (evt.selected) {
            this.selectedPlaceId = evt.feature.get('id');
            this.cookies.set('reachability-place', this.selectedPlaceId);
            this.showPlaceReachability();
          }
/*          else
            this.removePlaceReachability();*/
        })
/*        if (this.selectedPlaceId)
          this.placesLayer.selectFeatures([this.selectedPlaceId], { silent: false });*/
      })
    })
  }

  onFilter(): void {
    this.updatePlaces();
  }

  updateMapDescription(): void {

  }

  showPlaceReachability(): void {
    if (!this.rasterCells || this.selectedPlaceId === undefined) return;
    this.planningService.getPlaceReachability(this.selectedPlaceId, this.mode).subscribe(cellResults => {
      if (this.reachRasterLayer) {
        this.reachLayerGroup?.removeLayer(this.reachRasterLayer);
      }
      let features: RasterCell[] = [];
      cellResults.forEach(cellResult => {
        const cell = this.rasterCells.find(c => c.properties.cellcode === cellResult.cellCode);
        if (cell) {
          cell.properties.value = Math.round(cellResult.value * 100) / 100;
          features.push(cell);
        }
      })
      const max = Math.max(...cellResults.map(c => c.value));

      this.reachRasterLayer = new VectorLayer('gewählter Standort', {
        order: 0,
        description: 'Erreichbarkeit des gewählten Standorts',
        opacity: 1,
        style: {
          fillColor: 'rgba(0, 0, 0, 0)',
          strokeColor: 'rgba(0, 0, 0, 0)',
          strokeWidth: 1,
          symbol: 'square'
        },
        labelField: 'value',
        showLabel: false,
        valueMapping: {
          field: 'value',
          color: {
            range: d3.interpolateRdYlGn,
            scale: 'sequential',
            bins: 5,
            reverse: true
          },
          min: 0,
          max: max
        },
        unit: 'Minute(n)'
      });
      this.reachLayerGroup?.addLayer(this.reachRasterLayer);
      this.reachRasterLayer.addFeatures(features,{
        properties: 'properties',
        geometry: 'geometry'
      });
    })
  }

  showCellReachability(): void {
    if (!this.rasterCells || this.pickedCoords === undefined) return;
    const lat = this.pickedCoords[1];
    const lon = this.pickedCoords[0];
    this.planningService.getClosestCell(lat, lon, {targetProjection: this.mapControl?.map?.mapProjection }).subscribe(cell => {
      const marker = this.mapControl?.addMarker(cell.geometry as Geometry);
      this.planningService.getCellReachability(cell.properties.cellcode!, this.mode).subscribe(placeResults => {
        let showLabel = false;
        if (this.placeReachabilityLayer) {
          this.reachLayerGroup?.removeLayer(this.placeReachabilityLayer);
          this.placeReachabilityLayer = undefined;
        }
        this.places.forEach(place => {
          const res = placeResults.find(p => p.placeId === place.id);
          place.properties.value = res?.value || 999999999;
        })
        const max = Math.max(...placeResults.map(c => c.value), 0);
        this.placeReachabilityLayer = new VectorLayer(this.activeInfrastructure!.name, {
          order: 0,
          description: this.activeInfrastructure!.name,
          opacity: 1,
          style: {
            fillColor: 'green',
            strokeColor: 'black',
            symbol: 'circle'
          },
          labelField: 'value',
          showLabel: showLabel,
          tooltipField: 'value',
          valueMapping: {
            field: 'value',
            color: {
              range: d3.interpolateRdYlGn,
              scale: 'sequential',
              bins: 5,
              reverse: true
            },
            min: 0,
            max: max
          },
          unit: 'Minute(n)'
        });
        this.reachLayerGroup?.addLayer(this.placeReachabilityLayer);
        this.placeReachabilityLayer.addFeatures(this.places,{
          properties: 'properties',
          geometry: 'geometry'
        });
      })
    });
  }

  toggleIndicator(): void {
    this.setPlaceSelection(false);
    this.setMarkerPlacement(false);
    if (this.placesLayer)
      this.placesLayer?.clearSelection();
    this.reachLayerGroup?.clear();

  }

  setPlaceSelection(enable: boolean): void {
    this.selectPlaceMode = enable;
    this.mapControl?.map?.setCursor(enable? 'crosshair': '');
    this.placesLayer?.setSelectable(enable);
  }

  setMarkerPlacement(enable: boolean): void {
    this.placeMarkerMode = enable;
    if (this.mapClickSub) {
      this.mapClickSub.unsubscribe();
      this.mapClickSub = undefined;
    }
    if (enable) {
      this.mapClickSub = this.mapControl?.map?.mapClicked.subscribe(coords => {
        this.pickedCoords = coords;
        this.showCellReachability();
      })
    }
    this.mapControl?.map?.setCursor(enable? 'crosshair': '');
  }

  changeMode(mode: TransportMode): void {
    this.mode = mode;
    this.cookies.set('planning-mode', mode);
    this.showPlaceReachability();
    this.showCellReachability();
  }

  getCapacity(serviceId: number, placeId: number): number{
    const cap = this.capacities?.find(capacity => capacity.place === placeId);
    return cap?.capacity || 0;
  }

  ngOnDestroy(): void {
    if (this.mapClickSub) this.mapClickSub.unsubscribe();
    if (this.reachLayerGroup) this.mapControl?.removeGroup(this.reachLayerGroup);
    if (this.placesLayerGroup) this.mapControl?.removeGroup(this.placesLayerGroup);
    this.mapControl?.map?.setCursor('');
    this.mapControl?.removeMarker();
    this.subscriptions.forEach(subscription => subscription.unsubscribe());
  }
}
