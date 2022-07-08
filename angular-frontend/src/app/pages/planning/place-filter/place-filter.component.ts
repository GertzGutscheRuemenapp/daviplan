import { Component, EventEmitter, Input, Output, TemplateRef, ViewChild } from '@angular/core';
import { Capacity, FieldType, Infrastructure, Place, Scenario, Service } from "../../../rest-interfaces";
import { PlanningService } from "../planning.service";
import { TimeSliderComponent } from "../../../elements/time-slider/time-slider.component";
import { forkJoin, Observable } from "rxjs";
import { map } from "rxjs/operators";
import { FilterTableComponent, FilterColumn } from "../../../elements/filter-table/filter-table.component";
import { MatDialog } from "@angular/material/dialog";
import { ConfirmDialogComponent } from "../../../dialogs/confirm-dialog/confirm-dialog.component";

@Component({
  selector: 'app-place-filter-button',
  templateUrl: './place-filter.component.html',
  styleUrls: ['./place-filter.component.scss']
})
export class PlaceFilterComponent {
  @ViewChild('filterTemplate') filterTemplate!: TemplateRef<any>;
  @ViewChild('timeSlider') timeSlider?: TimeSliderComponent;
  @ViewChild('filterTable') filterTable?: FilterTableComponent;
  @Input() infrastructure?: Infrastructure;
  @Input() scenario?: Scenario;
  // @Input() services?: Service[];
  @Input() year?: number;
  @Input() places?: Place[];
  @Output() onFilter = new EventEmitter<FilterColumn[]>();
  public columns: FilterColumn[] = [];
  filterColumns: FilterColumn[] = [];
  _filterColumnsTemp: FilterColumn[] = [];
  years: number[] = [];
  prognosisYears: number[] = [];
  private realYears: number[] = [];
  private fieldTypes: FieldType[] = [];
  private capacitiesPerService: Record<number, Capacity[]> = {};
  rows: any[][] = [];

  constructor(public dialog: MatDialog, public planningService: PlanningService) {}

  onClick() {
    if (!this.infrastructure) return;
    // this.services = this.infrastructure!.services;
    this.planningService.getFieldTypes().subscribe(fieldTypes => {
      this.fieldTypes = fieldTypes;
      this.columns = this.getColumns();
      this.planningService.getRealYears().subscribe(years => {
        this.realYears = years;
        this.planningService.getPrognosisYears().subscribe(years => {
          this.prognosisYears = years;
          this.years = this.realYears.concat(this.prognosisYears);
          if (!this.year) this.year = this.realYears![0];
          this.updateCapacities().subscribe(() => {
            this.rows = this.placesToRows(this.places!);
            this.openDialog();
          });
        })
      })
    })
  }

  updateTable(): void {
    this.updateCapacities().subscribe(() => this.rows = this.placesToRows(this.places!));
  }

  private openDialog(): void {
    if (!this.infrastructure) return;
    this._filterColumnsTemp = this.filterColumns;
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
      this.filterColumns = this._filterColumnsTemp;
      this.onFilter.emit(this.filterColumns);
    });
  }

  private updateCapacities(): Observable<any> {
    const observable = new Observable<any>(subscriber => {
      let observables: Observable<any>[] = [];
      this.infrastructure!.services?.forEach(service => {
        observables.push(this.planningService.getCapacities({
          year: this.year!,
          service: service.id!
        }).pipe(map(capacities => {
          this.capacitiesPerService[service.id] = capacities;
        })));
      });

      forkJoin(...observables).subscribe(() => {
        subscriber.next();
        subscriber.complete();
      })

    })
    return observable;
  }

  getColumns(): FilterColumn[] {
    let columns: FilterColumn[] = [{ name: 'Name', type: 'STR' }];
    this.infrastructure!.services!.forEach(service => {
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
      const capValues = this.infrastructure!.services!.map(service => {
        return this.getCapacity(service, place);
      })
      const values: any[] = this.infrastructure!.placeFields!.map(field => {
        return place.properties.attributes[field.name] || '';
      })
      rows.push([place.properties.name as any].concat(capValues).concat(values));
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

  filterPlaces(places: Place[]): Observable<Place[]> {
    const observable = new Observable<Place[]>(subscriber => {
      this.updateCapacities().subscribe(() =>  {
        subscriber.next(places.filter(place => this._filterPlace(place)));
        subscriber.complete();
      });
    });
    return observable;
  }

  private _filterPlace(place: Place): boolean {
    if (this.filterColumns.length === 0) return true;
    let match = false;
    this.filterColumns.forEach((filterColumn, i) => {
      const filter = filterColumn.filter!;
      if (filterColumn.service) {
        const cap = this.getCapacity(filterColumn.service, place);
        if (!filter.filter(cap)) return;
      }
      else if (filterColumn.attribute) {
        const value = place.properties.attributes[filterColumn.attribute];
        if (!filter.filter(value)) return;
      }
      if (i === this.filterColumns.length - 1) match = true;
    })
    return match;
  }

  getCapacity(service: Service, place: Place): number{
    const cap = this.capacitiesPerService[service.id]?.find(c => c.place === place.id);
    return cap?.capacity || 0;
  }
}
