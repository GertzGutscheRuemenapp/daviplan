import { Component, OnInit, ViewChild } from '@angular/core';
import { FormControl } from "@angular/forms";
import { MatDatepicker } from "@angular/material/datepicker";

@Component({
  selector: 'app-supply',
  templateUrl: './supply.component.html',
  styleUrls: ['./supply.component.scss']
})
export class SupplyComponent implements OnInit{
  activeInfrastructure: string = '';
  compareYear = 2025;
  addPlaceMode = false;
  @ViewChild('compareYearPicker', {static: false}) private compareYearPicker?: MatDatepicker<Date>;

  constructor() {}

  ngOnInit(): void {
  }

  chosenYearHandler(ev: any): void {
    this.compareYearPicker?.close();
    this.compareYear = ev.getFullYear();
  }
}
