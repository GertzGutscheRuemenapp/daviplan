import { AfterViewInit, Component, OnDestroy, ViewChild } from '@angular/core';
import { MapControl, MapService } from "../../../map/map.service";
import { environment } from "../../../../environments/environment";
import { Observable, Subscription } from "rxjs";
import { map, shareReplay } from "rxjs/operators";
import { BreakpointObserver } from "@angular/cdk/layout";
import { MultilineChartComponent, MultilineData } from "../../../diagrams/multiline-chart/multiline-chart.component";
import { BalanceChartData } from "../../../diagrams/balance-chart/balance-chart.component";
import { PopulationService } from "../population.service";
import { Area, AreaLevel, Layer, LayerGroup } from "../../../rest-interfaces";
import { SettingsService } from "../../../settings.service";
import * as d3 from "d3";
import { StackedBarchartComponent } from "../../../diagrams/stacked-barchart/stacked-barchart.component";
import { sortBy } from "../../../helpers/utils";

export const mockTotalData: MultilineData[] = [
  { group: '2000', values: [0] },
  { group: '2001', values: [-10] },
  { group: '2002', values: [-50] },
  { group: '2003', values: [-12] },
  { group: '2004', values: [-40] },
  { group: '2005', values: [-21] },
  { group: '2006', values: [2] },
  { group: '2007', values: [32] },
  { group: '2008', values: [12] },
  { group: '2009', values: [3] },
  { group: '2010', values: [-4] },
  { group: '2011', values: [15] },
  { group: '2012', values: [12] },
  { group: '2013', values: [-6] },
  { group: '2014', values: [21] },
  { group: '2015', values: [-23] }
]

export const mockData: BalanceChartData[] = [
  { group: '2000', values: [5, -8] },
  { group: '2001', values: [3, -10] },
  { group: '2002', values: [1, -9] },
  { group: '2003', values: [2, -3] },
  { group: '2004', values: [5, -6] },
  { group: '2005', values: [4, -8] },
  { group: '2006', values: [8, -7] },
  { group: '2007', values: [10, -5] },
  { group: '2008', values: [9, -2] },
  { group: '2009', values: [12, -4] },
  { group: '2010', values: [15, 0] },
  { group: '2011', values: [12, -1] },
  { group: '2012', values: [10, -1] },
  { group: '2013', values: [3, -6] },
  { group: '2014', values: [1, -9] },
  { group: '2015', values: [2, -5] }
]

@Component({
  selector: 'app-pop-statistics',
  templateUrl: './pop-statistics.component.html',
  styleUrls: ['./pop-statistics.component.scss']
})
export class PopStatisticsComponent implements AfterViewInit, OnDestroy {
  @ViewChild('totalChart') totalChart?: MultilineChartComponent;
  @ViewChild('balanceChart') balanceChart?: StackedBarchartComponent;
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
  data: BalanceChartData[] = mockData;
  totalData: MultilineData[] = mockTotalData;
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
    this.mapControl.mapDescription = 'Bevölkerungsstatistik > Gemeinden | Wanderung';
    if (this.populationService.isReady)
      this.initData();
    else {
      this.populationService.ready.subscribe(r => {
        this.initData();
      });
    }
  }

  initData(): void {
    this.populationService.realYears$.subscribe(years => {
      this.years = years;
      this.year = years[0];
      this.setSlider();
      this.settings.baseDataSettings$.subscribe(baseSettings => {
        const baseLevel = baseSettings.popStatisticsAreaLevel;
        this.populationService.areaLevels$.subscribe(areaLevels => {
          this.areaLevel = areaLevels.find(al => al.id === baseLevel);
          this.populationService.getAreas(baseLevel,
            { targetProjection: this.mapControl!.map!.mapProjection }).subscribe(areas => {
            this.areas = areas;
            this.updateMap();
            this.updateDiagrams();
          })
        })
      })
    })
    this.subscriptions.push(this.populationService.timeSlider!.valueChanged.subscribe(year => {
      this.year = year;
      this.updateMap();
    }))
  }

  updateMap(): void {
    if (this.statisticsLayer) {
      this.mapControl?.removeLayer(this.statisticsLayer.id!);
      this.statisticsLayer = undefined;
    }
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
        max = (diffDisplay)? Math.max(mvs.births!, mvs.deaths!): this.showBirths? mvs.births!: mvs.deaths!;
      }
      else {
        descr = diffDisplay? 'Wanderungssaldo' : (this.showImmigration) ? 'Zuzüge' : 'Fortzüge';
        color = this.showImmigration? '#1a9850': '#d73027';
        max = (diffDisplay)? Math.max(mvs.immigration!, mvs.emigration!): this.showImmigration? mvs.immigration!: mvs.emigration!;
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
      // ToDo: move wkt parsing to populationservice, is done on every change year/level atm (expensive)
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
        const diffValue = posValue - negValue;
        maxValue = Math.max(maxValue, posValue);
        minValue = Math.min(minValue, negValue);
        maxTotal = Math.max(maxTotal, diffValue);
        minTotal = Math.min(minTotal, diffValue);
        balanceData.push({ group: yearData.year.toString(), values: [posValue, negValue] })
        totalData.push({ group: yearData.year.toString(), values: [diffValue] });
      })
      // ToDo: min, max, labels, legend
      // ToDo: backend - max diff of migration and nature (map)
      this.balanceChart?.draw(balanceData);
      this.totalChart?.draw(totalData);
    })
  }

  onAreaChange(): void {
    this.mapControl?.selectFeatures([this.activeArea!.id], this.statisticsLayer!.id!, { silent: true, clear: true });
    this.updateDiagrams();
  }

  setSlider(): void {
    let slider = this.populationService.timeSlider!;
    slider.prognosisStart = 0;
    slider.years = this.years!;
    slider.value = this.year;
    slider.draw();
  }

  ngOnDestroy(): void {
    if (this.statisticsLayer)
      this.mapControl?.removeLayer(this.statisticsLayer.id!);
    if (this.legendGroup)
      this.mapControl?.removeGroup(this.legendGroup.id!)
    this.subscriptions.forEach(subscription => subscription.unsubscribe());
  }

}
