import { AfterViewInit, Component, OnDestroy, OnInit } from '@angular/core';
import { CookieService } from "../../../helpers/cookies.service";
import { PlanningService } from "../planning.service";
import { Area, AreaLevel, Infrastructure, Layer, LayerGroup, PlanningProcess, Service } from "../../../rest-interfaces";
import * as d3 from "d3";
import { map } from "rxjs/operators";
import { forkJoin, Observable } from "rxjs";
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
  infrastructures?: Infrastructure[];
  activeInfrastructure?: Infrastructure;
  activeLevel?: AreaLevel;
  activeService?: Service;
  areaLevels: AreaLevel[] = [];
  areas: Area[] = [];
  activeProcess?: PlanningProcess;
  realYears?: number[];
  prognosisYears?: number[];
  mapControl?: MapControl;
  demandLayer?: Layer;
  legendGroup?: LayerGroup;
  serviceSelection = new SelectionModel<Service>(false);
  year?: number;

  constructor(public cookies: CookieService, private mapService: MapService,
              public planningService: PlanningService) {}

  ngAfterViewInit(): void {
    this.mapControl = this.mapService.get('planning-map');
    this.legendGroup = this.mapControl.addGroup({
      name: 'Nachfrage',
      order: -1
    }, false)
    this.planningService.activeProcess$.subscribe(process => {
      this.activeProcess = process;
    })
    this.initData();
  }

  initData(): void {
    this.planningService.year$.subscribe(year => {
      this.year = year;
      this.updateMap();
    })
    let observables: Observable<any>[] = [];
    observables.push(this.planningService.getInfrastructures().pipe(map(infrastructures => {
      this.infrastructures = infrastructures;
    })))
    observables.push(this.planningService.getAreaLevels().pipe(map(areaLevels => {
      this.areaLevels = areaLevels;
    })))
    observables.push(this.planningService.getRealYears().pipe( map(years => {
      this.realYears = years;
      this.year = this.realYears[0];
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
      this.updateMap();
    })
  }

  onInfrastructureChange(): void {
    this.serviceSelection.select(this.activeInfrastructure!.services[0]);
    this.onServiceChange();
  }

  onServiceChange(): void {
    this.activeService = this.serviceSelection.selected[0];
    this.updateMap();
  }

  updateMap(): void {
    if (this.demandLayer) {
      this.mapControl?.removeLayer(this.demandLayer.id!);
      this.demandLayer = undefined;
    }
    if (!this.year || !this.activeLevel || !this.activeService) return;
    this.updateMapDescription();

    this.planningService.getDemand(this.activeLevel.id,
      { year: this.year!, prognosis: undefined, service: this.activeService?.id }).subscribe(demandData => {
        const colorFunc = d3.scaleSequential().domain([0, 1000 || 0])
          .interpolator(d3.interpolateViridis);
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
          }
        });
      this.areas.forEach(area => {
        const data = demandData.find(d => d.areaId == area.id);
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
