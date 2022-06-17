import { AfterViewInit, Component, OnDestroy, TemplateRef, ViewChild } from '@angular/core';
import { CookieService } from "../../../helpers/cookies.service";
import { environment } from "../../../../environments/environment";
import { MatDialog } from "@angular/material/dialog";
import { SimpleDialogComponent } from "../../../dialogs/simple-dialog/simple-dialog.component";
import { PlanningService } from "../planning.service";
import {
  Area,
  AreaLevel,
  Indicator,
  Infrastructure, Layer,
  LayerGroup,
  PlanningProcess,
  RasterCell,
  Service
} from "../../../rest-interfaces";
import { RestAPI } from "../../../rest-api";
import { HttpClient } from "@angular/common/http";
import { SelectionModel } from "@angular/cdk/collections";
import { MapControl, MapService } from "../../../map/map.service";
import * as d3 from "d3";
import { Subscription } from "rxjs";

@Component({
  selector: 'app-rating',
  templateUrl: './rating.component.html',
  styleUrls: ['./rating.component.scss']
})
export class RatingComponent implements AfterViewInit, OnDestroy {
  @ViewChild('diagramDialog') diagramDialogTemplate!: TemplateRef<any>;
  backend: string = environment.backend;
  years = [2009, 2010, 2012, 2013, 2015, 2017, 2020, 2025];
  compareSupply = true;
  compareStatus = 'option 1';
  indicators: Indicator[] = [];
  areaLevels: AreaLevel[] = [];
  areas: Area[] = [];
  infrastructures?: Infrastructure[];
  selectedService?: Service;
  selectedIndicator?: Indicator;
  selectedAreaLevel?: AreaLevel;
  selectedInfrastructure?: Infrastructure;
  activeProcess?: PlanningProcess;
  mapControl?: MapControl;
  serviceSelection = new SelectionModel<Service>(false);
  indicatorLayer?: Layer;
  legendGroup?: LayerGroup;
  year?: number;
  subscriptions: Subscription[] = [];

  constructor(private dialog: MatDialog, public cookies: CookieService,
              public planningService: PlanningService, private mapService: MapService) {}

  ngAfterViewInit(): void {
    this.mapControl = this.mapService.get('planning-map');
    this.legendGroup = this.mapControl.addGroup({
      name: 'Bewertung',
      order: -1
    }, false)
    this.subscriptions.push(this.planningService.year$.subscribe(year => {
      this.year = year;
      this.updateMap();
    }));
    this.planningService.getAreaLevels({ active: true }).subscribe(areaLevels => {
      this.areaLevels = areaLevels;
      this.planningService.getInfrastructures().subscribe(infrastructures => {
        this.infrastructures = infrastructures;
        this.applyUserSettings();
      });
    })
    this.planningService.activeProcess$.subscribe(process => {
      this.activeProcess = process;
    })
  }

  applyUserSettings(): void {
    this.selectedAreaLevel = this.areaLevels.find(al => al.id === this.cookies.get('planning-area-level', 'number'));
    this.selectedInfrastructure = this.infrastructures?.find(i => i.id === this.cookies.get('planning-infrastructure', 'number'));
    this.selectedService = this.selectedInfrastructure?.services.find(i => i.id === this.cookies.get('planning-service', 'number'));
    this.onServiceChange();
    this.onAreaLevelChange();
  }

  onAreaLevelChange(): void {
    if(!this.selectedAreaLevel) return;
    this.planningService.getAreas(this.selectedAreaLevel!.id).subscribe(areas => {
      this.areas = areas;
      this.cookies.set('planning-area-level', this.selectedAreaLevel?.id);
      this.updateMap();
    })
  }

  onInfrastructureChange(): void {
    this.serviceSelection.select();
    this.cookies.set('planning-infrastructure', this.selectedInfrastructure?.id);
    const services = this.selectedInfrastructure!.services;
    this.selectedService = (services.length > 0)? services[0]: undefined;
    this.onServiceChange();
  }

  onServiceChange(): void {
    this.cookies.set('planning-service', this.selectedService?.id);
    if (!this.selectedService) {
      this.indicators = [];
      this.selectedIndicator = undefined;
      return;
    }
    this.planningService.getIndicators(this.selectedService.id).subscribe(indicators => {
      this.indicators = indicators;
      this.selectedIndicator = indicators?.find(i => i.name === this.cookies.get('planning-indicator', 'string'));
      this.updateMap();
    })
  }

  updateMap(): void {
    if (this.indicatorLayer) {
      this.mapControl?.removeLayer(this.indicatorLayer.id!);
      this.indicatorLayer = undefined;
    }
    if (!this.year || !this.selectedAreaLevel || !this.selectedIndicator || !this.selectedService || this.areas.length === 0) return;
    this.updateMapDescription();

    this.planningService.computeIndicator(this.selectedIndicator.name, this.selectedAreaLevel.id, this.selectedService.id,
      { year: this.year!, prognosis: undefined }).subscribe(results => {
      let max = 0;
      let min = Number.MAX_VALUE;
      this.areas.forEach(area => {
        const data = results.find(d => d.areaId == area.id);
        const value = (data && data.value)? data.value: 0;
        max = Math.max(max, value);
        min = Math.min(min, value);
        area.properties.value = value;
        area.properties.description = `<b>${area.properties.label}</b><br>Nachfrage: ${area.properties.value}`
      })
      const colorFunc = d3.scaleSequential(d3.interpolatePurples).domain([min, max || 1]);
      this.indicatorLayer = this.mapControl?.addLayer({
          order: 0,
          type: 'vector',
          group: this.legendGroup?.id,
          name: this.selectedAreaLevel!.name,
          description: this.selectedAreaLevel!.name,
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
      this.mapControl?.addFeatures(this.indicatorLayer!.id!, this.areas,
        { properties: 'properties' });
    })
  }

  updateMapDescription(): void {

  }

  onIndicatorChange(): void {
    console.log(this.selectedIndicator)
    this.cookies.set('planning-indicator', this.selectedIndicator?.name);
    this.updateMap();
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
    if (this.legendGroup) {
      this.mapControl?.removeGroup(this.legendGroup.id!);
    }
    this.subscriptions.forEach(subscription => subscription.unsubscribe());
  }
}
