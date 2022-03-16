import { AfterViewInit, Component, OnDestroy, OnInit } from '@angular/core';
import { CookieService } from "../../../helpers/cookies.service";
import { PlanningService } from "../planning.service";
import { Area, AreaLevel, Infrastructure, Layer, LayerGroup, PlanningProcess, Service } from "../../../rest-interfaces";
import * as d3 from "d3";
import { map } from "rxjs/operators";
import { forkJoin, Observable } from "rxjs";
import { MapControl, MapService } from "../../../map/map.service";

@Component({
  selector: 'app-demand',
  templateUrl: './demand.component.html',
  styleUrls: ['./demand.component.scss']
})
export class DemandComponent implements AfterViewInit, OnDestroy {
  years = [2009, 2010, 2012, 2013, 2015, 2017, 2020, 2025];
  compareSupply = true;
  compareStatus = 'option 1';
  infrastructures?: Infrastructure[];
  activeInfrastructure?: Infrastructure;
  activeLevel?: AreaLevel;
  activeService?: Service;
  areaLevels: AreaLevel[] = [];
  areas: Area[] = [];
  showScenarioMenu: boolean = false;
  activeProcess?: PlanningProcess;
  realYears?: number[];
  prognosisYears?: number[];
  mapControl?: MapControl;
  demandLayer?: Layer;
  legendGroup?: LayerGroup;
  year?: number;

  constructor(public cookies: CookieService, private mapService: MapService,
              private planningService: PlanningService) {}

  ngAfterViewInit(): void {
    this.mapControl = this.mapService.get('planning-map');
    this.legendGroup = this.mapControl.addGroup({
      name: 'Nachfrage',
      order: -1
    }, false)
    this.planningService.activeProcess$.subscribe(process => {
      this.activeProcess = process;
      if (!process) this.cookies.set('exp-planning-scenario', false);
      this.showScenarioMenu = !!this.cookies.get('exp-planning-scenario');
    })
    this.initData();
  }

  initData(): void {
    let observables: Observable<any>[] = [];
    observables.push(this.planningService.getInfrastructures().pipe(map(infrastructures => {
      this.infrastructures = infrastructures;
    })))
    observables.push(this.planningService.getAreaLevels().pipe(map(areaLevels => {
      this.areaLevels = areaLevels;
    })))
    observables.push(this.planningService.getRealYears().pipe( map(years => {
      this.realYears = years;
    })))
    observables.push(this.planningService.getPrognosisYears().pipe( map(years => {
      this.prognosisYears = years;
    })))
    forkJoin(...observables).subscribe(() => {
      this.applyUserSettings();
    })
  }

  applyUserSettings(): void {
    this.updateMap();
  }

  onAreaLevelChange(): void {
    this.planningService.getAreas(this.activeLevel!.id).subscribe(areas => {
      this.areas = areas;
    })
  }

  updateMap(): void {
    if (this.demandLayer) {
      this.mapControl?.removeLayer(this.demandLayer.id!);
      this.demandLayer = undefined;
    }
    if (!this.year || !this.activeLevel || !this.activeService) return;
    this.updateMapDescription();
    this.planningService.getDemand(this.activeLevel.id,
      { year: this.year!, prognosis: undefined }).subscribe(popData => {
      const radiusFunc = d3.scaleLinear().domain([0, this.activeLevel?.maxValues!.population! || 1000]).range([5, 50]);
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
            symbol: 'circle'
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
          selectable: true,
          select: {
            strokeColor: 'rgb(180, 180, 0)',
            fillColor: 'rgba(255, 255, 0, 0.9)'
          },
          radiusFunc: radiusFunc
        });
      this.areas.forEach(area => {
        const data = popData.find(d => d.areaId == area.id);
        area.properties.value = (data)? Math.round(data.value): 0;
        area.properties.description = `<b>${area.properties.label}</b><br>Nachfrage: ${area.properties.value}`
      })
      this.mapControl?.addFeatures(this.demandLayer!.id!, this.areas,
        { properties: 'properties', geometry: 'centroid', zIndex: 'value' });
    })
  }

  updateMapDescription(): void {

  }

  ngOnDestroy(): void {
  }
}
