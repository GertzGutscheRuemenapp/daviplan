import { Component, OnInit } from '@angular/core';
import { mockInfrastructures } from "../../administration/infrastructure/infrastructure.component";

@Component({
  selector: 'app-reachabilities',
  templateUrl: './reachabilities.component.html',
  styleUrls: ['./reachabilities.component.scss']
})
export class ReachabilitiesComponent implements OnInit {
  selectMode = false;
  transportMode = 1;
  indicator = 'option 1';
  selectFacMode = false;
  selectLivMode = false;
  infrastructures = mockInfrastructures;
  selectedInfrastructure = this.infrastructures[0];

  constructor() { }

  ngOnInit(): void {
  }

  toggleIndicator(): void {
    this.selectFacMode = false;
    this.selectLivMode = false;
  }

}
