import { Component, Input, TemplateRef, ViewChild } from '@angular/core';
import { ConfirmDialogComponent } from "../../dialogs/confirm-dialog/confirm-dialog.component";
import { MatDialog } from "@angular/material/dialog";
import { FormBuilder, FormControl, FormGroup } from "@angular/forms";

export function serializeFilter(filter: ColumnFilter): string {
  const obj = {
    value: filter.value,
    active: filter.active,
    operator: filter.operator,
    classes: filter.hasOwnProperty('classes')? filter['classes' as keyof ColumnFilter]: [],
    filterClass: filter.constructor.name
  }
  return JSON.stringify(obj);
}

export function deSerializeFilter(serialized: string): ColumnFilter | undefined {
  let obj;
  try {
    obj = JSON.parse(serialized);
  }
  catch {
    return;
  }
  switch (obj.filterClass) {
    case 'NumFilter':
      return new NumFilter({ value: obj.value, active: obj.active, operator: obj.operator });
    case 'ClassFilter':
      return new ClassFilter({ value: obj.value, active: obj.active, operator: obj.operator, classes: obj.classes });
    case 'BoolFilter':
      return new BoolFilter({ value: obj.value, active: obj.active, operator: obj.operator });
    default:
      return new StrFilter({ value: obj.value, active: obj.active, operator: obj.operator })
  }
}

export enum FilterOperator {
  gt = '>',
  lt = '<',
  eq = '=',
  gte = '>=',
  lte = '<=',
  in = 'in',
  contains = 'contains'
}

export type ColumnFilterType = 'CLA' | 'NUM' | 'STR' | 'BOOL';

const opText: Record<any, string> = {
  '>': 'größer' ,
  '<': 'kleiner',
  '=': 'gleich',
  '>=': 'größer gleich' ,
  '<=': 'kleiner gleich',
  'in': 'Auswahl',
  'contains': 'enthält'
}

export interface FilterColumn {
  name: string;
  type: ColumnFilterType;
  classes?: string[];
  filter?: ColumnFilter;
  unit?: string;
  changed: boolean;
}

export abstract class ColumnFilter {
  operator: FilterOperator = FilterOperator.eq;
  active: boolean;
  name = 'ColumnFilter';
  value?: any;
  allowedOperators: FilterOperator[] = Object.values(FilterOperator);

  constructor(options?: { operator?: FilterOperator, active?: boolean, value?: any }) {
    if (options?.operator)
      this.operator = options.operator;
    if (options?.value !== undefined)
      this.value = options.value;
    this.active = !!options?.active;
  }
  filter(value: any): boolean {
    // defaults fitting strings and bools
    switch (this.operator) {
      case FilterOperator.gt:
        return (value > this.value);
      case FilterOperator.lt:
        return (value < this.value);
      case FilterOperator.eq:
        return (value == this.value);
      case FilterOperator.gte:
        return (value >= this.value);
      case FilterOperator.lte:
        return (value <= this.value);
      case FilterOperator.in:
        if (this.value === undefined) return true;
        return this.value.split(',').indexOf(value) >= 0;
      default:
        return false;
    }
  };

  getDescription(): string {
    let val;
    switch (this.operator) {
      case FilterOperator.in:
        val = `(${this.value.split(',').length} Einträge)`;
        break;
      case FilterOperator.contains:
        val = `"${this.value}"`;
        break;
      default:
        val = this.value;
    }
    return `${opText[this.operator]} ${val}`;
  }

  clone(): ColumnFilter {
    return Object.assign(Object.create(Object.getPrototypeOf(this)), this);
  }
}

export class StrFilter extends ColumnFilter {
  name = 'Zeichenfilter';
  allowedOperators = [FilterOperator.in, FilterOperator.contains];
  filter(value: string): boolean {
    if (!this.value) return true;
    if (this.operator === FilterOperator.contains)
      return (!!value && value.toLowerCase().indexOf(this.value.toLowerCase()) >= 0);
    return super.filter(value);
  }
}

