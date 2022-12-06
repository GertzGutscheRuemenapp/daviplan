import { Component, EventEmitter, Input, OnInit, Output, TemplateRef, ViewChild } from '@angular/core';
import { ConfirmDialogComponent } from "../../dialogs/confirm-dialog/confirm-dialog.component";
import { MatDialog } from "@angular/material/dialog";
import { FormArray, FormBuilder, FormControl, FormGroup } from "@angular/forms";
import { Service } from "../../rest-interfaces";

// type Operator = '>' | '<' | '=' | '>=' | '<=';

enum Operator {
  gt = '>',
  lt = '<',
  eq = '=',
  gte = '>=',
  lte = '<=',
  in = 'in',
  contains = 'contains'
}

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
  name: string,
  attribute?: string,
  service?: Service,
  type: 'CLA' | 'NUM' | 'STR' | 'BOOL',
  classes?: string[],
  filter?: Filter,
  unit?: string
}

abstract class Filter {
  operator: Operator;
  active: boolean;
  name = 'Filter';
  value?: any;
  allowedOperators: Operator[] = Object.values(Operator);
  constructor(operator: Operator = Operator.eq, active = false) {
    this.operator = operator;
    this.active = active;
  }
  filterColumn(values: any[]): boolean[]{
    if (!this.active) return Array(values.length).fill(true);
    return values.map(v => this.filter(v));
  };
  filter(value: any): boolean {
    if (!this.active) return false;
    if (this.operator === Operator.gt)
      return (value > this.value);
    if (this.operator === Operator.lt)
      return (value < this.value);
    if (this.operator === Operator.eq)
      return (value == this.value);
    if (this.operator === Operator.gte)
      return (value >= this.value);
    if (this.operator === Operator.lte)
      return (value <= this.value);
    if (this.operator === Operator.in) {
      if (!this.value) return true;
      return this.value.split(', ').indexOf(value) >= 0;
    }
    return false;
  };
}

class StrFilter extends Filter {
  name = 'Zeichenfilter';
  value = '';
  allowedOperators = [Operator.in, Operator.contains];

  constructor(operator: Operator = Operator.eq, active: boolean = false) {
    super(operator, active);
  }

  filter(value: string): boolean {
    return super.filter(value);
  }
}

class NumFilter extends Filter {
  name = 'Zahlenfilter';
  value = 0;
  allowedOperators = [Operator.gt, Operator.lt, Operator.eq, Operator.gte, Operator.lte];

  filter(value: number): boolean {
    return super.filter(value);
  }
}

class BoolFilter extends Filter {
  name = 'Booleanfilter';
  value = false;

  filter(value: number | boolean): boolean {
    return this.value === !!value;
  }
}

class ClassFilter extends Filter {
  name = 'Klassenfilter';
  classes: string[];
  allowedOperators = [Operator.in];
  value = '';

  constructor(classes: string[] = [], operator: Operator = Operator.eq, active: boolean = false) {
    super(Operator.in, active);
    this.classes = classes;
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
export class FilterTableComponent implements OnInit {
  @Output() filtersChanged = new EventEmitter<FilterColumn[]>();
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
  Operator = Operator;

  constructor(private dialog: MatDialog, private formBuilder: FormBuilder) {}

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
          column.filter = new StrFilter();
        else if (column.type === 'CLA')
          column.filter = new ClassFilter(column.classes || []);
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
      this.emitChange();
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
    const formConfig: any = {
      operator: new FormControl(column.filter.operator),
      value: new FormControl('')
    }
    if (column.type === 'CLA' || column.type === 'STR') {
      const options = (column.type === 'CLA')? (column.filter as ClassFilter).classes: [...new Set(this._rows.map(r => r[col]))].sort();
      context['options'] = options;
      const formArray = this.formBuilder.array([]);
      options.forEach(o => formArray.push(new FormControl(false)));
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
      column.filter!.operator = this.filterForm.value.operator;
      let value = this.filterForm.value.value;
      if (column.type === 'BOOL') value = value === '1';
      if (this.filterForm.value.operator === Operator.in) {
        const checked = context['options'].filter((o: any, i: number) => this.filterForm.value.options[i]);
        value = checked.join(', ');
      }
      column.filter!.value = value;
      column.filter!.active = true;
      this.emitChange();
      this.filterAndSort()
      dialogRef.close(true);
    });
  }

  private emitChange(): void {
    this.filtersChanged.emit(this._columns.filter(col => col.filter?.active));
  }

  private filterAndSort(): void {
    const filtered = this.filter(this._rows);
    this.processedRows = this.sort(filtered);
  }

  removeAllFilters(): void {
    this._columns.forEach(column => column.filter!.active = false);
    this.emitChange();
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
    const filters: [number, Filter][] = this._columns.map((column, i) => [i, column.filter!]);
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

  ngOnInit(): void {
  }

}
