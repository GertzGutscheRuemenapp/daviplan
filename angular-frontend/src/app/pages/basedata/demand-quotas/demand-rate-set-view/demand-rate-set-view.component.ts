import { AfterViewInit, Component, Input, ViewChild } from '@angular/core';
import { environment } from "../../../../../environments/environment";
import { AgeGroup, DemandRate, DemandRateSet, Gender } from "../../../../rest-interfaces";
import { TimeSliderComponent } from "../../../../elements/time-slider/time-slider.component";

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
  @Input() demandTypeLabel: string = '';
  @Input() unit: string = '';
  @Input() edit: boolean = false;
  @ViewChild('timeSlider') timeSlider?: TimeSliderComponent;
  backend: string = environment.backend;
  year?: number;
  _years: number[] = [];
  _demandRateSet?: DemandRateSet;
  _genders: Gender[] = [];
  _ageGroups: AgeGroup[] = [];
  // columns: string[] = [];
  demandRates: DemandRate[] = [];
  rows: Row[] = [];

  @Input() set years(years: number[]) {
    this._years = years;
    if (years.length > 0) this.year = years[0];
    this.setDemandRates();
  }

  @Input() set demandRateSet(set: DemandRateSet | undefined) {
    // deep clone
    if (set)
      set = JSON.parse(JSON.stringify(set));
    this._demandRateSet = set;
    this.setDemandRates();
  }

  @Input() set genders(genders: Gender[]) {
    this._genders = genders;
    this.setDemandRates();
  }

  @Input() set ageGroups(ageGroups: AgeGroup[]) {
    this._ageGroups = ageGroups;
    this.setDemandRates();
  }

  constructor() { }

  ngAfterViewInit(): void { }

  /**
   * build table data
   */
  private setDemandRates(): void {
    this.rows = [];
    if (!this.year || !this._demandRateSet || this._genders.length === 0 || this._ageGroups.length === 0 ) {
      this.demandRates = [];
      return;
    }
    // const genderLabels = this._genders.map(gender => gender.name);
    const yearDemandRates = this._demandRateSet.demandRates.filter(dr => dr.year === this.year) || [];
    // this.columns = [''].concat(genderLabels);
    this._ageGroups.forEach(ageGroup => {
      const groupDemandRates = yearDemandRates.filter(dr => dr.ageGroup === ageGroup.id!) || [];
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
  }
}
