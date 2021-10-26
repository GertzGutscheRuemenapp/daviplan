import { Component, Input, OnInit } from '@angular/core';

const mockHeader = ['Name', 'Zustand', 'Anzahl Betreuer', 'Kapazität Krippe', 'Kapazität Kita', 'Adresse']
const mockRows = [
  ['KIGA Nord', 'gut', 12, 28, 22, 'Paul Ehrlich Straße 3, 35029 Bremen'],
  ['Krippe Westentchen', 'sehr gut', 20, 80, 0, 'Cuxhavener Landstraße 2, 35029 Bremen'],
  ['Kita Süd', 'befriedigend', 6, 10, 20, 'Diepholzer Weg 133, 35029 Bremen'],
  ['Katholische Kita Mitte', 'gut', 2, 8, 12, 'Kirchenallee 24, 35029 Bremen'],
]

@Component({
  selector: 'app-filter-table',
  templateUrl: './filter-table.component.html',
  styleUrls: ['./filter-table.component.scss']
})
export class FilterTableComponent implements OnInit {
  @Input() header = mockHeader;
  @Input() rows = mockRows;
  filtered = [true, false, false, true, false, false];

  constructor() { }

  ngOnInit(): void {
  }

}
