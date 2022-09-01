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
  RasterCell,
  Scenario,
  Service,
  TransportMode
} from "../../../rest-interfaces";
import { MapControl, MapService } from "../../../map/map.service";
import { Subscription } from "rxjs";
import { Geometry } from "ol/geom";
import {  MapLayerGroup, VectorLayer, VectorTileLayer } from "../../../map/layers";
import { modes } from "../mode-select/mode-select.component";

const modeColorValues = [[0,104,55],[100,188,97],[215,238,142],[254,221,141],[241,110,67],[165,0,38],[0,0,0]];
const modeColors = modeColorValues.map(c => `rgb(${c.join(',')})`);
const modeBins: Record<number, number[]> = {};
modeBins[TransportMode.WALK] = modeBins[TransportMode.BIKE] = [5, 10, 15, 20, 30, 45];
modeBins[TransportMode.CAR] = [5, 10, 15, 20, 25, 30];
modeBins[TransportMode.TRANSIT] = [10, 15, 20, 30, 45, 60];

@Component({
  selector: 'app-reachabilities',
  templateUrl: './reachabilities.component.html',
  styleUrls: ['./reachabilities.component.scss']
})
export class ReachabilitiesComponent implements AfterViewInit, OnDestroy {
  @ViewChild('filterTemplate') filterTemplate!: TemplateRef<any>;
  rasterCells: RasterCell[] = [];
  activeMode: TransportMode = TransportMode.WALK;
  indicator: 'place' | 'cell' | 'all' = 'place';
  infrastructures: Infrastructure[] = [];
  places: Place[] = [];
  activeInfrastructure?: Infrastructure;
  activeService?: Service;
  activeScenario?: Scenario;
  activeProcess?: PlanningProcess;
  mapControl?: MapControl;
  placesLayerGroup?: MapLayerGroup;
  reachPlaceLayerGroup?: MapLayerGroup;
  reachCellLayerGroup?: MapLayerGroup;
  baseRasterLayer?: VectorTileLayer;
  reachRasterLayer?: VectorTileLayer;
  private subscriptions: Subscription[] = [];
  private mapClickSub?: Subscription;
  placesLayer?: VectorLayer;
  capacities?: Capacity[];
  year?: number;
  placeReachabilityLayer?: VectorLayer;
  selectedPlaceId?: number;
  pickedCoords?: number[];

  constructor(private mapService: MapService, private dialog: MatDialog, public cookies: CookieService,
              public planningService: PlanningService) { }

  ngAfterViewInit(): void {
    this.mapControl = this.mapService.get('planning-map');
    this.placesLayerGroup = new MapLayerGroup('Standorte', { order: -2 })
    this.reachPlaceLayerGroup = new MapLayerGroup('Erreichbarkeiten', { order: -1 })
    this.reachCellLayerGroup = new MapLayerGroup('Erreichbarkeiten', { order: -3 })
    this.mapControl.addGroup(this.placesLayerGroup);
    this.mapControl.addGroup(this.reachPlaceLayerGroup);
    this.mapControl.addGroup(this.reachCellLayerGroup);
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
      this.onIndicatorChange();
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
    this.activeMode = this.cookies.get('planning-mode', 'number') || TransportMode.WALK;
    // indicator is set to "place" by default
    this.setPlaceSelection(true);
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
    this.baseRasterLayer?.clearFeatures();
  }

