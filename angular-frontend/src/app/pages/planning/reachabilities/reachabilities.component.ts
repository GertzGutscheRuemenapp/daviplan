import { AfterViewInit, Component, OnDestroy, TemplateRef, ViewChild } from '@angular/core';
import { MatDialog } from "@angular/material/dialog";
import { CookieService } from "../../../helpers/cookies.service";
import { PlanningService } from "../planning.service";
import { environment } from "../../../../environments/environment";
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
import { MapLayerGroup, VectorLayer, VectorTileLayer } from "../../../map/layers";

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
  baseRasterLayer?: VectorTileLayer;
  reachRasterLayer?: VectorTileLayer;
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
      // this.drawRaster();
      this.applyUserSettings();
/*      this.planningService.getRasterCells({targetProjection: this.mapControl?.map?.mapProjection }).subscribe(rasterCells => {
        this.rasterCells = rasterCells;
      });*/
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
    const url = `${environment.backend}/tiles/raster/{z}/{x}/{y}/`;
    this.baseRasterLayer = new VectorTileLayer( 'Rasterzellen', url,{
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
    this.placesLayerGroup?.addLayer(this.baseRasterLayer);
    this.baseRasterLayer?.clearFeatures(this.baseRasterLayer!.id!);
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
      let values: Record<string, number> = {};
      cellResults.forEach(cellResult => {
        values[cellResult.cellCode] = Math.round(cellResult.value * 100) / 100;
      })
      const max = Math.max(...cellResults.map(c => c.value));

      const url = `${environment.backend}/tiles/raster/{z}/{x}/{y}/`;
      this.reachRasterLayer = new VectorTileLayer( 'gewählter Standort', url,{
        order: 0,
        description: 'Erreichbarkeit des gewählten Standorts',
        opacity: 1,
        style: {
          fillColor: 'grey',
          strokeColor: 'rgba(0, 0, 0, 0)',
          symbol: 'line'
        },
        labelField: 'label',
        showLabel: false,
        valueStyles: {
          color: {
            range: d3.interpolateRdYlGn,
            scale: 'sequential',
            bins: 5,
            reverse: true
          },
          min: 0,
          max: max
        },
        valueMap: {
          field: 'cellcode',
          values: values
        },
        unit: 'Minute(n)'
      });
      this.reachLayerGroup?.addLayer(this.reachRasterLayer);
    })
  }

  showCellReachability(): void {
    if (!this.rasterCells || this.pickedCoords === undefined) return;
    const lat = this.pickedCoords[1];
    const lon = this.pickedCoords[0];
    this.planningService.getClosestCell(lat, lon, {targetProjection: this.mapControl?.map?.mapProjection }).subscribe(cell => {
      this.mapControl?.removeMarker();
      this.mapControl?.addMarker(cell.geom as Geometry);
      this.planningService.getCellReachability(cell.cellcode, this.mode).subscribe(placeResults => {
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
          valueStyles: {
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
    this.mapControl?.removeMarker();
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
