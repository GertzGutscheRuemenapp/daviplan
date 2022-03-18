import { AfterViewInit, Component, Input, OnInit, ViewChild } from '@angular/core';
import { Capacity, Infrastructure, Place, Scenario, Service } from "../../../rest-interfaces";
import { PlanningService } from "../planning.service";
import { hasDirectiveDecorator } from "@angular/compiler-cli/ngcc/src/migrations/utils";
import { TimeSliderComponent } from "../../../elements/time-slider/time-slider.component";
import { MatSlider } from "@angular/material/slider";

const mockHeader = ['Name', 'Zustand', 'Anzahl Betreuer', 'Kapazität Krippe', 'Kapazität Kita', 'Adresse']
const mockRows = [
  ['KIGA Nord', 'gut', 12, 28, 22, 'Paul Ehrlich Straße 3, 35029 Bremen'],
  ['Krippe Westentchen', 'sehr gut', 20, 80, 0, 'Cuxhavener Landstraße 2, 35029 Bremen'],
  ['Kita Süd', 'befriedigend', 6, 10, 20, 'Diepholzer Weg 133, 35029 Bremen'],
  ['Katholische Kita Mitte', 'gut', 2, 8, 12, 'Kirchenallee 24, 35029 Bremen'],
]

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
  @ViewChild('timeSlider') timeSlider?: MatSlider;
  realYears?: number[];
  prognosisYears?: number[];
  minYear = 0;
  maxYear = 0;
  public header: string[] = [];
  public rows: any[][] = [];
  private capacities: Record<number, Capacity[]> = {};

  constructor(private planningService: PlanningService) {
  }

  ngAfterViewInit(): void {
    this.planningService.getRealYears().subscribe( years => {
      this.realYears = years;
      this.planningService.getPrognosisYears().subscribe( years => {
        this.prognosisYears = years;
        if (!this.year) this.year = this.realYears![0];
        this.setSlider();
        this.updateData();
      })
    })
    if (!this.services) this.services = this.infrastructure.services;
    this.timeSlider?.valueChange.subscribe(value => {
      if (value) {
        this.year = value;
        this.updateData();
      }
    })
  }

  initData(): void {

  }

  updateData(): void {
    this.capacities = {};
    this.services?.forEach(service => {
      this.planningService.getCapacities(this.year!, service.id).subscribe(capacities => {
        this.capacities[service.id] = capacities;
        this.header = this.getHeader();
        this.rows = this.placesToRows(this.places);
      })
    })
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
        const cap = this.capacities[service.id].find(c => c.place === place.id);
        return cap?.capacity || 0;
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
    this.maxYear = this.prognosisYears? this.prognosisYears[this.prognosisYears.length - 1]: this.realYears[this.realYears.length - 1];
    this.minYear = this.realYears[0];
    this.timeSlider!.min = this.minYear;
    this.timeSlider!.max = this.maxYear;
    this.timeSlider!.value = this.year!;
  }

}
