import { AfterViewInit, Component, OnDestroy, TemplateRef, ViewChild } from '@angular/core';
import { MatDialog } from "@angular/material/dialog";
import { CookieService } from "../../../helpers/cookies.service";
import { PlanningService } from "../planning.service";
import { environment } from "../../../../environments/environment";
import {
  CellResult,
  IndicatorLegendClass,
  Infrastructure,
  ModeStatistics,
  Place,
  Scenario,
  Service,
  TransportMode
} from "../../../rest-interfaces";
import { MapControl, MapLayerGroup, MapService } from "../../../map/map.service";
import { Observable, Subscription } from "rxjs";
import { Geometry } from "ol/geom";
import { ValueStyle, VectorLayer, VectorTileLayer } from "../../../map/layers";
import { modes } from "../mode-select/mode-select.component";

const modeColorValues = [[0,104,55],[100,188,97],[215,238,142],[254,221,141],[241,110,67],[165,0,38],[0,0,0]];
const modeColors = modeColorValues.map(c => `rgb(${c.join(',')})`);
const modeBins: Record<number, number[]> = {};
modeBins[TransportMode.WALK] = modeBins[TransportMode.BIKE] = [5, 10, 15, 20, 30, 45];
modeBins[TransportMode.CAR] = [5, 10, 15, 20, 25, 30];
modeBins[TransportMode.TRANSIT] = [10, 15, 20, 30, 45, 60];

function getIndicatorLegendClasses(mode: TransportMode): IndicatorLegendClass[]{
  const mBins = modeBins[mode];
  return modeColors.map((c, i) => {
      return { color: c, minValue: (i > 0)? mBins[i-1]: undefined, maxValue: (i < mBins.length)? mBins[i]: undefined }
  });
}

type IndicatorType = 'place' | 'cell' | 'next';

@Component({
  selector: 'app-reachabilities',
  templateUrl: './reachabilities.component.html',
  styleUrls: ['./reachabilities.component.scss']
})
export class ReachabilitiesComponent implements AfterViewInit, OnDestroy {
  @ViewChild('filterTemplate') filterTemplate!: TemplateRef<any>;
  activeMode?: TransportMode = TransportMode.WALK;
  indicator: IndicatorType = 'next';
  infrastructures: Infrastructure[] = [];
  places: Place[] = [];
  activeInfrastructure?: Infrastructure;
  activeService?: Service;
  activeScenario?: Scenario;
  mapControl?: MapControl;
  placesLayerGroup?: MapLayerGroup;
  reachLayerGroup?: MapLayerGroup;
  reachRasterLayer?: VectorTileLayer;
  private subscriptions: Subscription[] = [];
  private mapClickSub?: Subscription;
  placesLayer?: VectorLayer;
  stopsLayer?: VectorLayer;
  year?: number;
  placeReachabilityLayer?: VectorLayer;
  nextPlaceReachabilityLayer?: VectorTileLayer;
  selectedPlaceId?: number;
  pickedCoords?: number[];

  constructor(private mapService: MapService, public cookies: CookieService,
              public planningService: PlanningService) { }

  ngAfterViewInit(): void {
    this.mapControl = this.mapService.get('planning-map');
    this.placesLayerGroup = this.mapControl.addGroup('Standorte', { order: -1 });
    this.reachLayerGroup = this.mapControl.addGroup('Erreichbarkeiten', { order: -2 });
    this.applyUserSettings();
    this.planningService.getInfrastructures().subscribe(infrastructures => {
      this.infrastructures = infrastructures;
      this.updatePlaces().subscribe();
    });
    this.subscriptions.push(this.planningService.activeInfrastructure$.subscribe(infrastructure => {
      this.activeInfrastructure = infrastructure;
      this.updatePlaces().subscribe(() => this.renderReachability());
    }))
    this.subscriptions.push(this.planningService.activeService$.subscribe(service => {
      this.activeService = service;
      this.updatePlaces().subscribe(() => this.renderReachability());
    }))
    this.subscriptions.push(this.planningService.activeScenario$.subscribe(scenario => {
      this.activeScenario = scenario;
      this.updatePlaces().subscribe(() => this.renderReachability());
      // this.updateStops();
    }));
    this.subscriptions.push(this.planningService.year$.subscribe(year => {
      this.year = year;
      this.updatePlaces().subscribe(done => {
        // year is not relevant for the other indicators
        if (done && this.indicator === 'next') this.showNextPlaceReachabilities();
      });
    }));
  }

