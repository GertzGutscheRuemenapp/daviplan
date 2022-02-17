import { Component, AfterViewInit, ViewChild, TemplateRef, OnDestroy } from '@angular/core';
import { MapControl, MapService } from "../../../map/map.service";
import { StackedData } from "../../../diagrams/stacked-barchart/stacked-barchart.component";
import { MultilineChartComponent } from "../../../diagrams/multiline-chart/multiline-chart.component";
import { Observable, Subscription } from "rxjs";
import { BreakpointObserver, Breakpoints } from "@angular/cdk/layout";
import { map, shareReplay } from "rxjs/operators";
import { MatDialog } from "@angular/material/dialog";
import { ConfirmDialogComponent } from "../../../dialogs/confirm-dialog/confirm-dialog.component";
import { PopulationService } from "../population.service";
import { Area, AreaLevel, Gender, Layer, LayerGroup } from "../../../rest-interfaces";
import { AgeGroup } from "../../administration/project-definition/project-definition.component";

export const mockdata: StackedData[] = [
  { group: '2000', values: [200, 300, 280] },
  { group: '2001', values: [190, 310, 290] },
  { group: '2002', values: [192, 335, 293] },
  { group: '2003', values: [195, 340, 295] },
  { group: '2004', values: [189, 342, 293] },
  { group: '2005', values: [182, 345, 300] },
  { group: '2006', values: [176, 345, 298] },
  { group: '2007', values: [195, 330, 290] },
  { group: '2008', values: [195, 340, 295] },
  { group: '2009', values: [192, 335, 293] },
  { group: '2010', values: [195, 340, 295] },
  { group: '2012', values: [189, 342, 293] },
  { group: '2013', values: [200, 300, 280] },
  { group: '2014', values: [195, 340, 295] },
]

@Component({
  selector: 'app-pop-development',
  templateUrl: './pop-development.component.html',
  styleUrls: ['./pop-development.component.scss']
})
export class PopDevelopmentComponent implements AfterViewInit, OnDestroy {
  @ViewChild('lineChart') lineChart?: MultilineChartComponent;
  @ViewChild('ageGroupTemplate') ageGroupTemplate!: TemplateRef<any>;
  subscriptions: Subscription[] = [];
  populationLayer?: Layer;
  legendGroup?: LayerGroup;
  compareYears = false;
  areaLevels: AreaLevel[] = [];
  areas: Area[] = [];
  realYears?: number[];
  prognosisYears?: number[];
  genders: Gender[] = [];
  ageGroups: AgeGroup[] = [];
  mapControl?: MapControl;
  activeLevel?: AreaLevel;
  activeArea?: Area;
  data: StackedData[] = mockdata;
  year: number = 0;
  labels: string[] = ['65+', '19-64', '0-18'];
  xSeparator = {
    leftLabel: $localize`Realdaten`,
    rightLabel: $localize`Prognose (Basisjahr: 2003)`,
    x: '2003',
    highlight: false
  }
  isSM$: Observable<boolean> = this.breakpointObserver.observe('(max-width: 50em)')
    .pipe(
      map(result => result.matches),
      shareReplay()
    );

  constructor(private breakpointObserver: BreakpointObserver, private mapService: MapService, private dialog: MatDialog,
              private populationService: PopulationService) {
  }

  ngAfterViewInit(): void {
    this.mapControl = this.mapService.get('population-map');
    this.mapControl.mapDescription = 'Bevölkerungsentwicklung für [ausgewählte Gebietseinheit] | [ausgewähltes Prognoseszenario] | <br> Geschlecht: [ausgewähltes Geschlecht | [ausgewählte Altersgruppen] ';
    let first = mockdata[0].values;
    let relData = mockdata.map(d => { return {
      group: d.group,
      values: d.values.map((v, i) => Math.round(10000 * v / first[i]) / 100 )
    }})
    let max = Math.max(...relData.map(d => Math.max(...d.values))),
        min = Math.min(...relData.map(d => Math.min(...d.values)));
    this.lineChart!.min = Math.floor(min / 10) * 10;
    this.lineChart!.max = Math.ceil(max / 10) * 10;
    this.lineChart?.draw(relData);
    if (this.populationService.isReady)
      this.initData();
    else {
      this.populationService.ready.subscribe(r => {
        this.initData();
      });
    }
    this.legendGroup = this.mapControl.addGroup({
      name: 'Bevölkerungsentwicklung',
      order: -1
    }, false)
  }

  initData(): void {
    this.populationService.realYears$.subscribe( years => {
      this.realYears = years;
      this.year = this.realYears[0];
      this.setSlider();
    })
    this.populationService.prognosisYears$.subscribe( years => {
      this.prognosisYears = years;
      this.setSlider();
    })
    this.populationService.genders$.subscribe(genders => {
      this.genders = genders;
    })
    this.populationService.areaLevels$.subscribe(areaLevels => {
      this.areaLevels = areaLevels;
    })
    this.populationService.ageGroups$.subscribe(ageGroups => {
      this.ageGroups = ageGroups;
    })
    this.subscriptions.push(this.populationService.timeSlider!.valueChanged.subscribe(year => {
      this.year = year;
      this.updateMap();
    }))
  }

  setSlider(): void {
    if (!(this.realYears && this.prognosisYears)) return;
    let slider = this.populationService.timeSlider!;
    slider.prognosisStart = this.prognosisYears[0] || 0;
    slider.years = this.realYears.concat(this.prognosisYears);
    slider.value = this.realYears[0];
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
    this.populationService.getAreas(this.activeLevel!.id).subscribe(areas => {
      this.areas = areas;
      this.activeArea = undefined;
      this.updateMap();
    });
  }

  updateMap(): void {
    if(!this.activeLevel) return;
    this.populationService.getAreaPopulation(this.activeLevel.id, this.year).subscribe( popData => {
      if (this.populationLayer)
        this.mapControl?.removeLayer(this.populationLayer.id!)
      this.populationLayer = this.mapControl?.addLayer({
          order: 0,
          type: 'vector',
          group: this.legendGroup?.id,
          name: this.activeLevel!.name,
          description: this.activeLevel!.name,
          opacity: 1,
          symbol: {
            strokeColor: 'grey',
            fillColor: 'yellow',
            symbol: 'line'
          },
          labelField: 'value'
        },
        {
          visible: true,
          tooltipField: 'description',
          mouseOver: {
            strokeColor: 'blue'
          }
        });
      this.areas.forEach(area => {
        const data = popData.find(d => d.areaId == area.id);
        area.properties.value = (data)? Math.round(data.value): 0;
        area.properties.description = `<b>${area.properties.label}</b><br>Bevölkerung: ${area.properties.value}`
      })
      // ToDo: move wkt parsing to populationservice, is done on every change year/level atm (expensive)
      this.mapControl?.addWKTFeatures(this.populationLayer!.id!, this.areas, true);
    })
  }

  ngOnDestroy(): void {
    this.subscriptions.forEach(subscription => subscription.unsubscribe());
  }
}
