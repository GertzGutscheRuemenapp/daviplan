import { Component, OnInit } from '@angular/core';
import { mockInfrastructures } from "../../administration/infrastructure/infrastructure.component";

@Component({
  selector: 'app-services',
  templateUrl: './services.component.html',
  styleUrls: ['./services.component.scss']
})
export class ServicesComponent implements OnInit {
  infrastructures = mockInfrastructures;
  selectedInfrastructure = mockInfrastructures[1];
  services = mockInfrastructures[1].services;
  selectedService = mockInfrastructures[1].services[1];

  constructor() { }

  ngOnInit(): void {
  }

}
