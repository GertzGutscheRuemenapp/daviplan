import { Component, OnInit, TemplateRef, ViewChild } from '@angular/core';
import { mockInfrastructures } from "../../administration/infrastructure/infrastructure.component";
import { ConfirmDialogComponent } from "../../../dialogs/confirm-dialog/confirm-dialog.component";
import { MatDialog } from "@angular/material/dialog";

@Component({
  selector: 'app-services',
  templateUrl: './services.component.html',
  styleUrls: ['./services.component.scss']
})
export class ServicesComponent implements OnInit {
  infrastructures = mockInfrastructures;
  services = mockInfrastructures[1].services;
  selectedService = mockInfrastructures[1].services[1];
  @ViewChild('createService') createServiceTemplate?: TemplateRef<any>;

  constructor(private dialog: MatDialog) { }

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
