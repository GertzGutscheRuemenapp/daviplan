import { AfterViewInit, Component, OnDestroy, OnInit } from '@angular/core';
import { CookieService } from "../../../helpers/cookies.service";
import { PlanningService } from "../planning.service";
import {
  Area,
  AreaLevel,
  Infrastructure,
  Layer,
  LayerGroup,
  PlanningProcess,
  Scenario,
  Service
} from "../../../rest-interfaces";
import * as d3 from "d3";
import { map } from "rxjs/operators";
import { forkJoin, Observable, Subscription } from "rxjs";
import { MapControl, MapService } from "../../../map/map.service";
import { SelectionModel } from "@angular/cdk/collections";

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
  activeInfrastructure?: Infrastructure;
  activeLevel?: AreaLevel;
  activeService?: Service;
  areaLevels: AreaLevel[] = [];
  areas: Area[] = [];
  activeProcess?: PlanningProcess;
  activeScenario?: Scenario;
  realYears?: number[];
  prognosisYears?: number[];
  mapControl?: MapControl;
  demandLayer?: Layer;
  legendGroup?: LayerGroup;
  serviceSelection = new SelectionModel<Service>(false);
  year?: number;
  subscriptions: Subscription[] = [];

  constructor(public cookies: CookieService, private mapService: MapService,
              public planningService: PlanningService) {}

  ngAfterViewInit(): void {
    this.mapControl = this.mapService.get('planning-map');
    this.legendGroup = this.mapControl.addGroup({
      name: 'Nachfrage',
      order: -1
    }, false)
    this.subscriptions.push(this.planningService.activeProcess$.subscribe(process => {
      this.activeProcess = process;
      this.updateMap();
    }));
    this.subscriptions.push(this.planningService.activeScenario$.subscribe(scenario => {
      this.activeScenario = scenario;
      this.updateMap();
    }));
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
    this.activeInfrastructure = this.infrastructures?.find(i => i.id === this.cookies.get('planning-infrastructure', 'number')) || ((this.infrastructures.length > 0)? this.infrastructures[0]: undefined);
    this.activeService = this.activeInfrastructure?.services.find(i => i.id === this.cookies.get('planning-service', 'number'))  || ((this.activeInfrastructure && this.activeInfrastructure.services.length > 0)? this.activeInfrastructure.services[0]: undefined);
    if (this.activeService)
      this.serviceSelection.select(this.activeService);
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

  onInfrastructureChange(): void {
    this.serviceSelection.select(this.activeInfrastructure!.services[0]);
    this.cookies.set('planning-infrastructure', this.activeInfrastructure?.id);
    this.onServiceChange();
  }

  onServiceChange(): void {
    this.activeService = this.serviceSelection.selected[0]; // always an array, even if multiple is not allowed
    this.cookies.set('planning-service', this.activeService?.id);
    this.updateMap();
  }

  updateMap(): void {
    if (this.demandLayer) {
      this.mapControl?.removeLayer(this.demandLayer.id!);
      this.demandLayer = undefined;
    }
    if (!this.year || !this.activeLevel || !this.activeService || !this.activeProcess) return;
    this.updateMapDescription();

    this.planningService.getDemand(this.activeLevel.id,
      { year: this.year!, service: this.activeService?.id }).subscribe(demandData => {
        let max = 1;
        let min = Number.MAX_VALUE;
        this.areas.forEach(area => {
          const data = demandData.find(d => d.areaId == area.id);
          const value = (data)? Math.round(data.value): 0;
          max = Math.max(max, value);
          min = Math.min(min, value);
          area.properties.value = value;
          area.properties.description = `<b>${area.properties.label}</b><br>Nachfrage: ${area.properties.value}`
        })
        max = Math.max(max, 10);
      const steps = (max < 1.2 * min)? 3: (max < 1.4 * min)? 5: (max < 1.6 * min)? 7: 9;
      const colorFunc = d3.scaleSequential(d3.interpolateBlues).domain([min, max]);
        this.demandLayer = this.mapControl?.addLayer({
            order: 0,
            type: 'vector',
            group: this.legendGroup?.id,
            name: this.activeLevel!.name,
            description: this.activeLevel!.name,
            opacity: 1,
            symbol: {
              strokeColor: 'white',
              fillColor: 'rgba(165, 15, 21, 0.9)',
              symbol: 'line'
            },
            labelField: 'value',
            showLabel: true
          },
          {
            visible: true,
            tooltipField: 'description',
            mouseOver: {
              strokeColor: 'yellow',
              fillColor: 'rgba(255, 255, 0, 0.7)'
            },
            colorFunc: colorFunc
          });
        let colors: string[] = [];
        let labels: string[] = [];
        const step = (max - min) / steps;
        Array.from({ length: steps + 1 },(v, k) => k * step).forEach((value, i) => {
          colors.push(colorFunc(value));
          labels.push(Number(value.toFixed(2)).toString());
        })
        this.demandLayer!.legend = {
          colors: colors,
          labels: labels,
          elapsed: true
        }
        this.mapControl?.addFeatures(this.demandLayer!.id!, this.areas,
          { properties: 'properties' });
    })
  }

  updateMapDescription(): void {
    const desc = `Planungsprozess: ${this.activeProcess?.name} > ${this.activeScenario?.name} | ${this.year} <br>
                  Nachfrage nach ${this.activeService?.name} auf Ebene ${this.activeLevel?.name}`
    this.mapControl!.mapDescription = desc;
  }

  ngOnDestroy(): void {
    if (this.legendGroup) {
      this.mapControl?.removeGroup(this.legendGroup.id!);
    }
    this.subscriptions.forEach(subscription => subscription.unsubscribe());
  }
}
