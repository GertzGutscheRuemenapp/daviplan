import { AfterViewInit, Component, EventEmitter, Input, Output, TemplateRef, ViewChild } from '@angular/core';
import { FieldType, Infrastructure, Place, PlaceField, Scenario, Service } from "../../../rest-interfaces";
import { PlanningService } from "../planning.service";
import { TimeSliderComponent } from "../../../elements/time-slider/time-slider.component";
import { forkJoin, Observable } from "rxjs";
import { map } from "rxjs/operators";
import { v4 as uuid } from "uuid";
import {
  FilterTableComponent,
  FilterColumn,
  ColumnFilter, ColumnFilterType, NumFilter, StrFilter, ClassFilter, BoolFilter, FilterOperator
} from "../../../elements/filter-table/filter-table.component";
import { MatDialog } from "@angular/material/dialog";
import { ConfirmDialogComponent } from "../../../dialogs/confirm-dialog/confirm-dialog.component";
import { operators } from "rxjs/internal/Rx";

export class PlaceFilterColumn {
  readonly name?: string;
  readonly id = uuid();
  readonly service?: Service;
  readonly placeField?: PlaceField;
  readonly property?: string;
  readonly type: ColumnFilterType;
  private _filter: ColumnFilter;
  private readonly classes?: string[];

  constructor(options?: {name?: string, property?: string, service?: Service, field?: { placeField: PlaceField, fieldType?: FieldType }}) {
    this.name = options?.name;
    // only filter one of those three: capacity or place attribute or property, they exclude each other
    if (options?.service) {
      this.service = options.service;
      this.type = this.service.hasCapacity? 'NUM' : 'BOOL';
      if (!this.name)
        this.name = this.service.name;
    }
    else if (options?.field) {
      this.placeField = options.field.placeField;
      this.type = options.field.fieldType?.ftype || 'STR';
      this.classes = options.field.fieldType?.classification?.map(c => c.value);
      if (!this.name)
        this.name = this.placeField.label || this.placeField.name;
    }
    else {
      this.property = options?.property;
      this.type = 'STR';
    }
    if (this.type === 'NUM')
      this._filter = new NumFilter();
    else if (this.type === 'CLA')
      this._filter = new ClassFilter(this.classes || []);
    else if (this.type === 'BOOL')
      this._filter = new BoolFilter();
    else
      this._filter = new StrFilter();
  }

  getColumnDescriptor(): FilterColumn {
    return {
      id: this.id,
      name: this.name || '',
      type: this.type,
      classes: this.classes,
      // filter is cloned to avoid side effects
      filter: Object.assign(Object.create(Object.getPrototypeOf(this._filter)), this._filter),
      unit: this.placeField?.unit,
      changed: false
    };
  }

  isActive(): boolean {
    return this._filter.active;
  }

  setFilterAttributes(options?: { operator?: FilterOperator, value?: any, active?: boolean }) {
    if (options?.operator !== undefined)
      this._filter.operator = options.operator;
    if (options?.value !== undefined)
      this._filter.value = options.value;
    if (options?.active !== undefined)
      this._filter.active = options.active;
  }

  serialize(): string{
    return '';
  };

  deserialize(serialized: string): PlaceFilterColumn {
    return new PlaceFilterColumn();
  }

  filter(place: Place): boolean {
    // service filter => filter capacity
    if (this.service) {
      return this._filter.filter(place.capacity);
    }
    // placefield filter => filter place "attribute"
    else if (this.placeField) {
      return this._filter.filter(place.attributes[this.placeField.name]);
    }
    // property filter
    else {
      // if no property was given take the given name as a last resort
      const property = this.property || this.name;
      if (property && place.hasOwnProperty(property))
        return this._filter.filter(place[property as keyof Place]);
    }
    return false
  }

  getDescription(): string {
    return this._filter.getDescription();
  }
}

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
  // show filter toggle button to toggle between ignoring capacities
  @Input() showIgnoreCapacitiesToggle: boolean = false;
  @Input() ignoreCapacities: boolean = false;
  _ignoreCapacities: boolean = false;
  @Input() service?: Service;
  @Input() scenario?: Scenario;
  @Input() year?: number;
  @Output() onFilter = new EventEmitter<PlaceFilterColumn[]>();
  public _columnDescriptors: FilterColumn[] = [];
  _filterColumnsTemp: FilterColumn[] = [];
  years: number[] = [];
  prognosisYears: number[] = [];
  private realYears: number[] = [];
  private fieldTypes: FieldType[] = [];
  rows: any[][] = [];
  places: Place[] = [];

  constructor(public dialog: MatDialog, public planningService: PlanningService) {
  }

  ngAfterViewInit(): void {};

  onClick() {
    if (!this.infrastructure) return;
    this._ignoreCapacities = this.ignoreCapacities;
    let observables: Observable<any>[] = [];

    // order: name > fields > capacities
    this._columnDescriptors = this.planningService.getPlaceFilterColumns(this.infrastructure).map(
      c => c.getColumnDescriptor());
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
      const filterColumns = this.planningService.getPlaceFilterColumns(this.infrastructure);
      const changed = this._columnDescriptors.filter(c => c.changed);
      changed.filter(c => c.changed).forEach(desc => {
        filterColumns.find(c => c.id === desc.id)?.setFilterAttributes({
          operator: desc.filter?.operator,
          value: desc.filter?.value,
          active: desc.filter?.value
        });
      })
      if (changed.length) {
        this.onFilter.emit(this.planningService.getPlaceFilterColumns(this.infrastructure!));

      }
    });
  }

  getColumnDescriptors() {

  }

  private placesToRows(places: Place[]): any[][]{
    const rows: any[][] = [];
    places.forEach(place => {
      // skip rows with capacity of 0 in active service (except the switch to show them is toggled on)
      if (this.service && !this._ignoreCapacities && !this.planningService.getPlaceCapacity(place, { service: this.service, year: this.year, scenario: this.scenario })) return;

      const fieldValues: any[] = this.infrastructure!.placeFields!.map(field => {
        return place.attributes[field.name] || '';
      })
      const capValues = this.infrastructure!.services!.map(service => {
        const capacity = this.planningService.getPlaceCapacity(place, { service: service, year: this.year, scenario: this.scenario });
        return service.hasCapacity? capacity: !!capacity;
      })
      // order: name > fields > capacities
      rows.push([place.name as any].concat(fieldValues).concat(capValues));
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
}
