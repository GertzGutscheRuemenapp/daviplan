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
  @Input() rows!: any[][];
  filtered = [false, false, false, false, false, false];
  // sorting: ('asc' | 'desc' | 'none')[];
  sorting: ('asc' | 'desc' | 'none' )[] = [];

  constructor() {
  }

  toggleSort(column: number) {
    const prevOrder = this.sorting[column];
    // const order = (prevOrder === 'none')? 'asc': (prevOrder === 'asc')? 'desc': 'none';
    const order = (prevOrder === 'asc')? 'desc': 'asc';
    this.sorting[column] = order;
    // if (order === 'none') return;
    this.rows.sort((a, b) => {
      if (a[column] === b[column]) return 0;
      if (order === 'asc' && a[column] > b[column]) return 1;
      if (order === 'desc' && a[column] < b[column]) return 1;
      return -1;
    })
  }

  ngOnInit(): void {
    this.sorting = Array(this.header.length).fill('none');
  }

}
