import { Component, OnInit, TemplateRef, ViewChild } from '@angular/core';
import { mockInfrastructures } from "../../administration/infrastructure/infrastructure.component";
import { ConfirmDialogComponent } from "../../../dialogs/confirm-dialog/confirm-dialog.component";
import { MatDialog } from "@angular/material/dialog";
import { Infrastructure, Service } from "../../../rest-interfaces";

@Component({
  selector: 'app-services',
  templateUrl: './services.component.html',
  styleUrls: ['./services.component.scss']
})
export class ServicesComponent implements OnInit {
  @ViewChild('createService') createServiceTemplate?: TemplateRef<any>;
  services: Service[];
  infrastructures: Infrastructure[];
  selectedService: Service;

  constructor(private dialog: MatDialog) {
    this.infrastructures = mockInfrastructures;
    this.services = mockInfrastructures[0].services;
    this.selectedService = mockInfrastructures[0].services[0];
  }

  ngOnInit(): void {
  }

  onCreateService() {
    let dialogRef = this.dialog.open(ConfirmDialogComponent, {
      panelClass: 'absolute',
      width: '300px',
      disableClose: true,
      data: {
        title: 'Neue Leistung',
        template: this.createServiceTemplate,
        closeOnConfirm: false
      }
    });
  }
}
