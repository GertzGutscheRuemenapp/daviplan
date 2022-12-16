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
  Infrastructure, PlaceIndicatorResult,
  RasterIndicatorResult, Scenario,
  Service,
  TransportMode
} from "../../../rest-interfaces";
import { MapControl, MapLayerGroup, MapService } from "../../../map/map.service";
import * as d3 from "d3";
import { Subscription } from "rxjs";
import { MapLayer, TileLayer, ValueStyle, VectorLayer, VectorTileLayer } from "../../../map/layers";
import {
  BarChartData,
  HorizontalBarchartComponent
} from "../../../diagrams/horizontal-barchart/horizontal-barchart.component";
import { sortBy } from "../../../helpers/utils";
import { saveSvgAsPng } from "save-svg-as-png";
import { modes } from "../mode-select/mode-select.component";

@Component({
  selector: 'app-rating',
  templateUrl: './rating.component.html',
  styleUrls: ['./rating.component.scss']
})
export class RatingComponent implements AfterViewInit, OnDestroy {
  @ViewChild('diagramDialog') diagramDialogTemplate!: TemplateRef<any>;
  @ViewChild('barChart') barChart!: HorizontalBarchartComponent;
  barChartProps: {
    title: string,
    subtitle: string,
    unit: string,
    data: BarChartData[]
  } = { title: '', subtitle: '', data: [], unit: ''};
  backend: string = environment.backend;
  chartData: BarChartData[] = [];
  indicators: Indicator[] = [];
  areaLevels: AreaLevel[] = [];
  infrastructures: Infrastructure[] = [];
  activeService?: Service;
  selectedIndicator?: Indicator;
  selectedAreaLevel?: AreaLevel;
  activeScenario?: Scenario;
  mapControl?: MapControl;
  indicatorLayer?: MapLayer;
  layerGroup?: MapLayerGroup;
  year?: number;
  subscriptions: Subscription[] = [];
  indicatorParams: any = {mode: TransportMode.WALK};

  constructor(private dialog: MatDialog, public cookies: CookieService,
              public planningService: PlanningService, private mapService: MapService) {}