  updatePlaces(): void {
    if (!this.activeInfrastructure || !this.activeService || !this.activeProcess) return;
    this.updateMapDescription();
    const scenarioId = this.activeScenario?.isBase? undefined: this.activeScenario?.id
    this.planningService.getPlaces(this.activeInfrastructure.id,
      {
        targetProjection: this.mapControl!.map!.mapProjection, filter: { columnFilter: true, hasCapacity: true }, scenario: scenarioId
      }).subscribe(places => {
      this.places = places;
      let showLabel = true;
      if (this.placesLayer) {
        this.placesLayerGroup?.removeLayer(this.placesLayer);
        this.placesLayer = undefined;
      }
      this.placesLayer = new VectorLayer(this.activeInfrastructure!.name, {
        order: 1,
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
          // cursor: 'pointer'
          cursor: ''
        },
        select: {
          enabled: true,
          style: { fillColor: 'yellow' },
          multi: false
        },
        labelOffset: { y: 15 }
      });
      this.placesLayerGroup?.addLayer(this.placesLayer);
      this.placesLayer.addFeatures(places.map(place => {
        return { id: place.id, geometry: place.geom, properties: { name: place.name } }
      }));
      this.placesLayer?.setSelectable(this.indicator === 'place');

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
  }

  onFilter(): void {
    this.updatePlaces();
  }

  showPlaceReachability(): void {
    if (!this.rasterCells || this.selectedPlaceId === undefined) return;
    this.updateMapDescription('zur ausgewählten Einrichtung');
    this.planningService.getPlaceReachability(this.selectedPlaceId, this.activeMode).subscribe(cellResults => {
      if (this.reachRasterLayer) {
        this.reachPlaceLayerGroup?.removeLayer(this.reachRasterLayer);
      }
      let values: Record<string, number> = {};
      cellResults.forEach(cellResult => {
        values[cellResult.cellCode] = Math.round(cellResult.value * 100) / 100;
      })

      const url = `${environment.backend}/tiles/raster/{z}/{x}/{y}/`;
      const place = this.places.find(p => p.id === this.selectedPlaceId);
      this.reachRasterLayer = new VectorTileLayer( `Wegezeit ${modes[this.activeMode]}`, url,{
        order: 0,
        description: `Erreichbarkeit des gewählten Standorts (${place?.name}) ${modes[this.activeMode]}`,
        opacity: 1,
        style: {
          fillColor: 'grey',
          strokeColor: 'rgba(0, 0, 0, 0)',
          symbol: 'line'
        },
        labelField: 'value',
        showLabel: false,
        valueStyles: {
          fillColor: {
            bins: {
              colors: modeColors,
              values: modeBins[this.activeMode]
            }
          }
        },
        valueMap: {
          field: 'cellcode',
          values: values
        },
        unit: 'Minuten'
      });
      this.reachPlaceLayerGroup?.addLayer(this.reachRasterLayer);
    })
  }

  showCellReachability(): void {
    if (!this.rasterCells || this.pickedCoords === undefined) return;
    this.updateMapDescription('vom gewählten Wohnstandort zu allen Einrichtungen');
    const lat = this.pickedCoords[1];
    const lon = this.pickedCoords[0];
    this.planningService.getClosestCell(lat, lon, {targetProjection: this.mapControl?.map?.mapProjection }).subscribe(cell => {
      this.mapControl?.removeMarker();
      this.mapControl?.addMarker(cell.geom as Geometry);
      this.planningService.getCellReachability(cell.cellcode, this.activeMode).subscribe(placeResults => {
        let showLabel = false;
        if (this.placeReachabilityLayer) {
          this.reachCellLayerGroup?.removeLayer(this.placeReachabilityLayer);
          this.placeReachabilityLayer = undefined;
        }
        this.places.forEach(place => {
          const res = placeResults.find(p => p.placeId === place.id);
          place.value = res?.value;
        })
        this.placeReachabilityLayer = new VectorLayer(this.activeInfrastructure!.name, {
          order: 0,
          description: this.activeInfrastructure!.name,
          opacity: 1,
          style: {
            fillColor: 'green',
            strokeColor: 'black',
            symbol: 'circle',
            strokeWidth: 1
          },
          labelField: 'value',
          showLabel: showLabel,
          tooltipField: 'value',
          valueStyles: {
            field: 'value',
            fillColor: {
              bins: {
                colors: modeColors,
                values: modeBins[this.activeMode]
              }
            }
          },
          unit: 'Minuten',
          labelOffset: { y: 10 }
        });
        this.reachCellLayerGroup?.addLayer(this.placeReachabilityLayer);
        this.placeReachabilityLayer.addFeatures(this.places.map(place => {
          return { id: place.id, geometry: place.geom, properties: { name: place.name, value: place.value } }
        }));
      })
    });
  }

  onIndicatorChange(): void {
    const placeSelectMode = this.indicator === 'place';
    const cellSelectMode = this.indicator === 'cell';
    this.setPlaceSelection(placeSelectMode);
    this.setMarkerPlacement(cellSelectMode);
    this.mapControl?.setCursor(placeSelectMode? 'search': cellSelectMode? 'marker': 'pointer');
    // this.mapControl?.setCursor(cellSelectMode? 'marker': 'default');
    this.mapControl?.removeMarker();
    if (this.placesLayer)
      this.placesLayer?.clearSelection();
    this.reachCellLayerGroup?.clear();
    this.reachPlaceLayerGroup?.clear();
    this.updateMapDescription();
  }

  setPlaceSelection(enable: boolean): void {
    this.placesLayer?.setSelectable(enable);
  }

  setMarkerPlacement(enable: boolean): void {
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
  }

  changeMode(mode: TransportMode): void {
    this.activeMode = mode;
    this.cookies.set('planning-mode', mode);
    switch (this.indicator) {
      case 'place':
        this.showPlaceReachability();
        break;
      case 'cell':
        this.showCellReachability();
        break;
      default:
        break;
    }
  }

  getCapacity(serviceId: number, placeId: number): number{
    const cap = this.capacities?.find(capacity => capacity.place === placeId);
    return cap?.capacity || 0;
  }

  updateMapDescription(indicatorDesc?: string): void {
    let desc = `${this.activeScenario?.name}<br>
                  Erreichbarkeit "${this.activeService?.name}"<br>`;
    if (indicatorDesc) desc += `<b>Wegzeit ${(this.activeMode !== TransportMode.WALK)? 'mit dem ': ''}${modes[this.activeMode]} ${indicatorDesc}</b>`
    this.mapControl?.setDescription(desc);
  }

  ngOnDestroy(): void {
    this.mapClickSub?.unsubscribe();
    if (this.reachPlaceLayerGroup) this.mapControl?.removeGroup(this.reachPlaceLayerGroup);
    if (this.reachCellLayerGroup) this.mapControl?.removeGroup(this.reachCellLayerGroup);
    if (this.placesLayerGroup) this.mapControl?.removeGroup(this.placesLayerGroup);
    this.mapControl?.setCursor();
    this.mapControl?.removeMarker();
    this.subscriptions.forEach(subscription => subscription.unsubscribe());
  }
}