export class NumFilter extends ColumnFilter {
  name = 'Zahlenfilter';
  allowedOperators = [FilterOperator.gt, FilterOperator.lt, FilterOperator.eq, FilterOperator.gte, FilterOperator.lte];

  filter(value: number): boolean {
    return super.filter(value);
  }
}

export class BoolFilter extends ColumnFilter {
  name = 'Booleanfilter';
  value = false;
  allowedOperators = [FilterOperator.eq];

  filter(value: number | boolean): boolean {
    return this.value === !!value;
  }

  getDescription(): string {
    return this.value? 'Ja': 'Nein';
  }
}

export class ClassFilter extends ColumnFilter {
  name = 'Klassenfilter';
  operator = FilterOperator.in;
  classes: string[] = [];
  allowedOperators = [FilterOperator.in];
  value = '';

  constructor(options?: { active?: boolean, value?: any, operator?: FilterOperator, classes?: string []}) {
    super({ active: options?.active, value: options?.value, operator: options?.operator })
    if (options?.classes)
      this.classes = options.classes;
  }

  filter(value: string): boolean {
    return super.filter(value);
  }
}

@Component({
  selector: 'app-filter-table',
  templateUrl: './filter-table.component.html',
  styleUrls: ['../data-table/data-table.component.scss', './filter-table.component.scss']
})
export class FilterTableComponent {
  @Input() maxTableHeight = '100%';
  _columns: FilterColumn[] = [];
  processedRows: any[][] = [];
  _rows: any[][] = [];
  filterForm!: FormGroup;
  sorting: ('asc' | 'desc' | 'none' )[] = [];
  @ViewChild('numberFilter') numberFilter?: TemplateRef<any>;
  @ViewChild('stringFilter') stringFilter?: TemplateRef<any>;
  @ViewChild('classFilter') classFilter?: TemplateRef<any>;
  @ViewChild('boolFilter') boolFilter?: TemplateRef<any>;
  opText = opText;
  Operator = FilterOperator;

  @Input() set columns (columns: FilterColumn[]){
    this._columns = columns;
    if (columns) {
      this.sorting = Array(columns.length).fill('none');
      columns.forEach(column => {
        // filter already exists
        if (column.filter) return;
        if (column.type === 'NUM')
          column.filter = new NumFilter();
        else if (column.type === 'STR')
          column.filter = new StrFilter({ operator: FilterOperator.in });
        else if (column.type === 'CLA')
          column.filter = new ClassFilter({ operator: FilterOperator.in, classes: column.classes });
        else if (column.type === 'BOOL')
          column.filter = new BoolFilter();
      })
    }
  }

  @Input() set rows (rows: any[][]){
    // the order of setting the inputs seems not to be guaranteed, take row length
    // if header is not set yet
    if (rows.length > 0 && this.sorting.length !== rows[0].length)
      this.sorting = Array(rows[0].length).fill('none');
    this._rows = rows;
    this.filterAndSort();
  };

  constructor(private dialog: MatDialog, private formBuilder: FormBuilder) {}

  toggleSort(col: number) {
    const prevOrder = this.sorting[col];
    const order = (prevOrder === 'none')? 'asc': (prevOrder === 'asc')? 'desc': 'none';
    // only allow one column to be sorted atm
    this.sorting = Array(this.sorting.length).fill('none');
    this.sorting[col] = order;
    this.filterAndSort();
  }

  toggleFilter(col: number) {
    const column = this._columns[col]
    if (!column.filter) return;
    if (!column.filter.active)
      this.openFilterDialog(col);
    else {
      column.filter.active = !column.filter.active;
      column.changed = true;
      this.filterAndSort();
    }
  }