  applyUserSettings(): void {
    this.activeMode = this.cookies.get('planning-mode', 'number') || TransportMode.WALK;
    // @ts-ignore
    this.indicator = this.cookies.get('planning-reach-indicator', 'string') || 'place';
    this.onIndicatorChange();
  }

  updatePlaces(): Observable<boolean> {
    const observable = new Observable<any>(subscriber => {
      if (!this.activeInfrastructure || !this.activeService || !this.year || !this.activeScenario) {
        subscriber.next(false);
        subscriber.complete();
        return;
      };
      const scenario = this.activeScenario?.isBase? undefined: this.activeScenario
      this.planningService.getPlaces({
        targetProjection: this.mapControl!.map!.mapProjection, filter: { columnFilter: true, hasCapacity: true, year: this.year }, scenario: scenario
      }).subscribe(places => {
        this.placesLayerGroup?.clear();
        this.places = places;
        this.placesLayer = this.placesLayerGroup?.addVectorLayer(this.activeInfrastructure!.name, {
          id: 'reach-places',
          order: 1,
          zIndex: 99998,
          description: this.activeInfrastructure!.name,
          radius: 7,
          style: {
            fillColor: '#2171b5',
            strokeColor: 'black',
            symbol: 'circle'
          },
          labelField: 'name',
          tooltipField: 'name',
          mouseOver: {
            enabled: true,
            cursor: '',
            style: {
              strokeColor: 'yellow',
              fillColor: 'rgba(255, 255, 0, 0.7)'
            }
          },
          select: {
            enabled: true,
            style: { fillColor: 'yellow' },
            multi: false
          },
          labelOffset: { y: 15 }
        });
        this.placesLayer?.setSelectable(this.indicator === 'place');
        this.placesLayer?.addFeatures(places.map(place => {
          return { id: place.id, geometry: place.geom, properties: { name: `Standort: ${place.name}` } }
        }));

        this.placesLayer?.featuresSelected?.subscribe(features => {
          this.selectedPlaceId = features[0].get('id');
          this.cookies.set('reachability-place', this.selectedPlaceId);
          this.showPlaceReachability();
        })
        subscriber.next(true);
        subscriber.complete();
      })
    });
    return observable;
  }

  onFilter(): void {
    this.updatePlaces().subscribe(done => {
      if (done && this.indicator === 'next')
        this.showNextPlaceReachabilities();
    });
  }

  updateStops(): void {
    const transitVariant = this.activeScenario?.modeVariants.find(mv => mv.mode === TransportMode.TRANSIT);
    if (this.stopsLayer) {
      this.placesLayerGroup?.removeLayer(this.stopsLayer);
      this.stopsLayer = undefined;
    }
    if (!transitVariant) return;
    this.planningService.getTransitStops({ variant: transitVariant['variant'] }).subscribe(stops => {
      this.stopsLayer = this.placesLayerGroup?.addVectorLayer('Haltestellen', {
        id: 'reach-places',
        order: 1,
        zIndex: 99998,
        description: 'Haltestellen',
        radius: 7,
        style: {
          fillColor: '#c26f12',
          strokeColor: 'black',
          symbol: 'circle'
        },
        labelField: 'name',
        tooltipField: 'name',
        mouseOver: {
          enabled: true,
          cursor: '',
          style: {
            strokeColor: 'yellow',
            fillColor: 'rgba(255, 255, 0, 0.7)'
          }
        },
        labelOffset: { y: 15 }
      });
      this.stopsLayer?.addFeatures(stops.map(stop => {
        return { id: stop.id, geometry: stop.geom, properties: { name: `Haltestelle: ${stop.name}` } }
      }));;
    })
  }

