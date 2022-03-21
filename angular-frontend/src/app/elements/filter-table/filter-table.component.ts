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
  _header: string[] = [];
  _sorted: any[][] = [];
  _rows: any[][] = [];
  filtered = [false, false, false, false, false, false];
  sorting: ('asc' | 'desc' | 'none' )[] = [];

  constructor() { }

  @Input() set header (header: string[]){
    this._header = header;
    if (header)
      this.sorting = Array(this.header.length).fill('none');
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

  toggleSort(column: number) {
    const prevOrder = this.sorting[column];
    const order = (prevOrder === 'none')? 'asc': (prevOrder === 'asc')? 'desc': 'none';
    this.sorting[column] = order;
    this.sort();
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
