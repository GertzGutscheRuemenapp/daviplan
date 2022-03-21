import { AfterViewInit, Component, Input, OnInit, ViewChild } from '@angular/core';
import { Capacity, Infrastructure, Place, Scenario, Service } from "../../../rest-interfaces";
import { PlanningService } from "../planning.service";
import { TimeSliderComponent } from "../../../elements/time-slider/time-slider.component";
import { forkJoin, Observable } from "rxjs";
import { map } from "rxjs/operators";
import { FilterTableComponent } from "../../../elements/filter-table/filter-table.component";

@Component({
  selector: 'app-place-filter',
  templateUrl: './place-filter.component.html',
  styleUrls: ['./place-filter.component.scss']
})
export class PlaceFilterComponent implements AfterViewInit {
  @Input() infrastructure!: Infrastructure;
  @Input() services?: Service[];
  @Input() places!: Place[];
  @Input() scenario!: Scenario;
  @Input() year?: number;
  @ViewChild('timeSlider') timeSlider?: TimeSliderComponent;
  @ViewChild('filterTable') filterTable?: FilterTableComponent;
  realYears?: number[];
  prognosisYears?: number[];
  public header: string[] = [];
  public rows: any[][] = [];
  private capacities: Record<number, Record<string, number>> = {};

  constructor(private planningService: PlanningService) {
  }

  ngAfterViewInit(): void {
    if (!this.services) this.services = this.infrastructure.services;
    this.header = this.getHeader();
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

  getHeader(): string[] {
    let header = ['Name'];
    this.services!.forEach(service => {
      header.push(`Kapazität ${service.name}`);
    })
    this.infrastructure.placeFields?.forEach(field => {
      let fieldName = field.name;
      if (field.unit) fieldName += ` (${field.unit})`;
      header.push(fieldName);
    })
    return header;
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

}
