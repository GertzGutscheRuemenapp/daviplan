import { AfterViewInit, Component, OnDestroy, ViewChild } from '@angular/core';
import { MapControl, MapService } from "../../../map/map.service";
import { environment } from "../../../../environments/environment";
import { forkJoin, Observable, Subscription } from "rxjs";
import { map, shareReplay } from "rxjs/operators";
import { BreakpointObserver } from "@angular/cdk/layout";
import { MultilineChartComponent, MultilineData } from "../../../diagrams/multiline-chart/multiline-chart.component";
import { BalanceChartComponent, BalanceChartData } from "../../../diagrams/balance-chart/balance-chart.component";
import { PopulationService } from "../population.service";
import { Area, AreaLevel, Layer, LayerGroup } from "../../../rest-interfaces";
import { SettingsService } from "../../../settings.service";
import * as d3 from "d3";
import { sortBy } from "../../../helpers/utils";

@Component({
  selector: 'app-pop-statistics',
  templateUrl: './pop-statistics.component.html',
  styleUrls: ['./pop-statistics.component.scss']
})
export class PopStatisticsComponent implements AfterViewInit, OnDestroy {
  @ViewChild('totalChart') totalChart?: MultilineChartComponent;
  @ViewChild('balanceChart') balanceChart?: BalanceChartComponent;
  mapControl?: MapControl;
  backend: string = environment.backend;
  areas: Area[] = [];
  areaLevel?: AreaLevel;
  years?: number[];
  year?: number;
  theme: 'nature' | 'migration' = 'nature';
  isSM$: Observable<boolean> = this.breakpointObserver.observe('(max-width: 50em)')
    .pipe(
      map(result => result.matches),
      shareReplay()
    );
  statisticsLayer?: Layer;
  subscriptions: Subscription[] = [];
  legendGroup?: LayerGroup;
  activeArea?: Area;
  showBirths: boolean = true;
  showDeaths: boolean = true;
  showImmigration: boolean = true;
  showEmigration: boolean = true;

  constructor(private breakpointObserver: BreakpointObserver, private mapService: MapService,
              private populationService: PopulationService, private settings: SettingsService) {}

  ngAfterViewInit(): void {
    this.mapControl = this.mapService.get('population-map');
    this.legendGroup = this.mapControl.addGroup({
      name: 'Bevölkerungssalden',
      order: -1
    }, false)
    this.mapControl.mapDescription = '';
    if (this.populationService.isReady)
      this.initData();
    else {
      this.populationService.ready.subscribe(r => {
        this.initData();
      });
    }
  }

  initData(): void {
    this.populationService.getRealYears().subscribe(years => {
      this.years = years;
      this.year = years[0];
      this.setSlider();
      this.settings.baseDataSettings$.subscribe(baseSettings => {
        const baseLevel = baseSettings.popStatisticsAreaLevel;
        this.populationService.getAreaLevels().subscribe(areaLevels => {
          this.areaLevel = areaLevels.find(al => al.id === baseLevel);
          if (!this.areaLevel) return;
          this.populationService.getAreas(baseLevel,
            { targetProjection: this.mapControl!.map!.mapProjection }).subscribe(areas => {
            this.areas = areas;
            this.applyUserSettings();
          })
        })
      })
    })
    this.subscriptions.push(this.populationService.timeSlider!.valueChanged.subscribe(year => {
      this.year = year;
      this.updateMap();
      this.updateDiagrams();
    }))
  }

  applyUserSettings(): void {
    let observables: Observable<any>[] = [];
    observables.push(this.settings.user.get(`pop-area-${this.areaLevel!.id}`).pipe(map(areaId => {
      this.activeArea = this.areas?.find(a => a.id === areaId);
    })));
    observables.push(this.settings.user.get('pop-stat-theme').pipe(map(theme => {
      this.theme = theme || 'nature';
    })));
    observables.push(this.settings.user.get('pop-stat-births').pipe(map(checked => {
      this.showBirths = (checked !== undefined)? checked: true;
    })));
    observables.push(this.settings.user.get('pop-stat-deaths').pipe(map(checked => {
      this.showDeaths = (checked !== undefined)? checked: true;
    })));
    observables.push(this.settings.user.get('pop-stat-immigration').pipe(map(checked => {
      this.showImmigration = (checked !== undefined)? checked: true;
    })));
    observables.push(this.settings.user.get('pop-stat-emigration').pipe(map(checked => {
      this.showEmigration = (checked !== undefined)? checked: true;
    })));
    forkJoin(...observables).subscribe(() => {
      this.setSlider();
      this.updateMap();
      this.updateDiagrams();
    })
  }

