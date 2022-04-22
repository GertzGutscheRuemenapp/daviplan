import { Component, AfterViewInit, ViewChild, TemplateRef, OnDestroy } from '@angular/core';
import { MapControl, MapService } from "../../../map/map.service";
import { StackedBarchartComponent, StackedData } from "../../../diagrams/stacked-barchart/stacked-barchart.component";
import { MultilineChartComponent } from "../../../diagrams/multiline-chart/multiline-chart.component";
import { AgeTreeComponent, AgeTreeData } from "../../../diagrams/age-tree/age-tree.component";
import { forkJoin, Observable, Subscription } from "rxjs";
import { map } from "rxjs/operators";
import { MatDialog } from "@angular/material/dialog";
import { ConfirmDialogComponent } from "../../../dialogs/confirm-dialog/confirm-dialog.component";
import { PopulationService } from "../population.service";
import { Area, AreaLevel, Gender, Layer, LayerGroup, AgeGroup, Prognosis } from "../../../rest-interfaces";
import * as d3 from "d3";
import { SelectionModel } from "@angular/cdk/collections";
import { sortBy } from "../../../helpers/utils";
import { SettingsService } from "../../../settings.service";
import { CookieService } from "../../../helpers/cookies.service";

@Component({
  selector: 'app-pop-development',
  templateUrl: './pop-development.component.html',
  styleUrls: ['./pop-development.component.scss']
})
export class PopDevelopmentComponent implements AfterViewInit, OnDestroy {
  lineChart?: MultilineChartComponent;
  barChart?: StackedBarchartComponent;
  ageTree?: AgeTreeComponent;
  @ViewChild('lineChart', { static: false }) set _lineChart(content: MultilineChartComponent) {
    if (content) this.lineChart = content;
  }
  @ViewChild('barChart', { static: false }) set _barChart(content: StackedBarchartComponent) {
    if (content) this.barChart = content;
  }
  @ViewChild('ageTree', { static: false }) set _ageTree(content: AgeTreeComponent) {
    if (content) this.ageTree = content;
  }
  @ViewChild('ageGroupTemplate') ageGroupTemplate!: TemplateRef<any>;
  barChartProps: any = {};
  lineChartProps: any = {};
  ageTreeProps: any = {};
  subscriptions: Subscription[] = [];
  populationLayer?: Layer;
  legendGroup?: LayerGroup;
  compareYears = false;
  areaLevels: AreaLevel[] = [];
  areas: Area[] = [];
  realYears?: number[];
  selectedTab = 0;
  prognosisYears?: number[];
  prognoses?: Prognosis[];
  activePrognosis?: Prognosis;
  genders: Gender[] = [];
  ageGroups: AgeGroup[] = [];
  mapControl?: MapControl;
  activeLevel?: AreaLevel;
  activeArea?: Area;
  selectedGender?: Gender;
  year: number = 0;
  ageGroupSelection = new SelectionModel<AgeGroup>(true );
  allAgeGroupsChecked: boolean = true;
  ageGroupColors: Record<number, string> = {};

  constructor(private mapService: MapService, private dialog: MatDialog,
              private populationService: PopulationService, private settings: SettingsService,
              private cookies: CookieService) { }

