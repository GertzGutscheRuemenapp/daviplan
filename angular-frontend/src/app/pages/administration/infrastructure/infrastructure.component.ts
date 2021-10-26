import { Component, OnInit } from '@angular/core';

interface Service {
  id: number,
  name: string;
}

interface Infrastructure {
  id: number,
  name: string;
  description: string;
  services: Service[];
}

export const mockInfrastructures: Infrastructure[] = [
  { id: 1, name: 'Kinderbetreuung', description: 'Platzhalter Kinderbetreuung', services: [{ id: 1, name: 'Kita' }, { id: 2, name: 'Krippe' }]},
  { id: 2, name: 'Schulen', description: 'Platzhalter Schulen', services: [{ id: 3, name: 'Grundschule' }, { id: 4, name: 'Gymnasium' }]},
  { id: 3, name: 'Ärzte', description: 'Platzhalter Ärzte', services: [{ id: 5, name: 'Allgemeinmedizinerin' }, { id: 6, name: 'Internistin' }, { id: 7, name: 'Hautärztin' }]},
  { id: 4, name: 'Feuerwehr', description: 'Platzhalter Feuerwehr', services: [{ id: 8, name: 'Brandschutz???' }, { id: 9, name: '????' }]},
]

@Component({
  selector: 'app-infrastructure',
  templateUrl: './infrastructure.component.html',
  styleUrls: ['./infrastructure.component.scss']
})
export class InfrastructureComponent implements OnInit {
  infrastructures: Infrastructure[] = mockInfrastructures;
  selectedInfrastructure: Infrastructure = mockInfrastructures[0];

  constructor() { }

  ngOnInit(): void {
  }

}