  updateMap(): void {
    if (this.statisticsLayer) {
      this.mapControl?.removeLayer(this.statisticsLayer.id!);
      this.statisticsLayer = undefined;
    }
    this.updateMapDescription();
    if ((this.theme === 'nature' && !this.showBirths && !this.showDeaths) ||
         this.theme === 'migration' && !this.showImmigration && !this.showEmigration){
      return;
    }
    this.populationService.getStatistics({ year: this.year! }).subscribe(statistics => {
      let descr = '';
      let max: number;
      let color: string;
      const diffDisplay = ((this.theme ==='nature' && this.showBirths && this.showDeaths) || (this.theme ==='migration' && this.showEmigration && this.showImmigration));
      const mvs = this.areaLevel?.maxValues!;
      if (this.theme === 'nature') {
        descr = diffDisplay? 'Natürlicher Saldo' : (this.showBirths) ? 'Geburten' : 'Sterbefälle';
        color = this.showBirths? '#1a9850': '#d73027';
        max = (diffDisplay)? Math.max(mvs.natureDiff!): this.showBirths? mvs.births!: mvs.deaths!;
      }
      else {
        descr = diffDisplay? 'Wanderungssaldo' : (this.showImmigration) ? 'Zuzüge' : 'Fortzüge';
        color = this.showImmigration? '#1a9850': '#d73027';
        max = (diffDisplay)? Math.max(mvs.migrationDiff!): this.showImmigration? mvs.immigration!: mvs.emigration!;
      }
      const radiusFunc = d3.scaleLinear().domain([0, max]).range([5, 50]);
      const colorFunc = function(value: number) {
        return (value > 0)? '#1a9850': (value < 0)? '#d73027': 'grey';
      };

      this.statisticsLayer = this.mapControl?.addLayer({
        order: 0,
        type: 'vector',
        group: this.legendGroup?.id,
        name: descr,
        description: 'ToDo',
        opacity: 1,
        symbol: {
          strokeColor: 'white',
          fillColor: color,
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
          fillColor: 'rgba(255, 255, 0, 0.7)',
        },
        selectable: true,
        select: {
          strokeColor: 'rgb(180, 180, 0)',
          fillColor: 'rgba(255, 255, 0, 0.9)'
        },
        colorFunc: diffDisplay? colorFunc: undefined,
        radiusFunc: radiusFunc
      });
      this.areas.forEach(area => {
        const data = statistics.find(d => d.area == area.id);
        let value = 0;
        if (data) {
          if (this.theme === 'nature') {
            value = (this.showBirths && this.showDeaths) ? data.births - data.deaths : (this.showBirths) ? data.births : data.deaths;
          } else {
            value = (this.showImmigration && this.showEmigration) ? data.immigration - data.emigration : (this.showImmigration) ? data.immigration : data.emigration;
          }
        }
        area.properties.value = value;
        area.properties.description = `<b>${area.properties.label}</b><br>${descr}: ${area.properties.value}`
      })
      this.mapControl?.addFeatures(this.statisticsLayer!.id!, this.areas,
        { properties: 'properties', geometry: 'centroid', zIndex: 'value' });
      if (this.activeArea)
        this.mapControl?.selectFeatures([this.activeArea.id], this.statisticsLayer!.id!, { silent: true });
      this.statisticsLayer!.featureSelected?.subscribe(evt => {
        if (evt.selected) {
          this.activeArea = this.areas.find(area => area.id === evt.feature.get('id'));
        }
        else {
          this.activeArea = undefined;
        }
        this.settings.user.set(`pop-area-${this.areaLevel!.id}`, this.activeArea!.id);
        this.updateDiagrams();
      })
    })
  }

