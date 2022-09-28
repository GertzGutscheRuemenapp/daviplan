import { AfterViewInit, Component, OnDestroy, TemplateRef, ViewChild } from '@angular/core';
import { CookieService } from "../../../helpers/cookies.service";
import { environment } from "../../../../environments/environment";
import { MatDialog } from "@angular/material/dialog";
import { SimpleDialogComponent } from "../../../dialogs/simple-dialog/simple-dialog.component";
import { PlanningService } from "../planning.service";
import {
  Area,
  AreaIndicatorResult,
  AreaLevel,
  Indicator,
  Infrastructure, Place, PlaceIndicatorResult,
  PlanningProcess, RasterCell, RasterIndicatorResult, Scenario,
  Service,
  TransportMode
} from "../../../rest-interfaces";
import { MapControl, MapService } from "../../../map/map.service";
import * as d3 from "d3";
import { Subscription } from "rxjs";
import { MapLayerGroup, VectorLayer, VectorTileLayer } from "../../../map/layers";
import { modes } from "../mode-select/mode-select.component";

@Component({
  selector: 'app-rating',
  templateUrl: './rating.component.html',
  styleUrls: ['./rating.component.scss']
})
export class RatingComponent implements AfterViewInit, OnDestroy {
  @ViewChild('diagramDialog') diagramDialogTemplate!: TemplateRef<any>;
  backend: string = environment.backend;
  compareSupply = true;
  compareStatus = 'option 1';
  indicators: Indicator[] = [];
  areaLevels: AreaLevel[] = [];
  infrastructures: Infrastructure[] = [];
  activeService?: Service;
  selectedIndicator?: Indicator;
  selectedAreaLevel?: AreaLevel;
  activeScenario?: Scenario;
  showLabel = true;
  mapControl?: MapControl;
  indicatorLayer?: VectorLayer;
  layerGroup?: MapLayerGroup;
  year?: number;
  subscriptions: Subscription[] = [];
  indicatorParams: any = {mode: TransportMode.WALK};

  constructor(private dialog: MatDialog, public cookies: CookieService,
              public planningService: PlanningService, private mapService: MapService) {}

  ngAfterViewInit(): void {
    this.mapControl = this.mapService.get('planning-map');
    this.layerGroup = new MapLayerGroup('Bewertung', { order: -1 })
    this.mapControl.addGroup(this.layerGroup);
    try {
      this.indicatorParams = Object.assign(this.indicatorParams, this.cookies.get('planning-rating-params', 'json'));
    } catch {};
    this.planningService.getAreaLevels({ active: true }).subscribe(areaLevels => {
      this.areaLevels = areaLevels;
      this.planningService.getInfrastructures().subscribe(infrastructures => {
        this.infrastructures = infrastructures;
        this.applyUserSettings();
        this.subscriptions.push(this.planningService.year$.subscribe(year => {
          this.year = year;
          this.updateMap();
        }));
        this.subscriptions.push(this.planningService.activeService$.subscribe(service => {
          this.activeService = service;
          this.onServiceChange();
        }));
        this.subscriptions.push(this.planningService.activeScenario$.subscribe(scenario => {
          this.activeScenario = scenario;
          this.updateMap();
        }));
      });
    })
  }

  applyUserSettings(): void {
    this.selectedAreaLevel = this.areaLevels.find(al => al.id === this.cookies.get('planning-area-level', 'number')) || ((this.areaLevels.length > 0)? this.areaLevels[this.areaLevels.length - 1]: undefined);
/*    this.onServiceChange();
    this.onAreaLevelChange();*/
  }

  onAreaLevelChange(): void {
    if(!this.selectedAreaLevel) return;
    this.cookies.set('planning-area-level', this.selectedAreaLevel?.id);
    this.updateMap();
  }

  onServiceChange(): void {
    if (!this.activeService) {
      this.indicators = [];
      this.selectedIndicator = undefined;
      return;
    }
    this.planningService.getIndicators(this.activeService.id).subscribe(indicators => {
      this.indicators = indicators;
      this.selectedIndicator = indicators?.find(i => i.name === this.cookies.get('planning-indicator', 'string'));
      this.updateMap();
    })
  }

