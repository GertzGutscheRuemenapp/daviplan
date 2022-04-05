import { AfterViewInit, Component, TemplateRef, ViewChild } from '@angular/core';
import { ConfirmDialogComponent } from "../../../dialogs/confirm-dialog/confirm-dialog.component";
import { MatDialog } from "@angular/material/dialog";
import { Infrastructure, Service } from "../../../rest-interfaces";
import { RestCacheService } from "../../../rest-cache.service";
import { HttpClient } from "@angular/common/http";
import { RestAPI } from "../../../rest-api";
import { FormBuilder, FormGroup } from "@angular/forms";
import { InputCardComponent } from "../../../dash/input-card.component";

@Component({
  selector: 'app-services',
  templateUrl: './services.component.html',
  styleUrls: ['./services.component.scss']
})
export class ServicesComponent implements AfterViewInit {
  @ViewChild('createService') createServiceTemplate?: TemplateRef<any>;
  @ViewChild('propertiesCard') propertiesCard!: InputCardComponent;
  @ViewChild('capacitiesCard') capacitiesCard!: InputCardComponent;
  infrastructures?: Infrastructure[];
  activeService?: Service;
  indicators: any[] = [];
  propertiesForm: FormGroup;
  capacitiesForm: FormGroup;
  Object = Object;

  constructor(private dialog: MatDialog, private http: HttpClient,
              private restService: RestCacheService, private rest: RestAPI,
              private formBuilder: FormBuilder) {
    this.propertiesForm = this.formBuilder.group({
      name: '',
      description: ''
    });
    this.capacitiesForm = this.formBuilder.group({
      hasCapacity: false,
      capacitySingularUnit: '',
      capacityPluralUnit: '',
      demandSingularUnit: '',
      demandPluralUnit: '',
      facilityArticle: '',
      facilitySingularUnit: '',
      facilityPluralUnit: '',
      directionWayRelationship: 'To'
    });
  }

  ngAfterViewInit(): void {
    this.restService.getInfrastructures().subscribe(infrastructures => {
      this.infrastructures = infrastructures || [];
      if (infrastructures.length === 0) return;
      const services = infrastructures[0].services || [];
      if (services.length > 0) {
        this.activeService = services[0];
        this.onServiceChange();
      }
    })
    this.setupPropertiesCard();
    this.setupCapacitiesCard();
  }

  setupPropertiesCard() {
    this.propertiesCard.dialogOpened.subscribe(() => {
      this.propertiesForm.reset({
        name: this.activeService!.name,
        description: this.activeService!.description
      });
    })
  }

  setupCapacitiesCard() {
    this.capacitiesCard.dialogOpened.subscribe(() => {
      this.capacitiesForm.reset({
        hasCapacity: this.activeService!.hasCapacity,
        capacitySingularUnit: this.activeService!.capacitySingularUnit,
        capacityPluralUnit: this.activeService!.capacityPluralUnit,
        demandSingularUnit: this.activeService!.demandSingularUnit,
        demandPluralUnit: this.activeService!.demandPluralUnit,
        facilityArticle: this.activeService!.facilityArticle,
        facilitySingularUnit: this.activeService!.facilitySingularUnit,
        facilityPluralUnit: this.activeService!.facilityPluralUnit,
        directionWayRelationship: this.activeService!.directionWayRelationship
      });
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
