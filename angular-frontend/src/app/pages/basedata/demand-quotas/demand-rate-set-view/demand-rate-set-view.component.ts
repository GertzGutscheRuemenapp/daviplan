import { AfterViewInit, Component, Input, TemplateRef, ViewChild } from '@angular/core';
import { environment } from "../../../../../environments/environment";
import { AgeGroup, DemandRate, DemandRateSet, Gender } from "../../../../rest-interfaces";
import { TimeSliderComponent } from "../../../../elements/time-slider/time-slider.component";
import { MultilineChartComponent, MultilineData } from "../../../../diagrams/multiline-chart/multiline-chart.component";
import { sortBy } from "../../../../helpers/utils";
import { DemandTypes } from "../../../../rest-interfaces";
import { ConfirmDialogComponent } from "../../../../dialogs/confirm-dialog/confirm-dialog.component";
import { MatDialog } from "@angular/material/dialog";

interface Row {
  ageGroup: AgeGroup,
  entries: Entry[]
}

interface Entry {
  gender: Gender,
  value: number | undefined
}

@Component({
  selector: 'app-demand-rate-set-view',
  templateUrl: './demand-rate-set-view.component.html',
  styleUrls: ['./demand-rate-set-view.component.scss']
})
export class DemandRateSetViewComponent implements AfterViewInit {
  @Input() edit: boolean = false;
  @Input() chartHeight = 300;
  @Input() inPlace = false;
  @ViewChild('timeSlider') timeSlider?: TimeSliderComponent;
  @ViewChild('yearChart') yearChart!: MultilineChartComponent;
  @ViewChild('ageGroupChart') ageGroupChart!: MultilineChartComponent;
  @ViewChild('copyYearData') copyYearDataTemlate!: TemplateRef<any>;
  backend: string = environment.backend;
  year?: number;
  selectedAgeGroup?: AgeGroup;
  unit: string = '';
  demandTypeLabel: string = '';
  maxValue: number = 100;
  copyFromYear: number = 0;
  copyToYear: number = 0;
  _demandType?: 1 | 2 | 3;
  _years: number[] = [];
  _demandRateSet?: DemandRateSet;
  _genders: Gender[] = [];
  _ageGroups: AgeGroup[] = [];
  // columns: string[] = [];
  yearDemandRates: DemandRate[] = [];
  rows: Row[] = [];
  genderColors: string[] = [];

  @Input() set years(years: number[]) {
    this._years = years;
    if (years.length > 0) this.year = years[0];
    this.init();
  }

  @Input() set demandRateSet(set: DemandRateSet | undefined) {
    // deep clone
    if (!this.inPlace && set)
      set = JSON.parse(JSON.stringify(set));
    this._demandRateSet = set;
    this.init();
  }

  @Input() set genders(genders: Gender[]) {
    this._genders = genders;
    if (genders.length > 0) {
      this.genderColors = [];
      genders.forEach(gender => {
        this.genderColors.push(
          (gender.name === 'männlich') ? '#2c81ff' :
            (gender.name === 'weiblich') ? '#ee4a4a' : 'black')
      })
    }
    this.init();
  }

  @Input() set ageGroups(ageGroups: AgeGroup[]) {
    this._ageGroups = ageGroups;
    if (ageGroups.length > 0) this.selectedAgeGroup = ageGroups[0];
    this.init();
  }

  @Input() set demandType(demandType: 1 | 2 | 3) {
    this._demandType = demandType;
    if (demandType) {
      this.unit = (demandType === 1)? '%': '';
      this.demandTypeLabel = DemandTypes[demandType][0];
      this.maxValue = (demandType === 1)? 100: 9999;
    }
    this.init();
  }

  constructor(private dialog: MatDialog) { }

  ngAfterViewInit(): void {
    this.init();
  }

  init(): void {
    if (!this.year || !this._demandRateSet || this._genders.length === 0 ||
      this._ageGroups.length === 0 || !this._demandType)
      return;
    this.setDemandRates();
    this.updateYearDiagram();
    this.updateAgeGroupDiagram();
  }

  /**
   * build table data
   */
  private setDemandRates(): void {
    this.rows = [];
    if(!this._demandRateSet) return;
    // const genderLabels = this._genders.map(gender => gender.name);
    this.yearDemandRates = this._demandRateSet.demandRates.filter(dr => dr.year === this.year) || [];
    // this.columns = [''].concat(genderLabels);
    this._ageGroups.forEach(ageGroup => {
      const groupDemandRates = this.yearDemandRates.filter(dr => dr.ageGroup === ageGroup.id!) || [];
      let entries: Entry[] = [];
      this._genders.forEach(gender => {
        const demandRate = groupDemandRates.find(dr => dr.gender === gender.id);
        const value = demandRate? demandRate.value: undefined;
        entries.push({ gender: gender, value: value})
      })
      this.rows.push({ ageGroup: ageGroup, entries: entries });
    })
  }

  changeYear(year: number | null): void {
    if (year === null) return;
    this.year = year;
    this.setDemandRates();
    this.updateYearDiagram();
  }

  changeDemandRate(value: number, ageGroup: AgeGroup, gender: Gender){
    if (!this.year) return;
    let demandRate = this.yearDemandRates.find(dr => dr.ageGroup === ageGroup.id && dr.gender === gender.id);
    // demandRate is not existing yet
    if (!demandRate)
      demandRate = this.addDemandRate(this.year!, ageGroup, gender);
    demandRate.value = Math.min(Number(value), this.maxValue);
    this.updateYearDiagram();
    if (ageGroup.id === this.selectedAgeGroup?.id)
      this.updateAgeGroupDiagram();
  }

