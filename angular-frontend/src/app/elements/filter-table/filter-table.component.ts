import { Component, EventEmitter, Input, OnInit, Output, TemplateRef, ViewChild } from '@angular/core';
import { ConfirmDialogComponent } from "../../dialogs/confirm-dialog/confirm-dialog.component";
import { MatDialog } from "@angular/material/dialog";
import { FormBuilder, FormControl, FormGroup } from "@angular/forms";
import { Service } from "../../rest-interfaces";

// type Operator = '>' | '<' | '=' | '>=' | '<=';

enum Operator {
  gt = '>',
  lt = '<',
  eq = '=',
  gte = '>=',
  lte = '<='
}

const opText = {
  '>': 'größer' ,
  '<': 'kleiner',
  '=': 'gleich',
  '>=': 'größer gleich' ,
  '<=': 'kleiner gleich'
}

export interface FilterColumn {
  name: string,
  attribute?: string,
  service?: Service,
  type: 'CLA' | 'NUM' | 'STR',
  classes?: string[],
  filter?: Filter,
  unit?: string
}

abstract class Filter {
  operator: Operator;
  active: boolean;
  name = 'Filter';
  value?: any;
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
    return false;
  };
}

class StrFilter extends Filter {
  name = 'Zeichenfilter';
  value = '';

  filter(value: string): boolean {
    return super.filter(value);
  }
}

class NumFilter extends Filter {
  name = 'Zahlenfilter';
  value = 0;

  filter(value: number): boolean {
    return super.filter(value);
  }
}

class ClassFilter extends Filter {
  name = 'Klassenfilter';
  classes: string[];

  constructor(classes: string[], operator: Operator = Operator.eq, active: boolean = false) {
    super(operator, active);
    this.classes = classes;
    this.value = this.classes[0];
  }

  filter(value: string): boolean {
    return true
  }
}

@Component({
  selector: 'app-filter-table',
  templateUrl: './filter-table.component.html',
  styleUrls: ['./filter-table.component.scss']
})
export class FilterTableComponent implements OnInit {
  @Output() filtersChanged = new EventEmitter<FilterColumn[]>();
  _columns: FilterColumn[] = [];
  processedRows: any[][] = [];
  _rows: any[][] = [];
  filterForm: FormGroup;
  sorting: ('asc' | 'desc' | 'none' )[] = [];
  @ViewChild('numberFilter') numberFilter?: TemplateRef<any>;
  @ViewChild('stringFilter') stringFilter?: TemplateRef<any>;
  @ViewChild('classFilter') classFilter?: TemplateRef<any>;
  operators: string[][] = Object.values(Operator).map(op => [op, opText[op]]);
  opText = opText;

  constructor(private dialog: MatDialog, private formBuilder: FormBuilder) {
    this.filterForm = this.formBuilder.group({
      operator: new FormControl(''),
      value: new FormControl('')
    });
  }

  @Input() set columns (columns: FilterColumn[]){
    this._columns = columns;
    if (columns) {
      this.sorting = Array(columns.length).fill('none');
      columns.forEach(column => {
        if (column.type === 'NUM')
          column.filter = new NumFilter();
        else if (column.type === 'STR')
          column.filter = new StrFilter();
        else if (column.type === 'CLA')
          column.filter = new ClassFilter(column.classes || []);
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
    this.filterForm.reset({
        operator: column.filter.operator,
        value: column.filter.value
    });
    const template = (column.type === 'NUM')? this.numberFilter: (column.type === 'STR')? this.stringFilter: this.classFilter;
    const context: any = {
      unit: column.unit || '' ,
    }
    if (column.type === 'CLA')
      context['classes'] = (column.filter as ClassFilter).classes;
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
      column.filter!.value = this.filterForm.value.value;
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
