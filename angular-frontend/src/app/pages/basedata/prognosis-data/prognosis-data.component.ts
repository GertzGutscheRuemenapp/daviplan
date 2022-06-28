import { AfterViewInit, Component, OnDestroy, TemplateRef, ViewChild } from '@angular/core';
import { MapControl, MapService } from "../../../map/map.service";
import {
  Area,
  AreaLevel,
  Population,
  Year,
  Prognosis,
  ExtLayer,
  ExtLayerGroup,
  Gender,
  AgeGroup, PopEntry, DemandRateSet
} from "../../../rest-interfaces";
import { InputCardComponent } from "../../../dash/input-card.component";
import { SelectionModel } from "@angular/cdk/collections";
import { SettingsService } from "../../../settings.service";
import { RestAPI } from "../../../rest-api";
import { HttpClient } from "@angular/common/http";
import { RemoveDialogComponent } from "../../../dialogs/remove-dialog/remove-dialog.component";
import { MatDialog } from "@angular/material/dialog";
import { PopulationService } from "../../population/population.service";
import { sortBy } from "../../../helpers/utils";
import { AgeTreeComponent, AgeTreeData } from "../../../diagrams/age-tree/age-tree.component";
import * as d3 from "d3";
import { FormBuilder, FormControl, FormGroup } from "@angular/forms";
import { ConfirmDialogComponent } from "../../../dialogs/confirm-dialog/confirm-dialog.component";
import { BehaviorSubject } from "rxjs";
import * as fileSaver from "file-saver";
import { SimpleDialogComponent } from "../../../dialogs/simple-dialog/simple-dialog.component";
import { MapLayer, MapLayerGroup, VectorLayer } from "../../../map/layers";

@Component({
  selector: 'app-prognosis-data',
  templateUrl: './prognosis-data.component.html',
  styleUrls: ['./prognosis-data.component.scss','../real-data/real-data.component.scss']
})
export class PrognosisDataComponent implements AfterViewInit, OnDestroy {
  @ViewChild('yearCard') yearCard?: InputCardComponent;
  @ViewChild('ageTree') ageTree?: AgeTreeComponent;
  @ViewChild('propertiesEdit') propertiesEdit?: TemplateRef<any>;
  @ViewChild('propertiesCard') propertiesCard?: InputCardComponent;
  @ViewChild('dataTemplate') dataTemplate?: TemplateRef<any>;
  @ViewChild('fileUploadTemplate') fileUploadTemplate?: TemplateRef<any>;
  isLoading$ = new BehaviorSubject<boolean>(false);
  mapControl?: MapControl;
  layerGroup?: MapLayerGroup;
  activePrognosis?: Prognosis;
  genders: Gender[] = [];
  ageGroups: AgeGroup[] = [];
  years: Year[] = [];
  yearSelection = new SelectionModel<number>(true);
  prognoses: Prognosis[] = [];
  prognosisYears: number[] = [];
  populations: Population[] = [];
  popLevel?: AreaLevel;
  popEntries: Record<number, PopEntry[]> = {};
  popLevelMissing = false;
  defaultPopLevel?: AreaLevel;
  areas: Area[] = [];
  previewYear?: Year;
  previewArea?: Area;
  previewLayer?: VectorLayer;
  dataColumns: string[] = [];
  dataRows: any[][] = [];
  dataYear?: Year;
  propertiesForm: FormGroup;
  file?: File;
  uploadErrors: any = {};

  constructor(private mapService: MapService, private settings: SettingsService, private dialog: MatDialog,
              private rest: RestAPI, private http: HttpClient, public popService: PopulationService, private formBuilder: FormBuilder) {
    this.propertiesForm = this.formBuilder.group({
      name: new FormControl(''),
      description: new FormControl('')
    });
  }

  // ToDo: shares a lot of Code with real-data-component, at least the map view should be seperated into reusable view
  ngAfterViewInit(): void {
    this.mapControl = this.mapService.get('base-prog-data-map');
    this.layerGroup = new MapLayerGroup('Bevölkerungsentwicklung (Prognose)', { order: -1 })
    this.mapControl.addGroup(this.layerGroup, false);
    this.popService.getAreaLevels({ reset: true }).subscribe(areaLevels => {
      this.defaultPopLevel = areaLevels.find(al => al.isDefaultPopLevel);
      this.popLevel = areaLevels.find(al => al.isPopLevel);
      if (this.popLevel) {
        this.popService.getAreas(this.popLevel.id, { reset: true }).subscribe(areas => this.areas = areas);
      }
      else
        this.popLevelMissing = true;
    })
    this.fetchData();
    this.setupYearCard();
    this.setupPropertiesCard();
  }

