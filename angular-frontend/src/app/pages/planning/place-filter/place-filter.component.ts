import { AfterViewInit, Component, EventEmitter, Input, Output, TemplateRef, ViewChild } from '@angular/core';
import { Capacity, FieldType, Infrastructure, Place, Scenario, Service } from "../../../rest-interfaces";
import { PlanningService } from "../planning.service";
import { TimeSliderComponent } from "../../../elements/time-slider/time-slider.component";
import { BehaviorSubject, forkJoin, Observable } from "rxjs";
import { map } from "rxjs/operators";
import { FilterTableComponent, FilterColumn } from "../../../elements/filter-table/filter-table.component";
import { MatDialog } from "@angular/material/dialog";
import { ConfirmDialogComponent } from "../../../dialogs/confirm-dialog/confirm-dialog.component";

@Component({
  selector: 'app-place-filter-button',
  templateUrl: './place-filter.component.html',
  styleUrls: ['./place-filter.component.scss']
})
export class PlaceFilterComponent  implements AfterViewInit {
  @ViewChild('filterTemplate') filterTemplate!: TemplateRef<any>;
  @ViewChild('timeSlider') timeSlider?: TimeSliderComponent;
  @ViewChild('filterTable') filterTable?: FilterTableComponent;
  @Input() infrastructure?: Infrastructure;
  @Input() service?: Service;
  @Input() scenario?: Scenario;
  // @Input() services?: Service[];
  @Input() year?: number;
  @Output() onFilter = new EventEmitter<FilterColumn[]>();
  public columns: FilterColumn[] = [];
  _filterColumnsTemp: FilterColumn[] = [];
  years: number[] = [];
  prognosisYears: number[] = [];
  private realYears: number[] = [];
  private fieldTypes: FieldType[] = [];
  rows: any[][] = [];
  places: Place[] = [];

  constructor(public dialog: MatDialog, public planningService: PlanningService) {
  }

  ngAfterViewInit(): void {
  };

  onClick() {
    if (!this.infrastructure) return;
    let observables: Observable<any>[] = [];
    observables.push(this.planningService.getFieldTypes().pipe(map(fieldTypes => {
      this.fieldTypes = fieldTypes;
      this.columns = this.getColumns();
    })))
    observables.push(this.planningService.getRealYears().pipe(map(years => {
      this.realYears = years;
    })))
    observables.push(this.planningService.getPrognosisYears().pipe(map(years => {
      this.prognosisYears = years;
    })))
    observables.push(this.planningService.getPlaces().pipe(map(places => {
      this.places = places;
    })))
    forkJoin(...observables).subscribe(() => {
      this.years = this.realYears.concat(this.prognosisYears);
      if (!this.year) this.year = this.realYears![0];
      this.planningService.updateCapacities({ infrastructure: this.infrastructure, year: this.year }).subscribe(() => {
        this.rows = this.placesToRows(this.places!);
        this.openDialog();
      });
    })
  }

  updateTable(): void {
    this.planningService.updateCapacities({ infrastructure: this.infrastructure, year: this.year, scenario: this.scenario }
    ).subscribe(() => this.rows = this.placesToRows(this.places!));
  }

  private openDialog(): void {
    if (!this.infrastructure) return;
    this._filterColumnsTemp = this.planningService.placeFilterColumns;
    let dialogRef = this.dialog.open(ConfirmDialogComponent, {
      panelClass: 'absolute',
      // width: '100%',
      maxWidth: '90vw',
      disableClose: false,
      data: {
        template: this.filterTemplate,
        closeOnConfirm: true,
        infoText: '<p>Mit dem Schieberegler rechts oben können Sie das Jahr wählen für das die Standortstruktur in der Tabelle angezeigt werden soll. Die Einstellung wird für die Default-Kartendarstellung übernommen.</p>' +
          '<p>Mit einem Klick auf das Filtersymbol in der Tabelle können Sie Filter auf die in der jeweiligen Spalte Indikatoren definieren. Die Filter werden grundsätzlich auf alle Jahre angewendet. In der Karte werden nur die gefilterten Standorte angezeigt.</p>'+
          '<p>Sie können einmal gesetzte Filter bei Bedarf im Feld „Aktuell verwendete Filter“ unter der Tabelle wieder löschen.</p>',
        context: {
          // services: [this.activeService],
          places: this.places,
          scenario: this.scenario,
          year: this.year,
          infrastructure: this.infrastructure
        }
      }
    });
    dialogRef.afterClosed().subscribe((ok: boolean) => {  });
    dialogRef.componentInstance.confirmed.subscribe(() => {
      this.planningService.placeFilterColumns = this._filterColumnsTemp;
      this.onFilter.emit(this.planningService.placeFilterColumns);
    });
  }

  private getColumns(): FilterColumn[] {
    let columns: FilterColumn[] = [{ name: 'Name', type: 'STR' }];
    this.infrastructure!.services!.forEach(service => {
      const column: FilterColumn = {
        // name: service.hasCapacity? `${service.name} (Kapazität)`: service.name,
        name: service.name,
        service: service,
        type: service.hasCapacity? 'NUM' : 'STR',
        unit: service.hasCapacity? service.capacityPluralUnit: ''
      };
      const filterInput = this.planningService.placeFilterColumns?.find(c => c.service === service);
      if (filterInput)
        column.filter = Object.assign(Object.create(Object.getPrototypeOf(filterInput.filter)), filterInput.filter);
      columns.push(column);
    })
    this.infrastructure!.placeFields?.forEach(field => {
      const fieldType = this.fieldTypes.find(ft => ft.id == field.fieldType);
      if (!fieldType) return;
      const column: FilterColumn = {
        name: field.name,
        attribute: field.name,
        type: fieldType.ftype,
        classes: fieldType.classification?.map(c => c.value),
        unit: field.unit
      };
      const filterInput = this.planningService.placeFilterColumns?.find(c => c.attribute === field.name);
      if (filterInput)
        column.filter = Object.assign(Object.create(Object.getPrototypeOf(filterInput.filter)), filterInput.filter);
      columns.push(column);
    })
    return columns;
  }

  private placesToRows(places: Place[]): any[][]{
    const rows: any[][] = [];
    places.forEach(place => {
      if (this.service && !this.planningService.getPlaceCapacity(place, { service: this.service, year: this.year, scenario: this.scenario })) return;
      const capValues = this.infrastructure!.services!.map(service => {
        const capacity = this.planningService.getPlaceCapacity(place, { service: service, year: this.year, scenario: this.scenario });
        return service.hasCapacity? capacity: capacity? 'Ja': 'Nein';
      })
      const values: any[] = this.infrastructure!.placeFields!.map(field => {
        return place.attributes[field.name] || '';
      })
      rows.push([place.name as any].concat(capValues).concat(values));
    })
    return rows;
  }

  shiftYear(steps: number): void {
    const years = this.timeSlider!.years;
    const idx = years.indexOf(this.year!);
    const newIdx = idx + steps;
    if (newIdx < 0 && newIdx >= years.length)
      return;
    this.year = years[newIdx];
    this.timeSlider!.value = this.year;
    this.updateTable();
  }

  onFilterChange(columns: FilterColumn[]): void {
    this._filterColumnsTemp = columns;
  }
}