  ngAfterViewInit(): void {
    this.mapControl = this.mapService.get('population-map');
    this.legendGroup = this.mapControl.addGroup({
      name: 'Bevölkerungsentwicklung',
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
    let observables: Observable<any>[] = [];
    observables.push(this.populationService.getPrognoses().pipe(map(prognoses => {
      this.prognoses = prognoses;
    })))
    observables.push(this.populationService.getRealYears().pipe( map(years => {
      this.realYears = years;
    })))
    observables.push(this.populationService.getPrognosisYears().pipe( map(years => {
      this.prognosisYears = years;
    })))
    observables.push(this.populationService.getGenders().pipe(map(genders => {
      const genderAll: Gender = {
        id: -1,
        name: 'alle'
      }
      this.genders = [genderAll].concat(genders);
    })))
    observables.push(this.populationService.getAreaLevels({ active: true }).pipe(map(areaLevels => {
      this.areaLevels = areaLevels;
    })))
    observables.push(this.populationService.getAgeGroups().pipe(map(ageGroups => {
      this.ageGroupSelection.clear();
      let colorScale = d3.scaleSequential().domain([0, ageGroups.length])
        .interpolator(d3.interpolateRainbow);
      this.ageGroupColors = {};
      ageGroups.forEach((ag, i) => {
        this.ageGroupColors[ag.id!] = colorScale(i);
      });
      this.ageGroups = ageGroups;
    })))

    forkJoin(...observables).subscribe(() => {
      this.applyUserSettings();
    })

    this.subscriptions.push(this.populationService.timeSlider!.valueChanged.subscribe(year => {
      this.year = year;
      this.cookies.set('pop-year', year);
      this.updateMap();
      // update age tree on year change
      if (this.selectedTab === 2 && this.activeArea) {
        this.ageTreeProps.subtitle = `${this.activeArea?.properties.label!} ${year}`;
        this.forceDiagramReload();
      }
    }))
  }

  applyUserSettings(): void {
    const ageGroupIds = this.cookies.get('pop-ageGroups', 'array');
    if (ageGroupIds) {
      this.ageGroups.forEach(ag => {
        const select = ageGroupIds? ageGroupIds.indexOf(ag.id!.toString()) >= 0 : true;
        if (select)
          this.ageGroupSelection.select(ag);
      })
    }
    this.allAgeGroupsChecked = this.ageGroupSelection.selected.length === this.ageGroups.length;
    const genderId = this.cookies.get('pop-gender','number');
    this.selectedGender = this.genders.find(g => g.id === genderId) || this.genders[0];
    const progId = this.cookies.get('pop-prognosis','number');
    const defaultProg = this.prognoses?.find(prognosis => prognosis.isDefault);
    this.activePrognosis = this.prognoses!.find(p => p.id === progId) || defaultProg;
    const year = this.cookies.get('pop-year','number');
    this.year = year || this.realYears![this.realYears!.length - 1];
    const areaLevelId = this.cookies.get('pop-area-level','number');
    this.activeLevel = this.areaLevels.find(al => al.id === areaLevelId);

    this.setSlider();
    this.onLevelChange();
  }

  setSlider(): void {
    if (!(this.realYears && this.prognosisYears)) return;
    let slider = this.populationService.timeSlider!;
    slider.prognosisStart = this.prognosisYears[0] || 0;
    slider.years = this.realYears.concat(this.prognosisYears);
    slider.value = this.year;
    slider.draw();
  }

  editAgeGroups(): void {
    let dialogRef = this.dialog.open(ConfirmDialogComponent, {
      panelClass: 'absolute',
      width: '500px',
      disableClose: false,
      data: {
        title: 'Altersgruppen definieren',
        subtitle: 'Marker hinzufügen und entfernen',
        template: this.ageGroupTemplate,
        closeOnConfirm: true,
        confirmButtonText: 'Speichern',
        infoText: 'Hier können Sie die Altersgruppen für die Darstellung der Bevölkerungsentwicklung definieren. Dafür positionieren Sie die Marker bitte an den Grenzen („bis unter X Jahre“). Liegen die Grundlagendaten nach Einzelaltersjahrgängen vor, können Sie die Altersgruppen frei wählen. Sind die Grundlagendaten bereits nach Altersgruppen zusammengefasst, können diese hier für die Darstellung weiter aggregiert werden. Ein Klick auf den Button Speichern übernimmt Ihre Angaben für die Darstellung.'
      }
    });
    dialogRef.afterClosed().subscribe((ok: boolean) => {  });
    dialogRef.componentInstance.confirmed.subscribe(() => {  });
  }

  onLevelChange(): void {
    this.cookies.set('pop-area-level', this.activeLevel?.id);
    if (!this.activeLevel) return;
    this.populationService.getAreas(this.activeLevel!.id, {targetProjection: this.mapControl!.map!.mapProjection}).subscribe(areas => {
      this.areas = areas;
      const areaId = this.cookies.get(`pop-area-${this.activeLevel!.id}`, 'number');
      this.activeArea = this.areas?.find(a => a.id === areaId);
      this.updateMap();
      this.updateDiagrams();
    });
  }

  onPrognosisChange(): void {
    this.cookies.set('pop-prognosis', this.activePrognosis?.id);
    this.updateMap();
    this.updateDiagrams();
  }

  onGenderChange(): void {
    this.cookies.set('pop-genders', this.selectedGender!.id);
    this.updateMap();
    this.updateDiagrams();
  }

  onAreaChange(): void {
    this.mapControl?.selectFeatures([this.activeArea!.id], this.populationLayer!.id!, { silent: true, clear: true });
    this.cookies.set(`pop-area-${this.activeLevel!.id}`, this.activeArea?.id);
    this.updateDiagrams();
  }

  updateMap(): void {
    // only catch prognosis data if selected year is not in real data
    const prognosis = (this.realYears?.indexOf(this.year) === -1)? this.activePrognosis?.id: undefined;
    const genders = (this.selectedGender?.id !== -1)? [this.selectedGender!.id]: undefined;
    const ageGroups = this.ageGroupSelection.selected;
    if (this.populationLayer) {
      this.mapControl?.removeLayer(this.populationLayer.id!);
      this.populationLayer = undefined;
    }
    this.updateMapDescription();
    if (ageGroups.length === 0 || !this.activeLevel) return;
    this.populationService.getAreaLevelPopulation(this.activeLevel.id, this.year,
      { genders: genders, prognosis: prognosis, ageGroups: ageGroups.map(ag => ag.id!) }).subscribe(popData => {
      const radiusFunc = d3.scaleLinear().domain([0, this.activeLevel?.maxValues!.population! || 1000]).range([5, 50]);
      this.populationLayer = this.mapControl?.addLayer({
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
        area.properties.description = `<b>${area.properties.label}</b><br>Bevölkerung: ${area.properties.value}`
      })
      this.mapControl?.addFeatures(this.populationLayer!.id!, this.areas,
        { properties: 'properties', geometry: 'centroid', zIndex: 'value' });
      if (this.activeArea)
        this.mapControl?.selectFeatures([this.activeArea.id], this.populationLayer!.id!, { silent: true });
      this.populationLayer!.featureSelected?.subscribe(evt => {
        if (evt.selected) {
          this.activeArea = this.areas.find(area => area.id === evt.feature.get('id'));
        }
        else {
          this.activeArea = undefined;
        }
        this.cookies.set(`pop-area-${this.activeLevel!.id}`, this.activeArea?.id);
        this.updateDiagrams();
      })
    })
  }

  updateDiagrams(): void {
    const genders = (this.selectedGender?.id !== -1)? [this.selectedGender!.id]: undefined;
    let ageGroups = this.ageGroupSelection.selected;
    if (ageGroups.length === 0 || !this.activeArea) {
      this.barChartProps.data = [];
      this.lineChartProps.data = [];
      this.ageTreeProps.data = [];
      this.forceDiagramReload();
      return;
    }
    ageGroups = sortBy(ageGroups, 'fromAge');
    this.populationService.getPopulationData(this.activeArea.id, { genders: genders }).subscribe( popData => {
      this.populationService.getPopulationData(this.activeArea!.id, { prognosis: this.activePrognosis?.id, genders: genders }).subscribe(progData => {
        const data = popData.concat(progData);
        if (data.length === 0) return;
        const years = [... new Set(data.map(d => d.year))].sort();
        let stackedData: StackedData[] = [];
        let ageTreeData: Record<number, AgeTreeData[]> = {}
        const labels = this.ageGroupSelection.selected.map(ag => ag.label!);
        const colors = this.ageGroupSelection.selected.map(ag => this.ageGroupColors[ag.id!]);
        const maleId = this.genders.find(g => g.name === 'männlich')?.id || 1;
        const femaleId = this.genders.find(g => g.name === 'weiblich')?.id || 2;
        years.forEach(year => {
          let summed: number[] = [];
          let yearAgeData: AgeTreeData[] = [];
          const yearData = data.filter(d => d.year === year)!;
          ageGroups.forEach(ageGroup => {
            const ad = yearData.filter(d => d.agegroup === ageGroup.id);
            yearAgeData.push({
              male: ad.find(d => d.gender === maleId)?.value || 0,
              fromAge: ageGroup.fromAge,
              toAge: ageGroup.toAge,
              female: ad.find(d => d.gender === femaleId)?.value || 0,
              label: ageGroup.label || ''
            })
            const sum = (ad)? ad.reduce((a, d) => a + d.value, 0): 0;
            summed.push(sum);
          })
          ageTreeData[year] = yearAgeData;
          stackedData.push({
            group: String(year),
            values: summed
          });
        })

        const baseYear = this.realYears![this.realYears!.length - 1];
        const xSeparator = {
          leftLabel: `Realdaten`,
          rightLabel: `Prognose (Basisjahr: ${baseYear})`,
          x: String(baseYear),
          highlight: false
        }

        //Stacked Bar Chart
        this.barChartProps.labels = labels;
        this.barChartProps.colors = colors;
        this.barChartProps.title = 'Bevölkerungsentwicklung';
        if (this.selectedGender!.id !== -1)
          this.barChartProps.title += ` (${this.selectedGender!.name})`;
        this.barChartProps.subtitle = this.activeArea?.properties.label!;
        this.barChartProps.xSeparator = xSeparator;
        this.barChartProps.data = stackedData;

        // Line Chart
        let first = stackedData[0].values;
        let relData = stackedData.map(d => { return {
          group: d.group,
          values: d.values.map((v, i) => 100 * v / first[i] )
        }})
        let max = Math.max(...relData.map(d => Math.max(...d.values))),
          min = Math.min(...relData.map(d => Math.min(...d.values)));
        this.lineChartProps.labels = labels;
        this.lineChartProps.colors = colors;
        this.lineChartProps.title = 'relative Altersgruppenentwicklung';
        if (this.selectedGender!.id !== -1)
          this.lineChartProps.title += ` (${this.selectedGender!.name})`;
        this.lineChartProps.subtitle = this.activeArea?.properties.label!;
        this.lineChartProps.min = Math.floor(min / 10) * 10;
        this.lineChartProps.max = Math.ceil(max / 10) * 10;
        this.lineChartProps.xSeparator = xSeparator;
        this.lineChartProps.data = relData;

        this.ageTreeProps.title = 'Bevölkerungspyramide';
        this.ageTreeProps.subtitle = `${this.activeArea?.properties.label!} ${this.year}`;
        this.ageTreeProps.data = ageTreeData;

        this.forceDiagramReload();
      })
    })
  }

  forceDiagramReload(): void {
    // workaround to force redraw of diagram by triggering ngIf wrapper
    const _prev = this.selectedTab;
    this.selectedTab = -1;
    setTimeout(() => {  this.selectedTab = _prev; }, 1);
  }

  someAgeGroupsChecked(): boolean {
    if (!this.ageGroups) return false;
    return this.ageGroupSelection.selected.length > 0 && !this.allAgeGroupsChecked;
  }

  updateGroupsChecked(): void {
    this.allAgeGroupsChecked = this.ageGroupSelection.selected.length === this.ageGroups.length;
    this.patchUserAgeGroupSelection();
    this.updateMap();
    this.updateDiagrams();
  }

  setAllAgeGroupsChecked(check: boolean): void {
    this.allAgeGroupsChecked = check;
    this.ageGroups.forEach(ag => {
      if (check)
        this.ageGroupSelection.select(ag)
      else
        this.ageGroupSelection.deselect(ag)
    });
    this.patchUserAgeGroupSelection();
    this.updateMap();
    this.updateDiagrams();
  }

  patchUserAgeGroupSelection(): void {
    const ageGroupIds = this.ageGroupSelection.selected.map(ag => ag.id);
    this.cookies.set('pop-ageGroups', ageGroupIds);
  }

  updateMapDescription(): void {
    let description = '';
    if (!this.activeLevel)
      description = 'Bitte Gebietseinheit wählen';
    else {
      const genderDesc = `Geschlecht: ${this.selectedGender?.name || '-'}`;
      const ageGroupDesc = `${(this.ageGroupSelection.selected.length == this.ageGroups.length)? 'alle' : this.ageGroupSelection.selected.length === 0? 'keine': 'ausgewählte'} Altersgruppen`;
      const progDesc = (this.realYears?.indexOf(this.year) === -1)? `${this.activePrognosis?.name} `: '';
      description = `Bevölkerungsentwicklung für Gebietseinheit ${this.activeLevel.name} | ${progDesc}${this.year} <br>` +
                    `${genderDesc} | ${ageGroupDesc}`;
    }
    this.mapControl!.mapDescription = description;
  }

  ngOnDestroy(): void {
    if (this.populationLayer)
      this.mapControl?.removeLayer(this.populationLayer.id!);
    if (this.legendGroup)
      this.mapControl?.removeGroup(this.legendGroup.id!)
    this.subscriptions.forEach(subscription => subscription.unsubscribe());
  }
}