  fetchData(): void {
    this.previewYear = undefined;
    this.previewArea = undefined;
    this.ageTree?.clear();
    this.updatePreview();
    this.dataColumns = ['Gebiet']
    this.popService.getGenders().subscribe(genders => {
      this.genders = genders;
      this.popService.getAgeGroups().subscribe(ageGroups => {
        this.genders.forEach(gender => {
          this.dataColumns = this.dataColumns.concat(ageGroups.map(ag => `${ag.label} (${gender.name})`));
        })
        this.ageGroups = sortBy(ageGroups, 'fromAge');
        this.http.get<Year[]>(this.rest.URLS.years).subscribe(years => {
          this.years = [];
          this.prognosisYears = [];
          years.forEach(year => {
            if (year.isPrognosis) {
              this.prognosisYears.push(year.year);
            }
            this.years.push(year);
          })
          this.popService.fetchPopulations(true).subscribe(populations => {
            this.populations = populations;
            this.popService.fetchPrognoses().subscribe(prognoses => this.prognoses = prognoses);
          });
        });
      })
    });
  }

  onPrognosisChange() {
    // this.previewArea = undefined;
    this.ageTree?.clear();
    this.updatePreview();
  }

  setupYearCard(): void {
    this.yearCard?.dialogOpened.subscribe(ok => {
      this.yearSelection.clear();
      this.prognosisYears.forEach(year => this.yearSelection.select(year));
    })
    this.yearCard?.dialogConfirmed.subscribe((ok)=>{
      this.yearCard?.setLoading(true);
      const progYears = this.yearSelection.selected;
      this.http.post<Year[]>(`${this.rest.URLS.years}set_prognosis_years/`, { years: progYears }
      ).subscribe(years => {
        this.years.forEach(y => y.isPrognosis = false);
        this.prognosisYears = [];
        years.forEach(ry => {
          if (ry.isPrognosis) this.prognosisYears.push(ry.year);
          const year = this.years.find(y => y.id === ry.id);
          if (year)
            Object.assign(year, ry);
        })
        this.prognosisYears.sort();
        this.previewYear = undefined;
        this.dataYear = undefined;
        this.ageTree?.clear();
        this.updatePreview();
        this.yearCard?.closeDialog(true);
      });
    })
  }

  updatePreview(): void {
    if (this.previewLayer) {
      this.layerGroup?.removeLayer(this.previewLayer);
      this.previewLayer = undefined;
    }
    if (!this.activePrognosis) return;
    const population = this.populations.find(p => p.year === this.previewYear!.id && p.prognosis === this.activePrognosis!.id);
    if (!population) return;
    this.popService.getPopEntries(population.id).subscribe(popEntries => {
      this.popEntries = {};
      popEntries.forEach(pe => {
        if (!this.popEntries[pe.area]) this.popEntries[pe.area] = [];
        this.popEntries[pe.area].push(pe);
      })
      let max = 1000;
      this.dataRows = [];
      this.areas.forEach(area => {
        const entries = this.popEntries[area.id];
        // map data
        const value = entries.reduce((p: number, e: PopEntry) => p + e.value, 0);
        area.properties.value = value;
        area.properties.description = `<b>${area.properties.label}</b><br>Bevölkerung: ${area.properties.value}`
        max = Math.max(max, value);
      })
      const radiusFunc = d3.scaleLinear().domain([0, max]).range([5, 50]);
      this.previewLayer = new VectorLayer(this.popLevel!.name, {
        order: 0,
        description: this.popLevel!.name,
        opacity: 1,
        style: {
          strokeColor: 'white',
          fillColor: 'rgba(165, 15, 21, 0.9)',
          symbol: 'circle'
        },
        labelField: 'value',
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
        showLabel: true,
        valueMapping: {
          field: 'value',
          radius: radiusFunc
        }
      });
      this.previewLayer.addFeatures(this.areas, {
        properties: 'properties',
        geometry: 'centroid',
        zIndex: 'value'
      });
      if (this.previewArea)
        this.previewLayer?.selectFeatures([this.previewArea.id], { silent: true });
      this.updateAgeTree();
      this.previewLayer!.featureSelected?.subscribe(evt => {
        if (evt.selected) {
          this.previewArea = this.areas.find(area => area.id === evt.feature.get('id'));
        }
        else {
          this.previewArea = undefined;
        }
        this.updateAgeTree();
      })
    })
  }