  updateMap(): void {
    this.showLabel = (this.indicatorLayer?.showLabel !== undefined)? this.indicatorLayer.showLabel: true;
    this.layerGroup?.clear();
    this.updateMapDescription();
    if(!this.activeScenario || !this.activeService) return;
    switch (this.selectedIndicator?.resultType) {
      case 'area':
        this.renderAreaIndicator();
        break;
      case 'place':
        this.renderPlaceIndicator();
        break;
      case 'raster':
        this.renderRasterIndicator();
        break;
      default:
    }
  }

  renderRasterIndicator(): void {
    const scenarioId = this.planningService.activeScenario?.isBase ? undefined : this.planningService.activeScenario?.id;
    let max = 0;
    let min = Number.MAX_VALUE;
    let params = { year: this.year!, scenario: scenarioId, additionalParams: this.getAdditionalParams() };
    this.planningService.computeIndicator<RasterIndicatorResult>(this.selectedIndicator!.name, this.activeService!.id, params
      ).subscribe(cellResults => {
      let values: Record<string, number> = {};
      cellResults.forEach(cellResult => {
        values[cellResult.cellCode] = Math.round(cellResult.value);
        max = Math.max(max, cellResult.value);
        min = Math.min(min, cellResult.value);
      })

      const url = `${environment.backend}/tiles/raster/{z}/{x}/{y}/`;
      this.indicatorLayer = new VectorTileLayer( this.selectedIndicator!.title, url,{
        order: 0,
        opacity: 1,
        style: {
          fillColor: 'grey',
          strokeColor: 'rgba(0, 0, 0, 0)',
          symbol: 'line'
        },
        labelField: 'value',
        showLabel: this.showLabel,
        valueStyles: {
          field: 'value',
          fillColor: {
            interpolation: {
              range: d3.interpolatePurples,
              scale: 'sequential',
              steps: 5
            }
          },
          min: Math.max(min, 0),
          max: max || 1
        },
        valueMap: {
          field: 'cellcode',
          values: values
        },
        unit: 'Minuten'
      });
      this.layerGroup?.addLayer(this.indicatorLayer);
    })
  }

  renderPlaceIndicator(): void {
    if (!this.year || !this.selectedIndicator || !this.activeService) return;
    const scenarioId = this.planningService.activeScenario?.isBase ? undefined : this.planningService.activeScenario?.id;
    let params = { year: this.year!, scenario: scenarioId, additionalParams: this.getAdditionalParams() };
    this.planningService.getPlaces().subscribe(places => {
      this.planningService.computeIndicator<PlaceIndicatorResult>(this.selectedIndicator!.name, this.activeService!.id, params).subscribe(results => {
        // ToDo description with filter
        let max = 0;
        let min = Number.MAX_VALUE;
        let displayedPlaces: any[] = [];
        results.forEach(result => {
          const place = places.find(p => p.id == result.placeId);
          if (!place) return;
          displayedPlaces.push({
            id: place.id,
            geometry: place.geom,
            properties: { name: place.name, label: place.label, value: result.value, scenario: place.scenario }
          });
          max = Math.max(max, result.value);
          min = Math.min(min, result.value);
        })
        this.indicatorLayer = new VectorLayer(this.selectedIndicator!.title, {
          order: 0,
          // description: desc,
          opacity: 1,
          style: {
            fillColor: '#2171b5',
            strokeWidth: 2,
            strokeColor: 'black',
            symbol: 'circle'
          },
          radius: 7,
          labelField: 'value',
          showLabel: this.showLabel,
          tooltipField: 'value',
          select: {
            enabled: true,
            style: {
              strokeWidth: 2,
              fillColor: 'yellow',
            },
            multi: false
          },
          mouseOver: {
            enabled: true,
            cursor: 'pointer'
          },
          valueStyles: {
            field: 'value',
            fillColor: {
              interpolation: {
                range: d3.interpolatePurples,
                scale: 'sequential',
                steps: 5
              }
            },
            min: Math.max(min, 0),
            max: max || 1
          },
          labelOffset: { y: 15 }
        });
        this.layerGroup?.addLayer(this.indicatorLayer);
        this.indicatorLayer.addFeatures(displayedPlaces);
      });
    });
  }

