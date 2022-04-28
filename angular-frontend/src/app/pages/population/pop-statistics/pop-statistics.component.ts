import { AfterViewInit, Component, OnDestroy, ViewChild } from '@angular/core';
import { MapControl, MapService } from "../../../map/map.service";
import { environment } from "../../../../environments/environment";
import { Subscription } from "rxjs";
import { MultilineChartComponent, MultilineData } from "../../../diagrams/multiline-chart/multiline-chart.component";
import { BalanceChartComponent, BalanceChartData } from "../../../diagrams/balance-chart/balance-chart.component";
import { PopulationService } from "../population.service";
import { Area, AreaLevel, Layer, LayerGroup } from "../../../rest-interfaces";
import { SettingsService } from "../../../settings.service";
import * as d3 from "d3";
import { sortBy } from "../../../helpers/utils";
import { CookieService } from "../../../helpers/cookies.service";

@Component({
  selector: 'app-pop-statistics',
  templateUrl: './pop-statistics.component.html',
  styleUrls: ['./pop-statistics.component.scss']
})
export class PopStatisticsComponent implements AfterViewInit, OnDestroy {
  totalChart?: MultilineChartComponent;
  balanceChart?: BalanceChartComponent;
  @ViewChild('totalChart', { static: false }) set _totalChart(content: MultilineChartComponent) {
    if (content) this.totalChart = content;
  }
  @ViewChild('balanceChart', { static: false }) set _balanceChart(content: BalanceChartComponent) {
    if (content) this.balanceChart = content;
  }
  totalChartProps: any = {};
  balanceChartProps: any = {};
  selectedTab = 0;
  mapControl?: MapControl;
  backend: string = environment.backend;
  areas: Area[] = [];
  areaLevel?: AreaLevel;
  years?: number[];
  year?: number;
  theme: 'nature' | 'migration' = 'nature';
  statisticsLayer?: Layer;
  subscriptions: Subscription[] = [];
  legendGroup?: LayerGroup;
  activeArea?: Area;
  showBirths: boolean = true;
  showDeaths: boolean = true;
  showImmigration: boolean = true;
  showEmigration: boolean = true;

  constructor(private mapService: MapService,
              private populationService: PopulationService, private settings: SettingsService,
              private cookies: CookieService) {}

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
        this.populationService.getAreaLevels({ active: true }).subscribe(areaLevels => {
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
      this.cookies.set('pop-year', year);
      this.updateMap();
      this.updateDiagrams();
    }))
  }

  applyUserSettings(): void {
    const areaId = this.cookies.get(`pop-area-${this.areaLevel!.id}`, 'number');
    this.activeArea = this.areas?.find(a => a.id === areaId);
    const theme = this.cookies.get('pop-stat-theme', 'string');
    this.theme = theme as any || 'nature';
    this.showBirths = this.cookies.get('pop-stat-births', 'boolean');
    this.showDeaths = this.cookies.get('pop-stat-deaths', 'boolean');
    this.showImmigration = this.cookies.get('pop-stat-immigration', 'boolean');
    this.showEmigration = this.cookies.get('pop-stat-emigration', 'boolean');
    this.showEmigration = this.cookies.get('pop-stat-emigration', 'boolean');
    const year = this.cookies.get('pop-year','number');
    this.year = year || this.years![this.years!.length - 1];
    this.setSlider();
    this.updateMap();
    this.updateDiagrams();
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
      const radiusFunc = d3.scaleLinear().domain([0, max || 1000]).range([5, 50]);
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
        this.cookies.set(`pop-area-${this.areaLevel!.id}`, this.activeArea?.id);
        this.updateDiagrams();
      })
    })
  }

  updateDiagrams(): void {
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
      this.balanceChartProps.title = (this.theme === 'nature')? 'Natürliche Bevölkerungsentwicklung': 'Wanderung';
      this.balanceChartProps.subtitle = this.totalChartProps.subtitle = this.activeArea!.properties.label;
      const topLabel = (this.theme === 'nature')? 'Geburten': 'Zuzüge';
      const bottomLabel = (this.theme === 'nature')? 'Sterbefälle': 'Fortzüge';
      this.balanceChartProps.yTopLabel = topLabel;
      this.balanceChartProps.yBottomLabel = bottomLabel;
      this.balanceChartProps.labels = [topLabel, bottomLabel];
      const tchTitle = (this.theme === 'nature')? 'Natürlicher Saldo': 'Wanderungssaldo';
      this.balanceChartProps.lineLabel = tchTitle;
      this.balanceChartProps.yPadding = Math.ceil(Math.max(maxValue, -minValue) * 0.2);
      this.balanceChartProps.data = balanceData;

      this.totalChartProps.title = tchTitle;
      this.totalChartProps.labels = [tchTitle];
      this.totalChartProps.yTopLabel = 'mehr ' + topLabel;
      this.totalChartProps.yBottomLabel = 'mehr ' + bottomLabel;
      this.totalChartProps.yPadding = Math.ceil(Math.max(maxTotal, -minTotal) * 0.2);
      this.totalChartProps.data = totalData;

      // workaround to force redraw of diagram by triggering ngIf wrapper
      const _prev = this.selectedTab;
      this.selectedTab = -1;
      setTimeout(() => {  this.selectedTab = _prev; }, 1);
    })
  }

  onAreaChange(): void {
    this.cookies.set(`pop-area-${this.areaLevel!.id}`, this.activeArea!.id);
    this.mapControl?.selectFeatures([this.activeArea!.id], this.statisticsLayer!.id!, { silent: true, clear: true });
    this.updateDiagrams();
  }

  onThemeChange(updateDiagrams: boolean = false): void {
    this.cookies.set('pop-stat-theme', this.theme);
    this.cookies.set('pop-stat-births', this.showBirths);
    this.cookies.set('pop-stat-deaths', this.showDeaths);
    this.cookies.set('pop-stat-immigration', this.showImmigration);
    this.cookies.set('pop-stat-emigration', this.showEmigration);
    this.updateMap();
    if (updateDiagrams)
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
    let theme = '';
    if (this.theme === 'nature')
        theme = (this.showBirths && this.showDeaths)? 'Geburten und Sterbefälle': (this.showBirths)? 'Geburten': (this.showDeaths)? 'Sterbefälle': 'keine Auswahl';
    else
      theme = (this.showImmigration && this.showEmigration)? 'Wanderung': (this.showImmigration)? 'Zuzüge': (this.showEmigration)? 'Fortzüge': 'keine Auswahl';
    let description = `${theme} für Gebietseinheit ${this.areaLevel.name} | ${this.year}`;
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