  deleteData(year: Year): void {
    if (!year.hasPrognosisData) return;
    const dialogRef = this.dialog.open(RemoveDialogComponent, {
      width: '400px',
      data: {
        title: 'Entfernung von Prognosedaten',
        message: 'Sollen die Prognosedaten dieses Jahres wirklich entfernt werden?',
        confirmButtonText: 'Prognosedaten entfernen',
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
          year.hasPrognosisData = false;
          if (year === this.previewYear) {
            this.previewYear = undefined;
            this.ageTree?.clear();
            this.dataRows = [];
            this.updatePreview();
          }
        },(error) => {
          console.log('there was an error sending the query', error);
        });
      }
    });
  }

  onAreaChange(): void {
    if (!this.previewLayer) return;
    this.previewLayer?.selectFeatures([this.previewArea!.id], { silent: true, clear: true });
    this.updateAgeTree();
  }

  updateAgeTree(): void {
    this.ageTree?.clear();
    if (!this.previewArea || !this.previewYear) return;
    const areaData = this.popEntries[this.previewArea.id];
    const maleId = this.genders.find(g => g.name === 'männlich')?.id || 1;
    const femaleId = this.genders.find(g => g.name === 'weiblich')?.id || 2;
    const ageTreeData: AgeTreeData[] = [];
    this.ageGroups.forEach(ageGroup => {
      const ad = areaData.filter(d => d.ageGroup === ageGroup.id);
      ageTreeData.push({
        male: ad.find(d => d.gender === maleId)?.value || 0,
        fromAge: ageGroup.fromAge,
        toAge: ageGroup.toAge,
        female: ad.find(d => d.gender === femaleId)?.value || 0,
        label: ageGroup.label || ''
      })
    })
    this.ageTree!.subtitle = `${this.previewArea?.properties.label!} ${this.previewYear?.year}`;
    this.ageTree!.draw(ageTreeData);
  }

  setupPropertiesCard(): void {
    this.propertiesCard?.dialogOpened.subscribe(ok => {
      this.propertiesForm.reset({
        name: this.activePrognosis?.name,
        description: this.activePrognosis?.description,
      });
    })
    this.propertiesCard?.dialogConfirmed.subscribe((ok)=>{
      this.propertiesForm.setErrors(null);
      this.propertiesForm.markAllAsTouched();
      if (this.propertiesForm.invalid) return;
      let attributes: any = {
        name: this.propertiesForm.value.name,
        description: this.propertiesForm.value.description
      }
      this.propertiesCard?.setLoading(true);
      this.http.patch<DemandRateSet>(`${this.rest.URLS.prognoses}${this.activePrognosis?.id}/`, attributes
      ).subscribe(prognosis => {
        Object.assign(this.activePrognosis!, prognosis);
        this.propertiesCard?.closeDialog(true);
      },(error) => {
        // ToDo: set specific errors to fields
        this.propertiesForm.setErrors(error.error);
        this.propertiesCard?.setLoading(false);
      });
    })
  }

  createPrognosis(): void {
    let dialogRef = this.dialog.open(ConfirmDialogComponent, {
      panelClass: 'absolute',
      width: '300px',
      disableClose: true,
      data: {
        title: 'Neue Nachfragevariante',
        template: this.propertiesEdit,
        closeOnConfirm: false
      }
    });
    dialogRef.afterOpened().subscribe(ok => {
      this.propertiesForm.reset();
    });
    dialogRef.componentInstance.confirmed.subscribe(() => {
      this.propertiesForm.setErrors(null);
      // display errors for all fields even if not touched
      this.propertiesForm.markAllAsTouched();
      if (this.propertiesForm.invalid) return;
      let attributes: any = {
        name: this.propertiesForm.value.name,
        description: this.propertiesForm.value.description || ''
      }
      dialogRef.componentInstance.isLoading$.next(true);
      this.http.post<Prognosis>(this.rest.URLS.prognoses, attributes
      ).subscribe(prognosis => {
        this.prognoses.push(prognosis);
        this.activePrognosis = prognosis;
        this.onPrognosisChange();
        dialogRef.close();
      },(error) => {
        this.propertiesForm.setErrors(error.error);
        dialogRef.componentInstance.isLoading$.next(false);
      });
    });
  }

  removePrognosis(): void {
    if (!this.activePrognosis)
      return;
    const dialogRef = this.dialog.open(RemoveDialogComponent, {
      width: '400px',
      data: {
        title: $localize`Die Prognosevariante wirklich entfernen?`,
        confirmButtonText: $localize`Variante entfernen`,
        message: 'Es werden auch alle bereits eingespielten Daten der Variante entfernt.',
        value: this.activePrognosis.name
      }
    });
    dialogRef.afterClosed().subscribe((confirmed: boolean) => {
      if (confirmed) {
        this.http.delete(`${this.rest.URLS.prognoses}${this.activePrognosis?.id}/`
        ).subscribe(() => {
          const idx = this.prognoses.indexOf(this.activePrognosis!);
          if (idx > -1) {
            this.prognoses.splice(idx, 1);
          }
          this.activePrognosis = undefined;
        },(error) => {
          console.log('there was an error sending the query', error);
        });
      }
    });
  }

  showDataTable(): void {
    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      panelClass: 'absolute',
      width: '400',
      disableClose: false,
      autoFocus: false,
      data: {
        title: `Datentabelle Realdaten`,
        template: this.dataTemplate,
        hideConfirmButton: true,
        cancelButtonText: 'OK'
      }
    });
    dialogRef.afterOpened().subscribe(()=> this.updateTableData())
  }

  updateTableData(): void {
    this.dataRows = [];
    if (!this.dataYear) return;
    const population = this.populations.find(p => p.year === this.dataYear!.id && p.prognosis === this.activePrognosis!.id);
    if (!population) return;
    let rows: any[][] = [];
    this.isLoading$.next(true);
    this.popService.getPopEntries(population.id).subscribe(popEntries => {
      this.areas.forEach(area => {
        const entries = popEntries.filter(e => e.area === area.id);
        const row: any[] = [area.properties.label]
        if (!entries) return;
        // table data
        this.genders.forEach(gender => {
          const gEntries = entries.filter(e => e.gender === gender.id);
          this.ageGroups.forEach(ageGroup => {
            const entry = gEntries.find(e => e.ageGroup === ageGroup.id);
            row.push(entry?.value || 0);
          })
        })
        rows.push(row);
      })
      this.dataRows = rows;
      this.isLoading$.next(false);
    })
  }

  downloadTemplate(): void {
    if (!(this.popLevel && this.activePrognosis)) return;
    const url = `${this.rest.URLS.popEntries}create_template/`;
    const dialogRef = SimpleDialogComponent.show('Bereite Template vor. Bitte warten', this.dialog, { showAnimatedDots: true });
    this.http.post(url, { area_level: this.popLevel.id, years: this.prognosisYears, prognosis: this.activePrognosis.id }, { responseType: 'blob' }).subscribe((res:any) => {
      const blob: any = new Blob([res],{ type:'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
      fileSaver.saveAs(blob, 'prognosedaten-template.xlsx');
      dialogRef.close();
    },(error) => {
      dialogRef.close();
    });
  }

  uploadTemplate(): void {
    if (!this.activePrognosis) return;
    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      width: '450px',
      data: {
        title: `Template hochladen`,
        confirmButtonText: 'Datei hochladen',
        template: this.fileUploadTemplate
      }
    });
    dialogRef.componentInstance.confirmed.subscribe((confirmed: boolean) => {
      if (!this.file)
        return;
      const formData = new FormData();
      formData.append('excel_file', this.file);
      formData.append('prognosis', this.activePrognosis!.id.toString());
      const dialogRef2 = SimpleDialogComponent.show(
        'Das Template wird hochgeladen. Die Bevölkerungsdaten werden auf das Raster disaggregiert und anschließend auf die vorhandenen Gebiete aggregiert.<br><br>' +
        'Dies kann einige Minuten dauern. Bitte warten', this.dialog, { showAnimatedDots: true, width: '400px' });
      const url = `${this.rest.URLS.popEntries}upload_template/`;
      this.http.post(url, formData).subscribe(res => {
        this.popService.reset();
        this.fetchData();
        dialogRef.close();
        dialogRef2.close();
      }, error => {
        this.uploadErrors = error.error;
        dialogRef.componentInstance.isLoading$.next(false);
        dialogRef2.close();
      });
    });
    dialogRef.afterClosed().subscribe(ok => {
      this.uploadErrors = {};
    })
  }

  setFiles(event: Event){
    const element = event.currentTarget as HTMLInputElement;
    const files: FileList | null = element.files;
    this.file =  (files && files.length > 0)? files[0]: undefined;
  }

  ngOnDestroy(): void {
    this.mapControl?.destroy();
  }
}
