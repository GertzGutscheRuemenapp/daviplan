import { AfterViewInit, Component, TemplateRef, ViewChild } from '@angular/core';
import { ConfirmDialogComponent } from "../../../dialogs/confirm-dialog/confirm-dialog.component";
import { MatDialog } from "@angular/material/dialog";
import { AreaLevel, Infrastructure, Service } from "../../../rest-interfaces";
import { RestCacheService } from "../../../rest-cache.service";
import { HttpClient } from "@angular/common/http";
import { RestAPI } from "../../../rest-api";
import { FormBuilder, FormGroup } from "@angular/forms";
import { InputCardComponent } from "../../../dash/input-card.component";
import { RemoveDialogComponent } from "../../../dialogs/remove-dialog/remove-dialog.component";

@Component({
  selector: 'app-services',
  templateUrl: './services.component.html',
  styleUrls: ['./services.component.scss']
})
export class ServicesComponent implements AfterViewInit {
  @ViewChild('createService') createServiceTemplate?: TemplateRef<any>;
  @ViewChild('propertiesCard') propertiesCard!: InputCardComponent;
  @ViewChild('capacitiesCard') capacitiesCard!: InputCardComponent;
  @ViewChild('demandCard') demandCard!: InputCardComponent;
  infrastructures?: Infrastructure[];
  activeService?: Service;
  indicators: any[] = [];
  propertiesForm: FormGroup;
  serviceForm: FormGroup;
  capacitiesForm: FormGroup;
  demandForm: FormGroup;
  Object = Object;