  showPlaceReachability(): void {
    if (this.selectedPlaceId === undefined || !this.activeScenario || !this.activeMode) return;
    this.updateMapDescription('zur ausgewählten Einrichtung');

    this.planningService.getPlaceReachability(this.selectedPlaceId, this.activeMode, { scenario: this.activeScenario }).subscribe(cellResults => {
      this.reachLayerGroup?.clear();
      let values: Record<string, number> = {};
      cellResults.values.forEach(cellResult => {
        values[cellResult.cellCode] = Math.round(cellResult.value);
      })
      let style: ValueStyle = {};

      if (cellResults.legend) {
        style.fillColor = {
          bins: cellResults.legend
        }
      }
      else {
        style.fillColor = {
          bins: getIndicatorLegendClasses(this.activeMode!)
        };
      }
      if (this.placesLayer && this.selectedPlaceId !== undefined) {
        this.placesLayer.selectFeatures([this.selectedPlaceId],{silent: true});
      }

      const url = `${environment.backend}/tiles/raster/{z}/{x}/{y}/`;
      const place = this.places.find(p => p.id === this.selectedPlaceId);
      this.reachRasterLayer = this.reachLayerGroup?.addVectorTileLayer( `Wegezeit ${modes[this.activeMode!]}`, url,{
        id: 'reachability',
        visible: true,
        order: 0,
        description: `Erreichbarkeit des gewählten Standorts "${place?.name}" ${modes[this.activeMode!]}`,
        style: {
          fillColor: 'grey',
          strokeColor: 'rgba(0, 0, 0, 0)',
          symbol: 'line'
        },
        labelField: 'value',
        valueStyles: style,
        valueMap: {
          field: 'cellcode',
          values: values
        },
        unit: 'Minuten'
      });
    })
  }

  showCellReachability(): void {
    if (this.pickedCoords === undefined || !this.activeScenario || !this.activeMode) return;
    let indicatorDesc = 'vom gewählten Wohnstandort zu allen Einrichtungen';
    if (this.planningService.getPlaceFilters(this.activeInfrastructure).length > 0)
      indicatorDesc += ' <i class="warning">(gefiltert)</i>';
    this.updateMapDescription(indicatorDesc);
    const lat = this.pickedCoords[1];
    const lon = this.pickedCoords[0];
    this.planningService.getClosestCell(lat, lon, {targetProjection: this.mapControl?.map?.mapProjection }).subscribe(cell => {
      this.mapControl?.removeMarker();
      this.mapControl?.addMarker(cell.geom as Geometry);
      if (!this.activeScenario) return;
      this.planningService.getCellReachability(cell.cellcode, this.activeMode!, { scenario: this.activeScenario }).subscribe(placeResults => {
        this.reachLayerGroup?.clear();
        const valueBins = modeBins[this.activeMode!];
        let style: ValueStyle = {};

        if (placeResults.legend) {
          style.fillColor = {
            bins: placeResults.legend
          }
        }
        else {
          style.fillColor = {
            bins: getIndicatorLegendClasses(this.activeMode!)
          };
        }

        this.placeReachabilityLayer = this.reachLayerGroup?.addVectorLayer(this.activeInfrastructure!.name, {
          id: 'reachability',
          visible: true,
          order: 0,
          zIndex: 99999,
          description: `Erreichbarkeit der Angebote vom gesetzten Wohnstandort aus (${modes[this.activeMode!]})`,
          radius: 7,
          style: {
            fillColor: 'green',
            strokeColor: 'black',
            symbol: 'circle',
            strokeWidth: 1
          },
          labelField: 'label',
          tooltipField: 'tooltip',
          valueStyles: style,
          unit: 'Minuten',
          labelOffset: { y: 10 }
        });
        this.placeReachabilityLayer?.addFeatures(this.places.map(place => {
          const res = placeResults.values.find(p => p.placeId === place.id);
          const value = (res?.value !== undefined)? Math.round(res?.value): undefined;
          const label = (value !== undefined)? `${value} Minuten`: `nicht erreichbar innerhalb von ${valueBins[valueBins.length - 1]} Minuten`;
          return { id: place.id, geometry: place.geom, properties: {
            name: place.name, value: value,
              label: label, tooltip: `<b>${place.name}</b><br>${label}`} }
        }));
      })
    });
  }

