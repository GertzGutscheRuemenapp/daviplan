import { AfterViewInit, Component, EventEmitter, Input, OnInit, Output, ViewChild } from '@angular/core';
import { Infrastructure, Place, Scenario, Service } from "../../../rest-interfaces";
import { PlanningService } from "../planning.service";
import { TimeSliderComponent } from "../../../elements/time-slider/time-slider.component";
import { forkJoin, Observable } from "rxjs";
import { map } from "rxjs/operators";
import { FilterTableComponent, FilterColumn } from "../../../elements/filter-table/filter-table.component";

@Component({
  selector: 'app-place-filter',
  templateUrl: './place-filter.component.html',
  styleUrls: ['./place-filter.component.scss']
})
export class PlaceFilterComponent implements AfterViewInit {
  @Output() filtersChanged = new EventEmitter<FilterColumn[]>();
  @Input() infrastructure!: Infrastructure;
  @Input() services?: Service[];
  @Input() places!: Place[];
  @Input() scenario!: Scenario;
  @Input() year?: number;
  @Input() filterColumns?: FilterColumn[];
  @ViewChild('timeSlider') timeSlider?: TimeSliderComponent;
  @ViewChild('filterTable') filterTable?: FilterTableComponent;
  realYears?: number[];
  prognosisYears?: number[];
  public columns: FilterColumn[] = [];
  public rows: any[][] = [];
  private capacities: Record<number, Record<string, number>> = {};

  constructor(public planningService: PlanningService) {
  }

  ngAfterViewInit(): void {
    if (!this.services) this.services = this.infrastructure.services;
    this.columns = this.getColumns();
    this.planningService.getRealYears().subscribe( years => {
      this.realYears = years;
      this.planningService.getPrognosisYears().subscribe( years => {
        this.prognosisYears = years;
        if (!this.year) this.year = this.realYears![0];
        this.setSlider();
        this.updateData();
      })
    })
    this.timeSlider?.valueChanged.subscribe(value => {
      if (value) {
        this.year = value;
        this.updateData();
      }
    })
  }

  updateData(): void {
    let observables: Observable<any>[] = [];
    if (!this.capacities[this.year!]){
      let placeCaps: Record<string, number> = {};
      this.capacities[this.year!] = placeCaps;
      this.services?.forEach(service => {
        observables.push(this.planningService.getCapacities(this.year!, service.id).pipe(map(capacities => {
          this.places.forEach(place => {
            const key = `${service.id}-${place.id}`;
            placeCaps[key] = capacities.find(c => c.place === place.id)?.capacity || 0;
          })
        })));
      });

      forkJoin(...observables).subscribe(() => {
        this.rows = this.placesToRows(this.places);
      })
    }
    else
      this.rows = this.placesToRows(this.places);
  }

  getColumns(): FilterColumn[] {
    let columns: FilterColumn[] = [{ name: 'Name', type: 'STR' }];
    this.services!.forEach(service => {
      const column: FilterColumn = {
        name: `Kapazität ${service.name}`,
        service: service,
        type: 'NUM',
        unit: service.capacityPluralUnit
      };
      const filterInput = this.filterColumns?.find(c => c.service === service);
      if (filterInput)
        column.filter = Object.assign(Object.create(Object.getPrototypeOf(filterInput.filter)), filterInput.filter);
      columns.push(column);
    })
    this.infrastructure.placeFields?.forEach(field => {
      const column: FilterColumn = {
        name: field.name,
        attribute: field.name,
        type: field.fieldType.ftype,
        classes: field.fieldType.classification?.map(c => c.value),
        unit: field.unit
      };
      const filterInput = this.filterColumns?.find(c => c.attribute === field.name);
      if (filterInput)
        column.filter = Object.assign(Object.create(Object.getPrototypeOf(filterInput.filter)), filterInput.filter);
      columns.push(column);
    })
    return columns;
  }

  placesToRows(places: Place[]): any[][]{
    const rows: any[][] = [];
    places.forEach(place => {
      const capValues = this.services!.map(service => {
        const key = `${service.id}-${place.id}`;
        return this.capacities[this.year!][key];
      })
      const values: any[] = this.infrastructure.placeFields!.map(field => {
        return place.properties.attributes[field.name] || '';
      })
      rows.push([place.properties.name as any].concat(capValues).concat(values));
    })
    return rows;
  }

  setSlider(): void {
    if (!(this.realYears && this.prognosisYears)) return;
    this.timeSlider!.prognosisStart = this.prognosisYears[0] || 0;
    this.timeSlider!.years = this.realYears.concat(this.prognosisYears);
    this.timeSlider!.value = this.year;
    this.timeSlider!.draw();
  }

  shiftYear(steps: number): void {
    const years = this.timeSlider!.years;
    const idx = years.indexOf(this.year!);
    const newIdx = idx + steps;
    if (newIdx < 0 && newIdx >= years.length)
      return;
    this.year = years[newIdx];
    this.timeSlider!.value = this.year;
    this.updateData();
  }

  onFilterChange(columns: FilterColumn[]): void {
    this.filtersChanged.emit(columns);
  }

}
