import { Component, Input, OnInit } from '@angular/core';

export interface Header {
  name: string
}

@Component({
  selector: 'app-filter-table',
  templateUrl: './filter-table.component.html',
  styleUrls: ['./filter-table.component.scss']
})
export class FilterTableComponent implements OnInit {
  @Input() header!: string[];
  _rows: any[][] = [];
  private _sortIdx: number[] = [];
  filtered = [false, false, false, false, false, false];
  sorting: ('asc' | 'desc' | 'none' )[] = [];

  constructor() { }

  @Input() set rows (rows: any[][]){
    let i = -1;
    // add a row number to identify original row in case of sorting
    this._rows = rows.map(row => {
      i += 1;
      return row.concat([i]);
    });
  };

  toggleSort(column: number) {
    const prevOrder = this.sorting[column];
    // const order = (prevOrder === 'none')? 'asc': (prevOrder === 'asc')? 'desc': 'none';
    const order = (prevOrder === 'asc')? 'desc': 'asc';
    this.sorting[column] = order;
    // if (order === 'none') return;
    this._rows.sort((a, b) => {
      if (a[column] === b[column]) return 0;
      if (order === 'asc' && a[column] > b[column]) return 1;
      if (order === 'desc' && a[column] < b[column]) return 1;
      return -1;
    })
    this._sortIdx = [];
    const indices = this._rows.map(r => r[r.length - 1]);
    for (let i = 0; i < this._rows.length; i++){
      this._sortIdx.push(indices.indexOf(i));
    }
  }

  updateColumn(column: number, values: any[]): void {
    values.forEach((value, i) => this._rows[this._sortIdx[i]][column] = values[i]);
  }

  ngOnInit(): void {
    this.sorting = Array(this.header.length).fill('none');
  }

}
