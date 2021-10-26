import { Component, OnInit } from '@angular/core';
import { mockInfrastructures } from "../../administration/infrastructure/infrastructure.component";

@Component({
  selector: 'app-demand',
  templateUrl: './demand.component.html',
  styleUrls: ['./demand.component.scss']
})
export class DemandComponent implements OnInit {
  years = [2009, 2010, 2012, 2013, 2015, 2017, 2020, 2025];
  compareSupply = true;
  compareStatus = 'option 1';
  infrastructures = mockInfrastructures;
  selectedInfrastructure = this.infrastructures[0];

  constructor() { }

  ngOnInit(): void {
  }
}
