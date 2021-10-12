import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-infrastructure',
  templateUrl: './infrastructure.component.html',
  styleUrls: ['./infrastructure.component.scss']
})
export class InfrastructureComponent implements OnInit {
  infrastructures = ['Kinderbetreuung', 'Schulen', 'Ärzte', 'Feuerwehr']
  selectedInfrastructure = 'Kinderbetreuung'

  constructor() { }

  ngOnInit(): void {
  }

}
