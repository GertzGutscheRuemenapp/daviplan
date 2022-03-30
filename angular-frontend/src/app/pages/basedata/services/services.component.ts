import { Component, OnInit, TemplateRef, ViewChild } from '@angular/core';
import { ConfirmDialogComponent } from "../../../dialogs/confirm-dialog/confirm-dialog.component";
import { MatDialog } from "@angular/material/dialog";
import { Infrastructure, Service } from "../../../rest-interfaces";
import { RestCacheService } from "../../../rest-cache.service";
import { HttpClient } from "@angular/common/http";
import { RestAPI } from "../../../rest-api";

@Component({
  selector: 'app-services',
  templateUrl: './services.component.html',
  styleUrls: ['./services.component.scss']
})
export class ServicesComponent implements OnInit {
  @ViewChild('createService') createServiceTemplate?: TemplateRef<any>;
  infrastructures?: Infrastructure[];
  activeService?: Service;
  indicators: any[] = [];

  constructor(private dialog: MatDialog, private http: HttpClient,
              private restService: RestCacheService, private rest: RestAPI) {}

  ngOnInit(): void {
    this.restService.getInfrastructures().subscribe(infrastructures => {
      this.infrastructures = infrastructures || [];
      if (infrastructures.length === 0) return;
      const services = infrastructures[0].services || [];
      if (services.length > 0) {
        this.activeService = services[0];
        this.onServiceChange();
      }
    })
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

  onServiceChange() {
    if (!this.activeService) {
      this.indicators = [];
      return;
    }
    this.http.get<any>(`${this.rest.URLS.services}${this.activeService.id}/get_indicators/`).subscribe(indicators => {
      this.indicators = indicators;
    })
  }
}