  constructor(private dialog: MatDialog, private http: HttpClient,
              private restService: RestCacheService, private rest: RestAPI,
              private formBuilder: FormBuilder) {
    this.propertiesForm = this.formBuilder.group({
      name: '',
      description: ''
    });
    this.serviceForm = this.formBuilder.group({
      name: '',
      infrastructure: null
    });
    this.capacitiesForm = this.formBuilder.group({
      hasCapacity: false,
      capacitySingularUnit: '',
      capacityPluralUnit: '',
      facilityArticle: '',
      facilitySingularUnit: '',
      facilityPluralUnit: ''
    });
    this.demandForm = this.formBuilder.group({
      demandSingularUnit: '',
      demandPluralUnit: '',
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
    this.setupDemandCard();
  }

  setupPropertiesCard() {
    this.propertiesCard.dialogOpened.subscribe(() => {
      this.propertiesForm.reset({
        name: this.activeService!.name,
        description: this.activeService!.description
      });
    })
    this.propertiesCard.dialogConfirmed.subscribe((ok)=>{
      this.propertiesForm.setErrors(null);
      // display errors for all fields even if not touched
      this.propertiesForm.markAllAsTouched();
      if (this.propertiesForm.invalid) return;
      let attributes: any = {
        name: this.propertiesForm.value.name,
        description: this.propertiesForm.value.description || '',
      }
      this.propertiesCard.setLoading(true);
      this.http.patch<Service>(`${this.rest.URLS.services}${this.activeService!.id}/`, attributes
      ).subscribe(service => {
        Object.assign(this.activeService!, service);
        this.onServiceChange();
        this.propertiesCard.closeDialog(true);
      },(error) => {
        // ToDo: set specific errors to fields
        this.propertiesForm.setErrors(error.error);
        this.propertiesCard.setLoading(false);
      });
    })
  }

  setupCapacitiesCard() {
    this.capacitiesCard.dialogOpened.subscribe(() => {
      this.capacitiesForm.reset({
        hasCapacity: this.activeService!.hasCapacity,
        capacitySingularUnit: this.activeService!.capacitySingularUnit,
        capacityPluralUnit: this.activeService!.capacityPluralUnit,
        facilityArticle: this.activeService!.facilityArticle || 'die',
        facilitySingularUnit: this.activeService!.facilitySingularUnit,
        facilityPluralUnit: this.activeService!.facilityPluralUnit,
      });
    })
    this.capacitiesCard.dialogConfirmed.subscribe((ok)=>{
      this.capacitiesForm.setErrors(null);
      // display errors for all fields even if not touched
      this.capacitiesForm.markAllAsTouched();
      if (this.capacitiesForm.invalid) return;
      let attributes: any = {
        hasCapacity:  this.capacitiesForm.value.hasCapacity,
        facilityArticle: this.capacitiesForm.value.facilityArticle || '',
        facilitySingularUnit: this.capacitiesForm.value.facilitySingularUnit || '',
        facilityPluralUnit: this.capacitiesForm.value.facilityPluralUnit || ''
      }
      if (this.capacitiesForm.value.hasCapacity){
        attributes.capacitySingularUnit = this.capacitiesForm.value.capacitySingularUnit || '';
        attributes.capacityPluralUnit = this.capacitiesForm.value.capacityPluralUnit || '';
      }
      this.capacitiesCard.setLoading(true);
      this.http.patch<Service>(`${this.rest.URLS.services}${this.activeService!.id}/`, attributes
      ).subscribe(service => {
        Object.assign(this.activeService!, service);
        this.onServiceChange();
        this.capacitiesCard.closeDialog(true);
      },(error) => {
        // ToDo: set specific errors to fields
        this.capacitiesForm.setErrors(error.error);
        this.capacitiesCard.setLoading(false);
      });
    })
  }

  setupDemandCard() {
    this.demandCard.dialogOpened.subscribe(() => {
      this.demandForm.reset({
        demandSingularUnit: this.activeService!.demandSingularUnit,
        demandPluralUnit: this.activeService!.demandPluralUnit,
        directionWayRelationship: this.activeService!.directionWayRelationship
      });
    })
    this.demandCard.dialogConfirmed.subscribe((ok)=>{
      this.demandForm.setErrors(null);
      // display errors for all fields even if not touched
      this.demandForm.markAllAsTouched();
      if (this.demandForm.invalid) return;
      let attributes: any = {
        demandSingularUnit: this.demandForm.value.demandSingularUnit || '',
        demandPluralUnit: this.demandForm.value.demandPluralUnit || '',
        directionWayRelationship: this.demandForm.value.directionWayRelationship
      }
      this.demandCard.setLoading(true);
      this.http.patch<Service>(`${this.rest.URLS.services}${this.activeService!.id}/`, attributes
      ).subscribe(service => {
        Object.assign(this.activeService!, service);
        this.onServiceChange();
        this.demandCard.closeDialog(true);
      },(error) => {
        // ToDo: set specific errors to fields
        this.demandForm.setErrors(error.error);
        this.demandCard.setLoading(false);
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
    dialogRef.afterOpened().subscribe(() => {
      this.serviceForm.reset();
    })
    dialogRef.componentInstance.confirmed.subscribe(() => {
      // display errors for all fields even if not touched
      this.serviceForm.markAllAsTouched();
      if (this.serviceForm.invalid) return;
      dialogRef.componentInstance.isLoading$.next(true);
      let attributes = {
        name: this.serviceForm.value.name,
        infrastructure: this.serviceForm.value.infrastructure
      };
      this.http.post<Service>(this.rest.URLS.services, attributes
      ).subscribe(service => {
        const infrastructure = this.infrastructures!.find(i => i.id === service.infrastructure);
        infrastructure?.services.push(service);
        dialogRef.close();
      },(error) => {
        this.serviceForm.setErrors(error.error);
        dialogRef.componentInstance.isLoading$.next(false);
      });
    });
  }

  onDeleteService(): void {
    if (!this.activeService)
      return;
    const dialogRef = this.dialog.open(RemoveDialogComponent, {
      width: '400px',
      data: {
        title: $localize`Die Leistung wirklich entfernen?`,
        message: 'Die Entfernung der Leistung entfernt auch alle damit verknüpften Daten aus der Datenbank (z.B. die Standortkapazitäten der Leistung)',
        confirmButtonText: $localize`Leistung entfernen`,
        value: this.activeService.name
      }
    });
    dialogRef.afterClosed().subscribe((confirmed: boolean) => {
      if (confirmed) {
        this.http.delete(`${this.rest.URLS.services}${this.activeService!.id}/`
        ).subscribe(res => {
          const infrastructure = this.infrastructures!.find(i => i.id === this.activeService!.infrastructure);
          if (!infrastructure) return;
          const idx = infrastructure?.services.indexOf(this.activeService!);
          if (idx >= 0)
            infrastructure.services.splice(idx, 1);
          this.activeService = undefined;
        }, error => {
          console.log('there was an error sending the query', error);
        });
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
