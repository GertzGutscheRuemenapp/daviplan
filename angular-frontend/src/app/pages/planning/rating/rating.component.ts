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
  Infrastructure,
  PlanningProcess,
  Service
} from "../../../rest-interfaces";
import { SelectionModel } from "@angular/cdk/collections";
import { MapControl, MapService } from "../../../map/map.service";
import * as d3 from "d3";
import { Subscription } from "rxjs";
import { MapLayerGroup, VectorLayer } from "../../../map/layers";

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
  infrastructures: Infrastructure[] = [];
  activeService?: Service;
  selectedIndicator?: Indicator;
  selectedAreaLevel?: AreaLevel;
  activeInfrastructure?: Infrastructure;
  activeProcess?: PlanningProcess;
  mapControl?: MapControl;
  indicatorLayer?: VectorLayer;
  layerGroup?: MapLayerGroup;
  year?: number;
  subscriptions: Subscription[] = [];

  constructor(private dialog: MatDialog, public cookies: CookieService,
              public planningService: PlanningService, private mapService: MapService) {}

  ngAfterViewInit(): void {
    this.mapControl = this.mapService.get('planning-map');
    this.layerGroup = new MapLayerGroup('Bewertung', { order: -1 })
    this.mapControl.addGroup(this.layerGroup);
    this.subscriptions.push(this.planningService.year$.subscribe(year => {
      this.year = year;
      this.updateMap();
    }));
    this.subscriptions.push(this.planningService.activeInfrastructure$.subscribe(infrastructure => {
      this.activeInfrastructure = infrastructure;
    }))
    this.subscriptions.push(this.planningService.activeService$.subscribe(service => {
      this.activeService = service;
      this.updateMap();
    }));
    this.subscriptions.push(this.planningService.activeProcess$.subscribe(process => {
      this.activeProcess = process;
      this.updateMap();
    }));
    this.planningService.getAreaLevels({ active: true }).subscribe(areaLevels => {
      this.areaLevels = areaLevels;
      this.planningService.getInfrastructures().subscribe(infrastructures => {
        this.infrastructures = infrastructures;
        this.applyUserSettings();
      });
    })
  }

  applyUserSettings(): void {
    this.selectedAreaLevel = this.areaLevels.find(al => al.id === this.cookies.get('planning-area-level', 'number')) || ((this.areaLevels.length > 0)? this.areaLevels[this.areaLevels.length - 1]: undefined);
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
    if (this.indicatorLayer) {
      this.layerGroup?.removeLayer(this.indicatorLayer);
      this.indicatorLayer = undefined;
    }
    if (!this.year || !this.activeProcess || !this.selectedAreaLevel || !this.selectedIndicator || !this.activeService || this.areas.length === 0) return;
    this.updateMapDescription();
    const scenarioId = this.planningService.activeScenario?.isBase? undefined: this.planningService.activeScenario?.id;

    this.planningService.computeIndicator(this.selectedIndicator.name, this.selectedAreaLevel.id, this.activeService.id,
      { year: this.year!, scenario: scenarioId }).subscribe(results => {
      let max = 0;
      let min = Number.MAX_VALUE;
      this.areas.forEach(area => {
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
        showLabel: true,
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
          color: {
            range: d3.interpolatePurples,
            scale: 'sequential',
            bins: 5
          },
          min: min,
          max: max || 1
        },
      });
      this.layerGroup?.addLayer(this.indicatorLayer);
      this.indicatorLayer.addFeatures(this.areas,{ properties: 'properties' });
    })
  }

  updateMapDescription(): void {

  }

  onIndicatorChange(): void {
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
    if (this.layerGroup) {
      this.mapControl?.removeGroup(this.layerGroup);
    }
    this.subscriptions.forEach(subscription => subscription.unsubscribe());
  }
}
