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
  filtered = [true, false, false, true, false, false];

  constructor() { }

  ngOnInit(): void {
  }

}
