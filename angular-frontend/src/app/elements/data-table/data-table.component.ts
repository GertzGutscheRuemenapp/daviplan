import { Component, Input, OnInit } from '@angular/core';

@Component({
  selector: 'app-data-table',
  templateUrl: './data-table.component.html',
  styleUrls: ['./data-table.component.scss']
})
export class DataTableComponent implements OnInit {
  _columns: string[] = [];
  private _rows: any[][] = [];
  sortedRows: any[][] = [];
  sorting: ('asc' | 'desc' | 'none' )[] = [];

  constructor() { }

  ngOnInit(): void {
  }

  @Input() set columns (columns: string[]){
    this._columns = columns;
    this.sorting = Array(columns.length).fill('none');
  };

  @Input() set rows (rows: any[][]){
    this._rows = rows;
    this.sortedRows = this.sort(rows);
  };

  toggleSort(col: number) {
    const prevOrder = this.sorting[col];
    const order = (prevOrder === 'none')? 'asc': (prevOrder === 'asc')? 'desc': 'none';
    // only allow one column to be sorted atm
    this.sorting = Array(this.sorting.length).fill('none');
    this.sorting[col] = order;
    this.sortedRows = this.sort(this._rows);
  }

  // ToDo: inherit in filter table
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
}
