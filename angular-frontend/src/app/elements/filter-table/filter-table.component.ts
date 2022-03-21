import { Component, Input, OnInit, TemplateRef, ViewChild } from '@angular/core';
import { ConfirmDialogComponent } from "../../dialogs/confirm-dialog/confirm-dialog.component";
import { MatDialog } from "@angular/material/dialog";
import { FormBuilder, FormControl, FormGroup } from "@angular/forms";

enum Operator {
  '>' = 'größer' ,
  '<' = 'kleiner',
  '=' = 'gleich',
  '>=' = 'größer gleich' ,
  '<=' = 'kleiner gleich'
}

export interface FilterColumn {
  name: string,
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
  constructor(operator: Operator = Operator["="], active = false) {
    this.operator = operator;
    this.active = active;
  }
  filter(values: any[]): boolean[]{
    return Array(values.length).fill(true);
  };
}

class StrFilter extends Filter {
  name = 'Zeichenfilter';
  value = '';

  filter(values: string[]): boolean[] {
    if (!this.active) return Array(values.length).fill(true);
    return [true]
  }
}

class NumFilter extends Filter {
  name = 'Zahlenfilter';
  value = 0;

  filter(values: number[]): boolean[] {
    if (!this.active) return Array(values.length).fill(true);
    return [true]
  }
}

class ClassFilter extends Filter {
  name = 'Klassenfilter';
  classes: string[];

  constructor(classes: string[], operator: Operator = Operator["="], active: boolean = false) {
    super(operator, active);
    this.classes = classes;
    this.value = this.classes[0];
  }

  filter(values: string[]): boolean[] {
    if (!this.active) return Array(values.length).fill(true);
    return [true]
  }
}

@Component({
  selector: 'app-filter-table',
  templateUrl: './filter-table.component.html',
  styleUrls: ['./filter-table.component.scss']
})
export class FilterTableComponent implements OnInit {
  _columns: FilterColumn[] = [];
  _sorted: any[][] = [];
  _rows: any[][] = [];
  filterForm: FormGroup;
  sorting: ('asc' | 'desc' | 'none' )[] = [];
  @ViewChild('numberFilter') numberFilter?: TemplateRef<any>;
  @ViewChild('stringFilter') stringFilter?: TemplateRef<any>;
  @ViewChild('classFilter') classFilter?: TemplateRef<any>;
  operators: [string, string][] = Object.keys(Operator).map(key => [key, Operator[key as keyof typeof Operator]]);

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
    this._sorted = [...rows];
    this.sort();
  };

  toggleSort(col: number) {
    const prevOrder = this.sorting[col];
    const order = (prevOrder === 'none')? 'asc': (prevOrder === 'asc')? 'desc': 'none';
    this.sorting[col] = order;
    this.sort();
  }

  toggleFilter(col: number) {
    const column = this._columns[col]
    if (!column.filter) return;
    column.filter.active = !column.filter.active;
    if (column.filter.active)
      this.openFilterDialog(col);
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
      dialogRef.close();
    });
    dialogRef.afterClosed().subscribe(ok => {
      if (!ok)
        column.filter!.active = false;
    })
  }

  private sort() {
    this._sorted = [...this._rows];
    this.sorting.forEach((order, i) => {
      if (order === 'none') return;
      this._sorted.sort((a, b) => {
        if (a[i] === b[i]) return 0;
        if (order === 'asc' && a[i] > b[i]) return 1;
        if (order === 'desc' && a[i] < b[i]) return 1;
        return -1;
      })
    })
  }

  ngOnInit(): void {
  }

}