  ngAfterViewInit(): void {
    this.mapControl = this.mapService.get('planning-map');
    this.layerGroup = this.mapControl.addGroup('Bewertung', { order: -1 });
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
    this.layerGroup?.clear();
    this.barChart.clear();
    this.mapControl?.setDescription('');
    if(!this.activeScenario || !this.activeService) return;
    switch (this.selectedIndicator?.resultType) {
      case 'area':
        this.renderAreaIndicator();
        this.updateMapDescription();
        break;
      case 'place':
        this.renderPlaceIndicator();
        this.updateMapDescription();
        break;
      case 'raster':
        this.renderRasterIndicator();
        this.updateMapDescription();
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
      cellResults.values.forEach(cellResult => {
        values[cellResult.cellCode] = cellResult.value;
        max = Math.max(max, cellResult.value);
        min = Math.min(min, cellResult.value);
      })

      let style: ValueStyle = {
        field: 'value',
        min: Math.max(min, 0),
        max: max || 1
      };

      if (cellResults.legend) {
        style.fillColor = {
          bins: cellResults.legend
        }
      }
      else {
        style.fillColor = {
          interpolation: {
            range: d3.interpolatePurples,
            scale: 'sequential',
            steps: 5
          }
        }
      }

      const url = `${environment.backend}/tiles/raster/{z}/{x}/{y}/`;
      this.indicatorLayer = this.layerGroup?.addVectorTileLayer( this.selectedIndicator!.title, url, {
        id: 'indicator',
        visible: true,
        description: `<p><b>${this.selectedIndicator!.title}</b></p><p>${this.selectedIndicator!.description}</p>`,
        order: 0,
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
        unit: this.selectedIndicator?.unit
      });
    })
  }

  renderPlaceIndicator(): void {
    if (!this.year || !this.selectedIndicator || !this.activeService) return;
    const scenario = this.activeScenario?.isBase? undefined: this.activeScenario;
    let params = { year: this.year!, scenario: scenario?.id, additionalParams: this.getAdditionalParams() };
    this.planningService.getPlaces({scenario: scenario}).subscribe(places => {
      this.planningService.computeIndicator<PlaceIndicatorResult>(this.selectedIndicator!.name, this.activeService!.id, params).subscribe(results => {
        // ToDo description with filter
        let max = 0;
        let min = Number.MAX_VALUE;
        let displayedPlaces: any[] = [];
        this.chartData = [];
        results.values.forEach(result => {
          const place = places.find(p => p.id == result.placeId);
          if (!place) return;
          const formattedValue = `${result.value} ${this.selectedIndicator?.unit}`;
          let description = `<b>${place.name}</b><br>
                            ${this.selectedIndicator!.description}: <b>${formattedValue}</b><br>
                            Jahr: ${this.year}<br>
                            Szenario: ${this.activeScenario?.name}`;
          this.selectedIndicator?.additionalParameters?.forEach(param => {
            let value = this.indicatorParams[param.name];
            if (param.name == 'mode') value = modes[value];
            description += `<br>${param.title}: ${(value != undefined)? value: '-'}`;
          })
          displayedPlaces.push({
            id: place.id,
            geometry: place.geom,
            properties: {
              name: place.name,
              label: formattedValue,
              description: description,
              value: result.value
            }
          });
          max = Math.max(max, result.value);
          min = Math.min(min, result.value);
          this.chartData.push({ label: place.name || '', value: result.value });
        })

        let style: ValueStyle = {
          field: 'value',
          min: Math.max(min, 0),
          max: max || 1
        };

        if (results.legend) {
          style.fillColor = {
            bins: results.legend
          }
        }
        else {
          style.fillColor = {
            interpolation: {
              range: d3.interpolatePurples,
              scale: 'sequential',
              steps: 5
            }
          }
        }

        this.indicatorLayer = this.layerGroup?.addVectorLayer(this.selectedIndicator!.title, {
          id: 'indicator',
          visible: true,
          order: 0,
          description: `<p><b>${this.selectedIndicator!.title}</b></p><p>${this.selectedIndicator!.description}</p>`,
          style: {
            fillColor: '#2171b5',
            strokeWidth: 2,
            strokeColor: 'black',
            symbol: 'circle'
          },
          radius: 7,
          labelField: 'label',
          tooltipField: 'description',
          valueStyles: style,
          mouseOver: {
            enabled: true,
            cursor: 'pointer'
          },
          labelOffset: { y: 15 },
          unit: this.selectedIndicator?.unit
        });
        (this.indicatorLayer as VectorLayer).addFeatures(displayedPlaces);
        this.barChartProps.unit = this.selectedIndicator?.unit || '';
        this.renderDiagram(this.chartData);
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
        this.chartData = [];
        let displayedAreas: Area[] = [];
        areas.forEach(area => {
          const data = results.values.find(d => d.areaId == area.id);
          const value = (data && data.value)? data.value: 0;
          max = Math.max(max, value);
          min = Math.min(min, value);
          const formattedValue = `${value.toLocaleString()} ${this.selectedIndicator?.unit}`;
          let description = `<b>${area.properties.label}</b><br>
                            ${this.selectedIndicator!.description}: <b>${formattedValue}</b><br>
                            Jahr: ${this.year}<br>
                            Szenario: ${this.activeScenario?.name}`;
          this.selectedIndicator?.additionalParameters?.forEach(param => {
            let value = this.indicatorParams[param.name];
            if (param.name == 'mode') value = modes[value];
            description += `<br>${param.title}: ${(value != undefined)? value: '-'}`;
          })
          // display "copies" because changes are made to the properties
          displayedAreas.push({
            id: area.id,
            geometry: area.geometry,
            properties: {
              areaLevel: area.properties.areaLevel,
              attributes: area.properties.attributes,
              value: value,
              description: description,
              label: formattedValue
            }
          })
          this.chartData.push({ label: area.properties.label, value: value });
        })
        let style: ValueStyle = {
          field: 'value',
          min: Math.max(min, 0),
          max: max || 1
        };

        if (results.legend) {
          style.fillColor = {
            bins: results.legend
          }
        }
        else {
          style.fillColor = {
            interpolation: {
              range: d3.interpolatePurples,
              scale: 'sequential',
              steps: 5
            }
          }
        }
        this.indicatorLayer = this.layerGroup?.addVectorLayer(`${this.selectedIndicator!.title} (${this.selectedAreaLevel!.name})`, {
          id: 'indicator',
          visible: true,
          order: 0,
          description: `<p><b>${this.selectedIndicator!.title}</b></p><p>${this.selectedIndicator!.description}</p>`,
          style: {
            strokeColor: 'white',
            fillColor: 'rgba(165, 15, 21, 0.9)',
            symbol: 'line'
          },
          labelField: 'label',
          tooltipField: 'description',
          mouseOver: {
            enabled: true,
            style: {
              strokeColor: 'yellow',
              fillColor: 'rgba(255, 255, 0, 0.7)'
            }
          },
          valueStyles: style,
          unit: this.selectedIndicator?.unit
        });
        (this.indicatorLayer as VectorLayer).addFeatures(displayedAreas,{ properties: 'properties' });
        this.barChartProps.unit = this.selectedIndicator?.unit || '';
        this.renderDiagram(this.chartData);
      })
    })
  }

  renderDiagram(data: BarChartData[]){
    this.barChart.draw(sortBy(data, 'value', { reverse: true }));
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