  renderAreaIndicator(): void {
    if (!this.year || !this.selectedAreaLevel || !this.selectedIndicator || !this.activeService || !this.selectedAreaLevel) return;
    const scenarioId = this.planningService.activeScenario?.isBase ? undefined : this.planningService.activeScenario?.id;
    let params = { year: this.year!, scenario: scenarioId, areaLevelId: this.selectedAreaLevel.id, additionalParams: this.getAdditionalParams() };
    this.planningService.getAreas(this.selectedAreaLevel!.id).subscribe(areas => {
      this.planningService.computeIndicator<AreaIndicatorResult>(this.selectedIndicator!.name, this.activeService!.id, params).subscribe(results => {
        let max = 0;
        let min = Number.MAX_VALUE;
        areas.forEach(area => {
          const data = results.find(d => d.areaId == area.id);
          const value = (data && data.value)? data.value: 0;
          max = Math.max(max, value);
          min = Math.min(min, value);
          area.properties.value = value;
          area.properties.description = `<b>${area.properties.label}</b><br>${this.selectedIndicator!.title}: ${area.properties.value}`
        })
        this.indicatorLayer = new VectorLayer(`${this.selectedIndicator!.title} (${this.selectedAreaLevel!.name})`, {
          order: 0,
          description: this.selectedIndicator!.description,
          opacity: 1,
          style: {
            strokeColor: 'white',
            fillColor: 'rgba(165, 15, 21, 0.9)',
            symbol: 'line'
          },
          labelField: 'value',
          showLabel: this.showLabel,
          tooltipField: 'description',
          mouseOver: {
            enabled: true,
            style: {
              strokeColor: 'yellow',
              fillColor: 'rgba(255, 255, 0, 0.7)'
            }
          },
          valueStyles: {
            field: 'value',
            fillColor: {
              interpolation: {
                range: d3.interpolatePurples,
                scale: 'sequential',
                steps: 5
              }
            },
            min: min,
            max: max || 1
          },
        });
        this.layerGroup?.addLayer(this.indicatorLayer);
        this.indicatorLayer.addFeatures(areas,{ properties: 'properties' });
      })
    })
  }

  getAdditionalParams(): Record<string, any> {
    let params: Record<string, any> = {};
    if (!this.selectedIndicator || !this.selectedIndicator.additionalParameters) return params;
    this.selectedIndicator.additionalParameters.forEach(indicatorParam => {
      params[indicatorParam.name] = this.indicatorParams[indicatorParam.name];
    })
    return params;
  }

  setParam(param: string, value: any): void {
    this.indicatorParams[param] = value;
    this.cookies.set('planning-rating-params', this.indicatorParams);
    this.updateMap();
  }

  onIndicatorChange(): void {
    this.cookies.set('planning-indicator', this.selectedIndicator?.name);
/*    this.selectedIndicator?.additionalParameters?.forEach(indicatorParam => {
      this.indicatorParams[indicatorParam.name] = ;
    })*/
    this.updateMap();
  }

  updateMapDescription(): void {
    const desc = `${this.planningService.activeScenario?.name}<br>
                  ${this.selectedIndicator?.title} für Leistung "${this.activeService?.name}"<br>
                  <b>${this.selectedIndicator?.description}</b>`
    this.mapControl?.setDescription(desc);
  }


  onFullscreenDialog(): void {
    this.dialog.open(SimpleDialogComponent, {
      autoFocus: false,
      data: {
        template: this.diagramDialogTemplate
      }
    });
  }

  ngOnDestroy(): void {
    if (this.layerGroup) {
      this.mapControl?.removeGroup(this.layerGroup);
    }
    this.subscriptions.forEach(subscription => subscription.unsubscribe());
  }
}