  openFilterDialog(col: number) {
    const column = this._columns[col];
    if (!column.filter) return;
    const template = (column.type === 'NUM')? this.numberFilter:
                     (column.type === 'BOOL')? this.boolFilter:
                     (column.type === 'CLA')? this.classFilter:
                       this.stringFilter;
    const context: any = {
      unit: column.unit || '' ,
      filter: column.filter
    }
    const formValue = (column.type === 'BOOL')? ((column.filter.value)? '1': '0'):
                      (column.type === 'NUM')? column.filter.value || 0:
                      column.filter.value || ''
    const formConfig: any = {
      operator: new FormControl(column.filter.operator),
      value: new FormControl(formValue)
    }
    if (column.type === 'CLA' || column.type === 'STR') {
      // take classes as options or all unique strings that contain sth different than whitespaces
      let options = (column.type === 'CLA')? (column.filter as ClassFilter).classes:
        [...new Set(this._rows.map(r => r[col]))].filter(o => o && o.replace(/\s/g, "").length > 0).sort();
      context['options'] = options;
      const formArray = this.formBuilder.array([]);
      // values of the checkboxes for possible options, restoring current settings by filtering options with filter
      options.forEach(o => formArray.push(new FormControl(column.filter?.filter(o))));
      formConfig.options = formArray;
    }
    this.filterForm = this.formBuilder.group(formConfig);

    let dialogRef = this.dialog.open(ConfirmDialogComponent, {
      panelClass: 'absolute',
      width: '600px',
      disableClose: true,
      data: {
        title: column.filter.name,
        subtitle: column.name,
        template: template,
        closeOnConfirm: false,
        context: context
      }
    });
    dialogRef.componentInstance.confirmed.subscribe(() => {
      this.filterForm.markAllAsTouched();
      if (this.filterForm.invalid) return;
      if (this.filterForm.value.operator === '-1') {
        column.filter!.active = false;
      }
      else {
        let value = this.filterForm.value.value;
        if (column.type === 'BOOL') value = value === '1';
        if (this.filterForm.value.operator === FilterOperator.in) {
          const checked = context['options'].filter((o: any, i: number) => this.filterForm.value.options[i]);
          value = checked.join(',');
        }
        // no input > do nothing (keeping dialog open) ToDo: error message?
        if (!value && value !== 0 && value !== false) return;
        column.filter!.operator = this.filterForm.value.operator;
        column.filter!.value = value;
        column.filter!.active = true;
      }
      column.changed = true;
      this.filterAndSort();
      dialogRef.close(true);
    });
  }

  private filterAndSort(): void {
    const filtered = this.filter(this._rows);
    this.processedRows = this.sort(filtered);
  }

  removeAllFilters(): void {
    this._columns.forEach(column => {
      if (column.filter!.active) column.changed = true;
      column.filter!.active = false;
    });
    this.filterAndSort();
  }

  private sort(rows: any[][]): any[][] {
    let sorted = [...rows];
    this.sorting.forEach((order, i) => {
      if (order === 'none') return;
      sorted.sort((a, b) => {
        if (a[i] === b[i]) return 0;
        if (order === 'asc' && a[i] > b[i]) return 1;
        if (order === 'desc' && a[i] < b[i]) return 1;
        return -1;
      })
    })
    return sorted;
  }

  private filter(rows: any[][]): any[][] {
    let filtered: any[][] = [];
    const filters: [number, ColumnFilter][] = this._columns.map((column, i) => [i, column.filter!]);
    const activeFilters = filters.filter(ifs => ifs && ifs[1].active);
    if (activeFilters.length === 0) return [...rows];
    rows.forEach(row => {
      for(let i = 0; i < activeFilters.length; i++){
        const filter = activeFilters[i][1];
        const colIdx = activeFilters[i][0];
        // filtered out -> next row
        if (!filter.filter(row[colIdx])) return;
        // last column and no filtering out occured in row
        if (i === activeFilters.length - 1) filtered.push(row);
      }
    })
    return filtered;
  }

  downloadCSV(filename: string): void {
    // UTF-8 BOM
    let csvContent = 'data:text/csv;charset=utf-8,\uFEFF';
    csvContent += this._columns.map(c => c.name).join(';') + "\r\n";
    this.processedRows.forEach(row => {
      const rTxt = row.map(d => (typeof d === 'number')? d.toLocaleString(): d).join(';');
      csvContent += rTxt + "\r\n";
    });
    const link = document.createElement('a');
    link.setAttribute('href', encodeURI(csvContent));
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
  }

}
