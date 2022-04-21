import { AfterViewInit, Component, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { MapControl, MapService } from "../../../map/map.service";
import { environment } from "../../../../environments/environment";
import { PopulationService } from "../../population/population.service";
import {
  Area,
  AreaLevel,
  Infrastructure,
  Layer,
  LayerGroup,
  PopEntry,
  Population,
  Year
} from "../../../rest-interfaces";
import { SettingsService } from "../../../settings.service";
import { SelectionModel } from "@angular/cdk/collections";
import { RestAPI } from "../../../rest-api";
import { HttpClient } from "@angular/common/http";
import { RemoveDialogComponent } from "../../../dialogs/remove-dialog/remove-dialog.component";
import { MatDialog } from "@angular/material/dialog";
import { InputCardComponent } from "../../../dash/input-card.component";
import * as d3 from "d3";

@Component({
  selector: 'app-real-data',
  templateUrl: './real-data.component.html',
  styleUrls: ['./real-data.component.scss']
})
export class RealDataComponent implements AfterViewInit, OnDestroy {
  @ViewChild('yearCard') yearCard?: InputCardComponent;
  backend: string = environment.backend;
  mapControl?: MapControl;
  years: Year[] = [];
  popLevel?: AreaLevel;
  popLevelMissing = false;
  defaultPopLevel?: AreaLevel;
  areas: Area[] = [];
  realYears: number[] = [];
  previewYear?: Year;
  previewArea?: Area;
  previewLayer?: Layer;
  legendGroup?: LayerGroup;
  popEntries: Record<number, PopEntry[]> = {};
  populations: Population[] = [];
  // dataYears: number[] = [];
  yearSelection = new SelectionModel<number>(true);
  maxYear = new Date().getFullYear() - 1;

  constructor(private mapService: MapService, public popService: PopulationService, private dialog: MatDialog,
              private settings: SettingsService, private rest: RestAPI, private http: HttpClient) {

  }

  ngAfterViewInit(): void {
    this.popService.getAreaLevels({ reset: true }).subscribe(areaLevels => {
      this.defaultPopLevel = areaLevels.find(al => al.isDefaultPopLevel);
      this.popLevel = areaLevels.find(al => al.isPopLevel);
      if (this.popLevel) {
        this.popService.getAreas(this.popLevel.id, { reset: true }).subscribe(areas => this.areas = areas);
      }
      else
        this.popLevelMissing = true;
    })
    this.mapControl = this.mapService.get('base-real-data-map');
    this.legendGroup = this.mapControl.addGroup({
      name: 'Bevölkerungsentwicklung',
      order: -1
    }, false)
    this.http.get<Year[]>(this.rest.URLS.years).subscribe(years => {
      years.forEach(year => {
        if (year.year > this.maxYear) return;
        if (year.isReal) {
          this.realYears.push(year.year);
        }
        this.years.push(year);
      })
      this.popService.fetchPopulations().subscribe(populations => {
        this.populations = populations;
        /*       this.populations.forEach(population => {
                 const year = this.years.find(y => y.id == population.year);
                 if (year) this.dataYears.push(year.year);
               });*/
        this.setupYearCard();
      });
    });
  }

  setupYearCard(): void {
    this.yearCard?.dialogOpened.subscribe(ok => {
      this.yearSelection.clear();
      this.realYears.forEach(year => this.yearSelection.select(year));
    })
    this.yearCard?.dialogConfirmed.subscribe((ok)=>{
      this.yearCard?.setLoading(true);
      const realYears = this.yearSelection.selected;
      this.http.post<Year[]>(`${this.rest.URLS.years}set_real_years/`, { years: realYears }
      ).subscribe(years => {
        this.years.forEach(y => y.isReal = false);
        this.realYears = [];
        years.forEach(ry => {
          if (ry.isReal) this.realYears.push(ry.year);
          const year = this.years.find(y => y.id === ry.id);
          if (year)
            Object.assign(year, ry);
        })
        this.realYears.sort();
        this.yearCard?.closeDialog(true);
      });
    })
  }

  deleteData(year: Year): void {
    if (!year.hasRealData) return;
    const dialogRef = this.dialog.open(RemoveDialogComponent, {
      width: '350px',
      data: {
        title: 'Entfernung von Realdaten',
        message: 'Sollen die Realdaten dieses Jahres wirklich entfernt werden?',
        confirmButtonText: 'Realdaten entfernen',
        value: year.year
      }
    });
    dialogRef.afterClosed().subscribe((confirmed: boolean) => {
      const population = this.populations.find(p => p.year === year.id);
      if (!population) return;
      if (confirmed) {
        this.http.delete(`${this.rest.URLS.populations}${population.id}/`
        ).subscribe(res => {
          const idx = this.populations.indexOf(population);
          if (idx > -1) this.populations.splice(idx, 1);
          year.hasRealData = false;
        },(error) => {
          console.log('there was an error sending the query', error);
        });
      }
    });
  }

  updatePreview(): void {
    if (!this.previewYear) return;
    if (this.previewLayer) {
      this.mapControl?.removeLayer(this.previewLayer.id!);
      this.previewLayer = undefined;
    }
    const population = this.populations.find(p => p.year === this.previewYear!.id);
    if (!population) return;
    this.popService.getPopEntries(population.id).subscribe(popEntries => {
      this.popEntries = {};
      popEntries.forEach(pe => {
        if (!this.popEntries[pe.area]) this.popEntries[pe.area] = [];
        this.popEntries[pe.area].push(pe);
      })
      let max = 1000;
      this.areas.forEach(area => {
        const entries = this.popEntries[area.id];
        if (!entries) return;
        const value = entries.reduce((p: number, e: PopEntry) => p + e.value, 0);
        area.properties.value = value;
        area.properties.description = `<b>${area.properties.label}</b><br>Bevölkerung: ${area.properties.value}`
        max = Math.max(max, value);
      })
      const radiusFunc = d3.scaleLinear().domain([0, max]).range([5, 50]);
      this.previewLayer = this.mapControl?.addLayer({
          order: 0,
          type: 'vector',
          group: this.legendGroup?.id,
          name: this.popLevel!.name,
          description: this.popLevel!.name,
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
      this.mapControl?.addFeatures(this.previewLayer!.id!, this.areas,
        { properties: 'properties', geometry: 'centroid', zIndex: 'value' });
      // this.populationLayer!.featureSelected?.subscribe(evt => {
      //   if (evt.selected) {
      //     this.activeArea = this.areas.find(area => area.id === evt.feature.get('id'));
      //   }
      //   else {
      //     this.activeArea = undefined;
      //   }
      //   this.cookies.set(`pop-area-${this.activeLevel!.id}`, this.activeArea?.id);
      //   this.updateDiagrams();
      // })
    })
  }

  ngOnDestroy(): void {
    this.mapControl?.destroy();
  }
}
