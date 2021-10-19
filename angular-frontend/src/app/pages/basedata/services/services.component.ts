import { Component, OnInit } from '@angular/core';
import { infrastructures } from "../../administration/infrastructure/infrastructure.component";

@Component({
  selector: 'app-services',
  templateUrl: './services.component.html',
  styleUrls: ['./services.component.scss']
})
export class ServicesComponent implements OnInit {
  infrastructures = infrastructures;
  selectedInfrastructure = infrastructures[1];
  services = ['Grundschule', 'Gymnasium'];
  selectedService = 'Gymnasium';

  constructor() { }

  ngOnInit(): void {
  }

}
