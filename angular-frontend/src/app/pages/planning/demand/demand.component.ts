import { AfterViewInit, Component, OnDestroy } from '@angular/core';
import { CookieService } from "../../../helpers/cookies.service";
import { PlanningService } from "../planning.service";
import {
  Area,
  AreaLevel,
  Infrastructure,
  PlanningProcess,
  Scenario,
  Service
} from "../../../rest-interfaces";
import { map } from "rxjs/operators";
import { forkJoin, Observable, Subscription } from "rxjs";
import { MapControl, MapService } from "../../../map/map.service";
import { SelectionModel } from "@angular/cdk/collections";
import { MapLayerGroup, ValueStyle, VectorLayer } from "../../../map/layers";
import * as d3 from "d3";

@Component({
  selector: 'app-demand',
  templateUrl: './demand.component.html',
  styleUrls: ['./demand.component.scss']
})
export class DemandComponent implements AfterViewInit, OnDestroy {
  years = [2009, 2010, 2012, 2013, 2015, 2017, 2020, 2025];
  compareSupply = true;
  compareStatus = 'option 1';
  infrastructures: Infrastructure[] = [];
  activeLevel?: AreaLevel;
  areaLevels: AreaLevel[] = [];
  areas: Area[] = [];
  activeProcess?: PlanningProcess;
  realYears?: number[];
  prognosisYears?: number[];
  mapControl?: MapControl;
  demandLayer?: VectorLayer;
  layerGroup?: MapLayerGroup;
  year?: number;
  subscriptions: Subscription[] = [];

  constructor(public cookies: CookieService, private mapService: MapService,
              public planningService: PlanningService) {}

  ngAfterViewInit(): void {
    this.mapControl = this.mapService.get('planning-map');
    this.layerGroup = new MapLayerGroup('Nachfrage', { order: -1 })
    this.mapControl.addGroup(this.layerGroup);
    this.subscriptions.push(this.planningService.activeProcess$.subscribe(process => {
      this.updateMap();
    }));
    this.subscriptions.push(this.planningService.activeScenario$.subscribe(scenario => {
      this.updateMap();
    }));
    this.subscriptions.push(this.planningService.activeService$.subscribe(service => {
      this.updateMap();
    }))
    this.initData();
  }

  initData(): void {
    this.subscriptions.push(this.planningService.year$.subscribe(year => {
      this.year = year;
      this.updateMap();
    }));
    let observables: Observable<any>[] = [];
    observables.push(this.planningService.getInfrastructures().pipe(map(infrastructures => {
      this.infrastructures = infrastructures;
    })))
    observables.push(this.planningService.getAreaLevels({ active: true }).pipe(map(areaLevels => {
      this.areaLevels = areaLevels;
    })))
    observables.push(this.planningService.getRealYears().pipe(map(years => {
      this.realYears = years;
    })))
    observables.push(this.planningService.getPrognosisYears().pipe(map(years => {
      this.prognosisYears = years;
    })))
    forkJoin(...observables).subscribe(() => {
      this.applyUserSettings();
    })
  }

  applyUserSettings(): void {
    this.activeLevel = this.areaLevels.find(al => al.id === this.cookies.get('planning-area-level', 'number')) || ((this.areaLevels.length > 0)? this.areaLevels[this.areaLevels.length - 1]: undefined);
    this.onAreaLevelChange();
  }

  onAreaLevelChange(): void {
    if(!this.activeLevel) return;
    this.planningService.getAreas(this.activeLevel!.id).subscribe(areas => {
      this.areas = areas;
      this.cookies.set('planning-area-level', this.activeLevel?.id);
      this.updateMap();
    })
  }

  updateMap(): void {
/*    if (this.demandLayer) {
      this.layerGroup?.removeLayer(this.demandLayer);
      this.demandLayer = undefined;
    }*/
    this.layerGroup?.clear();
    if (!this.year || !this.activeLevel || !this.planningService.activeService || !this.planningService.activeScenario) return;
    this.updateMapDescription();
    const scenarioId = this.planningService.activeScenario?.isBase? undefined: this.planningService.activeScenario?.id;
    this.planningService.getDemand(this.activeLevel.id,
      { year: this.year!, service: this.planningService.activeService?.id, scenario: scenarioId
      }).subscribe(demandData => {
      let max = 1;
      let min = Number.MAX_VALUE;
      this.areas.forEach(area => {
        const data = demandData.values.find(d => d.areaId == area.id);
        const value = (data)? Math.round(data.value): 0;
        max = Math.max(max, value);
        min = Math.min(min, value);
        area.properties.value = value;
        const formattedValue = value? value.toLocaleString(): value;
        area.properties.description = `<b>${area.properties.label}</b>
                <br>Nachfrage nach Leistung "${this.planningService.activeService?.name}"
                <br>${formattedValue} ${this.planningService.activeService?.demandPluralUnit} im Jahr ${this.year}
                <br>im Szenario "${this.planningService.activeScenario?.name}"`
      })
      max = Math.max(max, 10);
      const steps = (max < 1.2 * min)? 3: (max < 1.4 * min)? 5: (max < 1.6 * min)? 7: 9;
      const desc = `<b>${this.planningService.activeService?.demandPluralUnit} ${this.year} nach ${this.activeLevel?.name}</b><br>
                    Minimum: ${min.toLocaleString()}<br>
                    Maximum: ${max.toLocaleString()}`;
      let style: ValueStyle = {
        field: 'value',
        min: Math.max(min, 0),
        max: max || 1
      };

      if (demandData.legend) {
        style.fillColor = {
          bins: demandData.legend
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
      this.demandLayer = new VectorLayer(this.planningService.activeService?.demandPluralUnit || 'Nachfragende',{
          order: 0,
          description: desc,
          opacity: 1,
          style: {
            strokeColor: 'white',
            fillColor: 'rgba(165, 15, 21, 0.9)',
            symbol: 'line'
          },
          labelField: 'value',
          showLabel: true,
          tooltipField: 'description',
          mouseOver: {
            enabled: true,
            style: {
              strokeColor: 'yellow',
              fillColor: 'rgba(255, 255, 0, 0.7)'
            }
          },
          valueStyles: style
        });
      this.layerGroup?.addLayer(this.demandLayer);
      this.demandLayer.addFeatures(this.areas, { properties: 'properties' });
    })
  }

  updateMapDescription(): void {
    const desc = `${this.planningService.activeScenario?.name}<br>
                  Nachfrage nach "${this.planningService.activeService?.name}"<br>
                  <b>${this.planningService.activeService?.demandPluralUnit} ${this.year} nach ${this.activeLevel?.name}</b>`
    this.mapControl?.setDescription(desc);
  }

  ngOnDestroy(): void {
    if (this.layerGroup) {
      this.layerGroup.clear();
      this.mapControl?.removeGroup(this.layerGroup);
    }
    this.subscriptions.forEach(subscription => subscription.unsubscribe());
  }
}