  private addDemandRate(year: number, ageGroup: AgeGroup, gender: Gender): DemandRate {
    let demandRate: DemandRate = {
      year: year,
      ageGroup: ageGroup.id!,
      gender: gender.id
    }
    if (year === this.year)
      this.yearDemandRates.push(demandRate);
    // if demandRate was not found it does not exist in demandRateSet yet either
    this._demandRateSet?.demandRates.push(demandRate);
    return demandRate;
  }

  copyColumn(fromGender: Gender, toGender: Gender, options?: { fromYear?: number, toYear?: number, update?: boolean }): void {
    const fromYear = options?.fromYear || this.year;
    const toYear = options?.toYear || this.year;
    const update = (options?.update !== undefined)? options.update: true;
    let fromYearRates = this._demandRateSet!.demandRates.filter(dr => dr.year === fromYear);
    let toYearRates = this._demandRateSet!.demandRates.filter(dr => dr.year === toYear);
    this._ageGroups.forEach(ageGroup => {
      const fromGroupRates = fromYearRates.filter(dr => dr.ageGroup === ageGroup.id);
      const toGroupRates = toYearRates.filter(dr => dr.ageGroup === ageGroup.id);
      const fromDemandRate = fromGroupRates.find(dr => dr.gender === fromGender.id);
      let toDemandRate = toGroupRates.find(dr => dr.gender === toGender.id);
      const value = fromDemandRate?.value || 0;
      if (!toDemandRate)
        toDemandRate = this.addDemandRate(this.year!, ageGroup, toGender);
      toDemandRate.value = value;
    })
    if (update) {
      this.setDemandRates();
      this.updateYearDiagram();
      this.updateAgeGroupDiagram();
    }
  }

  copyYear(): void {
    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      panelClass: 'absolute',
      autoFocus: false,
      width: '270px',
      data: {
        title: 'Daten übertragen',
        template: this.copyYearDataTemlate,
        closeOnConfirm: true,
        // message: 'Alle Einträge des links ausgewählten Jahres in das Rechte übertragen',
        confirmButtonText: 'Übertragen'
      }
    });
    dialogRef.afterOpened().subscribe(x => {
      this.copyFromYear = this.copyToYear = this.year || 0;
    })
    dialogRef.componentInstance.confirmed.subscribe(() => {
      if (this.copyFromYear === this.copyToYear) return;
      this.copyColumn(this._genders[0], this._genders[0],
        { fromYear: this.copyFromYear, toYear: this.copyToYear, update: false });
      this.copyColumn(this._genders[1], this._genders[1],
        { fromYear: this.copyFromYear, toYear: this.copyToYear, update: false });
      if (this.copyToYear === this.year) {
        this.setDemandRates();
        this.updateYearDiagram();
      }
      this.updateAgeGroupDiagram();
    });
  }

  updateYearDiagram(): void {
    if (!this.yearChart) return;
    this.yearChart.clear();
    if (!this.year) return;
    const max = Math.max(...this.yearDemandRates.map(dr => dr.value || 0), 0);
    this.yearChart.max = Math.min(Math.floor(max / 10) * 10 + 10, this.maxValue)
    const data: MultilineData[] = [];
    this._ageGroups.forEach(ageGroup => {
      const groupRates = sortBy(this.yearDemandRates.filter(dr => dr.ageGroup === ageGroup.id) || [], 'fromAge');
      let values: number[] = [];
      this._genders.forEach(gender => {
        values.push(groupRates.find(dr => dr.gender === gender.id)?.value || 0);
      })
      data.push({
        group: `ab ${ageGroup.fromAge}`,
        values: values
      });
    })
    this.yearChart.colors = this.genderColors;
    this.yearChart.title = `${this.demandTypeLabel} nach Altersgruppen`;
    this.yearChart.subtitle = `im Jahr ${this.year}`;
    this.yearChart.labels = this._genders.map(g => g.name);
    this.yearChart.draw(data);
  }

  updateAgeGroupDiagram(): void {
    if (!this.ageGroupChart) return;
    this.ageGroupChart.clear();
    if (!this.selectedAgeGroup) return;
    const max = Math.max(...this.yearDemandRates.map(dr => dr.value || 0), 0);
    this.ageGroupChart.max = Math.min(Math.floor(max / 10) * 10 + 10, this.maxValue)
    const data: MultilineData[] = [];
    const groupRates = this._demandRateSet?.demandRates.filter(dr => dr.ageGroup === this.selectedAgeGroup!.id) || [];
    this._years.forEach(year => {
      let values: number[] = [];
      const yearRates = groupRates.filter(dr => dr.year === year);
      this._genders.forEach(gender => {
        values.push(yearRates.find(dr => dr.gender === gender.id)?.value || 0);
      })
      data.push({
        group: year.toString(),
        values: values
      });
    })
    this.ageGroupChart.title = this.demandTypeLabel;
    this.ageGroupChart.colors = this.genderColors;
    this.ageGroupChart.subtitle = this.selectedAgeGroup.label || '';
    this.ageGroupChart.labels = this._genders.map(g => g.name);
    this.ageGroupChart.draw(data);
  }
}