  showNextPlaceReachabilities(): void {
    if (!this.year || !this.activeService || !this.activeScenario || !this.activeMode) return;
    const _this = this;
    let indicatorDesc = `von allen Wohnstandorten zum jeweils nächsten Angebot`;
    if (this.planningService.getPlaceFilters(this.activeInfrastructure).length > 0)
      indicatorDesc += ' <i class="warning">(gefiltert)</i>';
    this.updateMapDescription(indicatorDesc);
    if (this.places.length === 0)
      renderCells([]);
    else
      this.planningService.getNextPlaceReachability([this.activeService], this.activeMode, { scenario: this.activeScenario, year: this.year, places: this.places }).subscribe(
        res => renderCells(res.values, res.legend)
      );

    function renderCells(cellResults: CellResult[], legend?: IndicatorLegendClass[]) {
      _this.reachLayerGroup?.clear();
      let values: Record<string, number> = {};
      cellResults.forEach(cellResult => {
        values[cellResult.cellCode] = Math.round(cellResult.value);
      })
      const url = `${environment.backend}/tiles/raster/{z}/{x}/{y}/`;
      let style: ValueStyle = {};
      if (legend) {
        style.fillColor = {
          bins: legend
        }
      }
      else {
        style.fillColor = {
          bins: getIndicatorLegendClasses(_this.activeMode!)
        };
      }

      _this.nextPlaceReachabilityLayer = _this.reachLayerGroup?.addVectorTileLayer( `Wegezeit ${modes[_this.activeMode!]}`, url,{
        id: 'reachability',
        visible: true,
        order: 0,
        description: `Wegezeit von allen Wohnstandorten zum jeweils nächsten Angebot (${modes[_this.activeMode!]})`,
        style: {
          fillColor: 'grey',
          strokeColor: 'rgba(0, 0, 0, 0)',
          symbol: 'line'
        },
        labelField: 'value',
        // tooltipField: 'value',
        valueStyles: style,
        valueMap: {
          field: 'cellcode',
          values: values
        },
        unit: 'Minuten'
      });
    };
  }

  onIndicatorChange(): void {
    this.cookies.set('planning-reach-indicator', this.indicator);
    const placeSelectMode = this.indicator === 'place';
    const cellSelectMode = this.indicator === 'cell';
    this.setPlaceSelection(placeSelectMode);
    this.setMarkerPlacement(cellSelectMode);
    this.mapControl?.setCursor(placeSelectMode? 'search': cellSelectMode? 'marker': 'default');
    // this.mapControl?.setCursor(cellSelectMode? 'marker': 'default');
    this.mapControl?.removeMarker();
    this.reachLayerGroup?.clear();
    this.mapControl?.setDescription('');
    if (this.indicator === 'next')
      this.showNextPlaceReachabilities();
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

  changeMode(mode: TransportMode | undefined): void {
    this.activeMode = mode;
    this.cookies.set('planning-mode', mode);
    this.renderReachability();
  }

  renderReachability(): void {
    this.reachLayerGroup?.clear();
    if (!this.activeMode) return;
    switch (this.indicator) {
      case 'place':
        this.showPlaceReachability();
        break;
      case 'cell':
        this.showCellReachability();
        break;
      case 'next':
        this.showNextPlaceReachabilities();
        break;
      default:
        break;
    }
  }

  zoomToPlaceExtent(): void {
    this.placesLayer?.zoomTo();
  }

  updateMapDescription(indicatorDesc?: string): void {
    let desc = `${this.activeScenario?.name}<br>
                  Erreichbarkeit "${this.activeService?.name}" ${this.year}<br>`;
    if (indicatorDesc) desc += `<b>Wegezeit ${(this.activeMode !== TransportMode.WALK)? 'mit dem ': ''}${modes[this.activeMode!]} ${indicatorDesc}</b>`
    this.mapControl?.setDescription(desc);
  }

  ngOnDestroy(): void {
    this.mapClickSub?.unsubscribe();
    if (this.reachLayerGroup) this.mapControl?.removeGroup(this.reachLayerGroup);
    if (this.placesLayerGroup) this.mapControl?.removeGroup(this.placesLayerGroup);
    this.mapControl?.setCursor();
    this.mapControl?.removeMarker();
    this.subscriptions.forEach(subscription => subscription.unsubscribe());
  }
}