  updateDiagrams(): void {
    this.balanceChart?.clear();
    this.totalChart?.clear();
    if (!this.activeArea) return;
    this.populationService.getStatistics({ areaId: this.activeArea.id }).subscribe(statistics => {
      let totalData: MultilineData[] = [];
      let balanceData: BalanceChartData[] = [];
      let maxTotal = 0, minTotal = 0, maxValue = 0, minValue = 0;
      sortBy(statistics, 'year').forEach(yearData => {
        const posValue = (this.theme === 'nature')? yearData.births: yearData.immigration;
        const negValue = -((this.theme === 'nature')? yearData.deaths: yearData.emigration);
        const diffValue = posValue + negValue;
        maxValue = Math.max(maxValue, posValue);
        minValue = Math.min(minValue, negValue);
        maxTotal = Math.max(maxTotal, diffValue);
        minTotal = Math.min(minTotal, diffValue);
        balanceData.push({ group: yearData.year.toString(), values: [posValue, negValue] })
        totalData.push({ group: yearData.year.toString(), values: [diffValue] });
      })
      // ToDo: calc yPadding (10% of min/max or sth like that)
      this.balanceChart!.title = (this.theme === 'nature')? 'Natürliche Bevölkerungsentwicklung': 'Wanderung';
      this.balanceChart!.subtitle = this.totalChart!.subtitle = this.activeArea!.properties.label;
      const topLabel = (this.theme === 'nature')? 'Geburten': 'Zuzüge';
      const bottomLabel = (this.theme === 'nature')? 'Sterbefälle': 'Fortzüge';
      this.balanceChart!.yTopLabel = topLabel;
      this.balanceChart!.yBottomLabel = bottomLabel;
      this.balanceChart!.labels = [topLabel, bottomLabel];
      const tchTitle = (this.theme === 'nature')? 'Natürlicher Saldo': 'Wanderungssaldo';
      this.balanceChart!.lineLabel = tchTitle;
      this.balanceChart!.yPadding = Math.ceil(Math.max(maxValue, -minValue) * 0.2);

      this.totalChart!.title = tchTitle;
      this.totalChart!.labels = [tchTitle];
      this.totalChart!.yTopLabel = 'mehr ' + topLabel;
      this.totalChart!.yBottomLabel = 'mehr ' + bottomLabel;
      this.totalChart!.xLegendOffset = 0;
      this.totalChart!.yLegendOffset = 30;
      this.totalChart!.margin.right = 60;
      this.totalChart!.yPadding = Math.ceil(Math.max(maxTotal, -minTotal) * 0.2)

      this.balanceChart?.draw(balanceData);
      this.totalChart?.draw(totalData);
    })
  }

  onAreaChange(): void {
    this.settings.user.set(`pop-area-${this.areaLevel!.id}`, this.activeArea!.id);
    this.mapControl?.selectFeatures([this.activeArea!.id], this.statisticsLayer!.id!, { silent: true, clear: true });
    this.updateDiagrams();
  }

  onThemeChange(): void {
    this.settings.user.set('pop-stat-theme', this.theme);
    this.settings.user.set('pop-stat-births', this.showBirths);
    this.settings.user.set('pop-stat-deaths', this.showDeaths);
    this.settings.user.set('pop-stat-immigration', this.showImmigration);
    this.settings.user.set('pop-stat-emigration', this.showEmigration);
    this.updateMap();
    this.updateDiagrams()
  }

  setSlider(): void {
    let slider = this.populationService.timeSlider!;
    slider.prognosisStart = 0;
    slider.years = this.years!;
    slider.value = this.year;
    slider.draw();
  }

  updateMapDescription(): void {
    if (!this.areaLevel) return;
    const theme = (this.theme === 'nature')? 'Natürliche Bevölkerungsentwicklung': 'Wanderung';
    let description = `${theme} für ${this.areaLevel.name} | ${this.year}`;
    this.mapControl!.mapDescription = description;
  }

  ngOnDestroy(): void {
    if (this.statisticsLayer)
      this.mapControl?.removeLayer(this.statisticsLayer.id!);
    if (this.legendGroup)
      this.mapControl?.removeGroup(this.legendGroup.id!)
    this.subscriptions.forEach(subscription => subscription.unsubscribe());
  }

}
