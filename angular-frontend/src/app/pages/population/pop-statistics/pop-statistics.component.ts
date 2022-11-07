import { AfterViewInit, Component, OnDestroy, ViewChild } from '@angular/core';
import { MapControl, MapService } from "../../../map/map.service";
import { environment } from "../../../../environments/environment";
import { Subscription } from "rxjs";
import { MultilineChartComponent, MultilineData } from "../../../diagrams/multiline-chart/multiline-chart.component";
import { BalanceChartComponent, BalanceChartData } from "../../../diagrams/balance-chart/balance-chart.component";
import { PopulationService } from "../population.service";
import { Area, AreaLevel } from "../../../rest-interfaces";
import { SettingsService } from "../../../settings.service";
import { sortBy } from "../../../helpers/utils";
import { CookieService } from "../../../helpers/cookies.service";
import { MapLayerGroup, VectorLayer } from "../../../map/layers";
import { SideToggleComponent } from "../../../elements/side-toggle/side-toggle.component";

@Component({
  selector: 'app-pop-statistics',
  templateUrl: './pop-statistics.component.html',
  styleUrls: ['./pop-statistics.component.scss']
})
export class PopStatisticsComponent implements AfterViewInit, OnDestroy {
  totalChart?: MultilineChartComponent;
  balanceChart?: BalanceChartComponent;
  @ViewChild('chartToggle') chartToggle!: SideToggleComponent;
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
  years: number[] = [];
  year?: number;
  theme: 'nature' | 'migration' = 'nature';
  statisticsLayer?: VectorLayer;
  subscriptions: Subscription[] = [];
  layerGroup?: MapLayerGroup;
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
    this.layerGroup = new MapLayerGroup('Bevölkerungssalden', { order: -1 })
    this.mapControl.addGroup(this.layerGroup);
    this.mapControl?.setDescription('');
    if (this.populationService.isReady)
      this.initData();
    else {
      this.populationService.ready.subscribe(r => {
        this.initData();
      });
    }
  }

  initData(): void {
    this.populationService.getYears({ params: 'has_statistics_data=true' }).subscribe(years => {
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
    this.subscriptions.push(this.populationService.timeSlider!.onChange.subscribe(year => {
      this.year = year;
      this.cookies.set('pop-year', year);
      this.updateMap();
    }))
  }

  applyUserSettings(): void {
    const areaId = this.cookies.get(`pop-area-${this.areaLevel!.id}`, 'number');
    this.activeArea = this.areas?.find(a => a.id === areaId);
    const theme = this.cookies.get('pop-stat-theme', 'string');
    this.theme = theme as any || 'nature';
    // all true by default
    const showBirths = this.cookies.get('pop-stat-births', 'boolean');
    this.showBirths = (showBirths !== undefined)? showBirths: true;
    const showDeaths = this.cookies.get('pop-stat-deaths', 'boolean');
    this.showDeaths = (showDeaths !== undefined)? showDeaths: true;
    const showImmigration = this.cookies.get('pop-stat-immigration', 'boolean');
    this.showImmigration = (showImmigration !== undefined)? showImmigration: true;
    const showEmigration = this.cookies.get('pop-stat-emigration', 'boolean');
    this.showEmigration = (showEmigration !== undefined)? showEmigration: true;
    const year = this.cookies.get('pop-year','number');
    this.year = (year && this.years!.indexOf(year) > -1)? year: (this.years.length > 0)? this.years[0]: undefined;
    this.setSlider();
    this.updateMap();
    this.updateDiagrams();
  }

  updateMap(): void {
    if (this.statisticsLayer) {
      this.layerGroup?.removeLayer(this.statisticsLayer);
      this.statisticsLayer = undefined;
    }
    this.updateMapDescription();
    if ((this.theme === 'nature' && !this.showBirths && !this.showDeaths) ||
         this.theme === 'migration' && !this.showImmigration && !this.showEmigration){
      return;
    }
    this.populationService.getStatisticsData({ year: this.year! }).subscribe(statistics => {
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
      const colorFunc = function(value: number) {
        return (value > 0)? '#1a9850': (value < 0)? '#d73027': 'grey';
      };

      this.statisticsLayer = new VectorLayer(descr, {
        order: 0,
        description: 'ToDo',
        opacity: 1,
        style: {
          strokeColor: 'white',
          fillColor: color,
          symbol: 'circle'
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
        select: {
          enabled: true,
          style: {
            strokeColor: 'rgb(180, 180, 0)',
            fillColor: 'rgba(255, 255, 0, 0.9)'
          }
        },
        valueStyles: {
          field: 'value',
          fillColor: diffDisplay? { colorFunc: colorFunc }: undefined,
          radius: {
            range: [5, 50],
            scale: 'sqrt'
          },
          min: 0,
          max: max || 1000
        },
        unit: 'Ew.',
        forceSign: diffDisplay,
        labelOffset: { y: 15 }
      });
      this.layerGroup?.addLayer(this.statisticsLayer);
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
        let description = `<b>${area.properties.label}</b><br>`;
        description += (diffDisplay && !value)? 'keine Änderung ': `${diffDisplay && value > 0? '+': ''}${area.properties.value.toLocaleString()} Ew. im Jahr ${this.year}`;
        area.properties.description = description;
      })
      this.statisticsLayer.addFeatures(this.areas,{
        properties: 'properties',
        geometry: 'centroid',
        zIndex: 'value'
      });
      if (this.activeArea)
        this.statisticsLayer.selectFeatures([this.activeArea.id], { silent: true });
      this.statisticsLayer!.featuresSelected.subscribe(features => {
        this.setArea(this.areas.find(area => area.id === features[0].get('id')));
      })
      this.statisticsLayer!.featuresSelected.subscribe(features => {
        if (this.activeArea?.id === features[0].get('id'))
          this.setArea(undefined);
      })
    })
  }

  setArea(area: Area | undefined): void {
    this.activeArea = area;
    this.cookies.set(`pop-area-${this.areaLevel!.id}`, this.activeArea?.id);
    this.chartToggle.expanded = true;
    this.updateDiagrams();
  }

  updateDiagrams(): void {
    if (!this.activeArea) return;
    this.populationService.getStatisticsData({ areaId: this.activeArea.id }).subscribe(statistics => {
      let totalData: MultilineData[] = [];
      let balanceData: BalanceChartData[] = [];
      let maxTotal = 0, minTotal = 0, maxValue = 0, minValue = 0;
      sortBy(statistics, 'year').forEach(yearData => {
        const posValue = (this.theme === 'nature')? yearData.births: yearData.immigration;
        const negValue = -((this.theme === 'nature')? yearData.deaths: yearData.emigration);
        const diffValue = posValue + negValue;
        maxValue = Math.max(maxValue, posValue);
        minValue = Math.min(minValue, negValue);
        maxTotal = Math.max(maxTotal, diffValue, 1);
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
      this.balanceChartProps.yPadding = Math.ceil(Math.max(maxValue, Math.abs(minValue)) * 0.2);
      this.balanceChartProps.data = balanceData;

      this.totalChartProps.title = tchTitle;
      this.totalChartProps.labels = [tchTitle];
      this.totalChartProps.yTopLabel = 'mehr ' + topLabel;
      this.totalChartProps.yBottomLabel = 'mehr ' + bottomLabel;
      this.totalChartProps.yPadding = Math.ceil(Math.max(maxTotal, Math.abs(minTotal)) * 0.2);
      this.totalChartProps.data = totalData;

      // workaround to force redraw of diagram by triggering ngIf wrapper
      const _prev = this.selectedTab;
      this.selectedTab = -1;
      setTimeout(() => {  this.selectedTab = _prev; }, 1);
    })
  }

  onAreaChange(): void {
    this.cookies.set(`pop-area-${this.areaLevel!.id}`, this.activeArea!.id);
    this.statisticsLayer?.selectFeatures([this.activeArea!.id], { silent: true, clear: true });
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
    let description = `${theme} für ${this.areaLevel.name} ${this.year}`;
    this.mapControl?.setDescription(description);
  }

  ngOnDestroy(): void {
    if (this.layerGroup) this.mapControl?.removeGroup(this.layerGroup)
    this.subscriptions.forEach(subscription => subscription.unsubscribe());
  }

}
