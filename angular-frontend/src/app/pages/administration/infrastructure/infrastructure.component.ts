import { Component, OnInit } from '@angular/core';

export const infrastructures = ['Kinderbetreuung', 'Schulen', 'Ärzte', 'Feuerwehr'];

@Component({
  selector: 'app-infrastructure',
  templateUrl: './infrastructure.component.html',
  styleUrls: ['./infrastructure.component.scss']
})
export class InfrastructureComponent implements OnInit {
  infrastructures = infrastructures
  selectedInfrastructure = 'Kinderbetreuung'

  constructor() { }

  ngOnInit(): void {
  }

}
