import { AfterViewInit, Component, EventEmitter, Input, Output, TemplateRef, ViewChild } from '@angular/core';
import { FieldType, Infrastructure, Place, PlaceField, Scenario, Service } from "../../../rest-interfaces";
import { PlaceFilter, PlanningService } from "../planning.service";
import { TimeSliderComponent } from "../../../elements/time-slider/time-slider.component";
import { forkJoin, Observable } from "rxjs";
import { map } from "rxjs/operators";
import {
  FilterTableComponent,
  FilterColumn
} from "../../../elements/filter-table/filter-table.component";
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
  // show filter toggle button to toggle between ignoring capacities
  @Input() showIgnoreCapacitiesToggle: boolean = false;
  @Input() ignoreCapacities: boolean = false;
  _ignoreCapacities: boolean = false;
  @Input() service?: Service;
  @Input() scenario?: Scenario;
  @Input() year?: number;
  @Output() onFilter = new EventEmitter<PlaceFilter[]>();
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
    observables.push(this.planningService.getFieldTypes().pipe(map(fieldTypes => {
      this.fieldTypes = fieldTypes;
      this._columnDescriptors = this.getColumnDescriptors();
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

  getColumnDescriptors(): FilterColumn[] {
    const placeFilters = this.planningService.getPlaceFilters(this.infrastructure) || [];
    // order: name > fields > capacities
    let columns: FilterColumn[] = [{ name: 'Name', type: 'STR', changed: false }];
    const nameFilter = placeFilters.find(p => p.property === 'name');
    if (nameFilter)
      columns[0].filter = nameFilter.filter.clone();
    this.infrastructure!.placeFields?.forEach(field => {
      const fieldType = this.fieldTypes.find(ft => ft.id == field.fieldType);
      if (!fieldType) return;
      const column: FilterColumn = {
        name: field.label || field.name,
        type: fieldType.ftype,
        classes: fieldType.classification?.map(c => c.value),
        unit: field.unit,
        changed: false
      };
      const filterInput = placeFilters.find(c => c.field === field.name);
      if (filterInput)
        column.filter = filterInput.filter.clone();
      columns.push(column);
    })
    this.infrastructure!.services!.forEach(service => {
      const column: FilterColumn = {
        // name: service.hasCapacity? `${service.name} (Kapazität)`: service.name,
        name: service.name,
        type: service.hasCapacity? 'NUM' : 'BOOL',
        unit: service.hasCapacity? service.capacityPluralUnit: '',
        changed: false
      };
      const filterInput = placeFilters.find(c => c.service === service.id);
      if (filterInput)
        column.filter = filterInput.filter.clone();
      columns.push(column);
    })
    return columns;
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
      disableClose: true,
      data: {
        template: this.filterTemplate,
        closeOnConfirm: true,
        showCloseButton: false,
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
      if (!this.infrastructure) return;
      let placeFilters: PlaceFilter[] = [];
      // filters are changed in place on _columnDescriptors by filter table
      // order of _columnDescriptors: name > fields > capacities
      const nameFilterColumn = this._columnDescriptors[0];
      if (nameFilterColumn.filter?.active){
        placeFilters.push({ name: nameFilterColumn.name, property: 'name', filter: nameFilterColumn.filter });
      }
      let i = 1;
      this.infrastructure!.placeFields?.forEach(field => {
        const filterColumn = this._columnDescriptors[i];
        if (filterColumn.filter?.active) {
          placeFilters.push({ name: filterColumn.name, field: field.name, filter: filterColumn.filter });
        }
        i += 1;
      });
      this.infrastructure!.services!.forEach(service => {
        const filterColumn = this._columnDescriptors[i];
        if (filterColumn.filter?.active) {
          placeFilters.push({ name: filterColumn.name, service: service.id, filter: filterColumn.filter });
        }
        i += 1;
      });
      this.planningService.setPlaceFilters(this.infrastructure, placeFilters);
      this.onFilter.emit(placeFilters);
    });
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

  downloadCSV(): void {
    this.filterTable?.downloadCSV(`Standorte ${this.service?.name}.csv`);
  }
}
