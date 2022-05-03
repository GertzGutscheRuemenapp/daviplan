import { AfterViewInit, Component, TemplateRef, ViewChild } from '@angular/core';
import { Infrastructure, Service, DemandRateSet, Gender, AgeGroup } from "../../../rest-interfaces";
import { RestCacheService } from "../../../rest-cache.service";
import { FormBuilder, FormControl, FormGroup } from "@angular/forms";
import { InputCardComponent } from "../../../dash/input-card.component";
import { HttpClient } from "@angular/common/http";
import { RestAPI } from "../../../rest-api";
import { ConfirmDialogComponent } from "../../../dialogs/confirm-dialog/confirm-dialog.component";
import { MatDialog } from "@angular/material/dialog";
import { RemoveDialogComponent } from "../../../dialogs/remove-dialog/remove-dialog.component";
import { DemandRateSetViewComponent } from "./demand-rate-set-view/demand-rate-set-view.component";
import { DemandTypes } from "../../../rest-interfaces";
import { BehaviorSubject } from "rxjs";

@Component({
  selector: 'app-demand-quotas',
  templateUrl: './demand-quotas.component.html',
  styleUrls: ['./demand-quotas.component.scss']
})
export class DemandQuotasComponent implements AfterViewInit {
  @ViewChild('demandTypeCard') demandTypeCard?: InputCardComponent;
  @ViewChild('propertiesCard') propertiesCard?: InputCardComponent;
  @ViewChild('demandRateSetCard') demandRateSetCard?: InputCardComponent;
  @ViewChild('demandRateSetPreview') demandRateSetPreview?: DemandRateSetViewComponent;
  @ViewChild('propertiesEdit') propertiesEdit?: TemplateRef<any>;
  isLoading$ = new BehaviorSubject<boolean>(false);
  years: number[] = [];
  genders: Gender[] = [];
  ageGroups: AgeGroup[] = [];
  infrastructures: Infrastructure[] = [];
  activeService?: Service;
  activeDemandRateSet?: DemandRateSet;
  editDemandRateSet?: DemandRateSet;
  demandTypes = DemandTypes;
  demandTypeForm: FormGroup;
  propertiesForm: FormGroup;
  demandRateSets: DemandRateSet[] = [];
  demandRateSetCache: Record<number, DemandRateSet[]> = {};

  constructor(private restService: RestCacheService, private formBuilder: FormBuilder,
              private dialog: MatDialog, private http: HttpClient, private rest: RestAPI) {
    this.demandTypeForm = this.formBuilder.group({
      demandType: new FormControl('1')
    });
    this.propertiesForm = this.formBuilder.group({
      name: new FormControl(''),
      description: new FormControl('')
    });
  }

  ngAfterViewInit(): void {
    this.restService.getYears().subscribe(years => this.years = years);
    this.restService.getGenders().subscribe(genders => this.genders = genders);
    this.restService.getAgeGroups().subscribe(ageGroups => this.ageGroups = ageGroups);
    this.isLoading$.next(true);
    this.restService.getInfrastructures().subscribe(infrastructures => {
      this.infrastructures = infrastructures || [];
      if (infrastructures.length === 0) return;
      const services = infrastructures[0].services || [];
      this.isLoading$.next(false);
      if (services.length > 0) {
        this.activeService = services[0];
        this.onServiceChange();
      }
    })
    this.setupDemandTypeCard();
    this.setupPropertiesCard();
    this.setupDemandRateSetCard()
  }

  setupDemandTypeCard(): void {
    this.demandTypeCard?.dialogOpened.subscribe(ok => {
      this.demandTypeForm.reset({
        demandType: String(this.activeService?.demandType)
      });
    })
    this.demandTypeCard?.dialogConfirmed.subscribe((ok)=>{
      this.demandTypeForm.setErrors(null);
      this.demandTypeForm.markAllAsTouched();
      if (this.demandTypeForm.invalid) return;
      let attributes: any = {
        demandType: this.demandTypeForm.value.demandType,
      }
      this.demandTypeCard?.setLoading(true);
      this.http.patch<Service>(`${this.rest.URLS.services}${this.activeService?.id}/`, attributes
      ).subscribe(service => {
        Object.assign(this.activeService!, service);
        this.demandTypeCard?.closeDialog(true);
      },(error) => {
        // ToDo: set specific errors to fields
        this.demandTypeForm.setErrors(error.error);
        this.demandTypeCard?.setLoading(false);
      });
    })
  }

  setupPropertiesCard(): void {
    this.propertiesCard?.dialogOpened.subscribe(ok => {
      this.propertiesForm.reset({
        name: this.activeDemandRateSet?.name,
        description: this.activeDemandRateSet?.description,
      });
    })
    this.propertiesCard?.dialogConfirmed.subscribe((ok)=>{
      this.propertiesForm.setErrors(null);
      this.propertiesForm.markAllAsTouched();
      if (this.propertiesForm.invalid) return;
      let attributes: any = {
        name: this.propertiesForm.value.name,
        description: this.propertiesForm.value.description
      }
      this.propertiesCard?.setLoading(true);
      this.http.patch<DemandRateSet>(`${this.rest.URLS.demandRateSets}${this.activeDemandRateSet?.id}/`, attributes
      ).subscribe(set => {
        Object.assign(this.activeDemandRateSet!, set);
        // trigger reload of demand rate card
        const activeDemandRateSet = this.activeDemandRateSet;
        this.activeDemandRateSet = undefined;
        setTimeout(() => {  this.activeDemandRateSet = activeDemandRateSet; }, 1);
        this.propertiesCard?.closeDialog(true);
      },(error) => {
        // ToDo: set specific errors to fields
        this.propertiesForm.setErrors(error.error);
        this.propertiesCard?.setLoading(false);
      });
    })
  }

  setupDemandRateSetCard(): void {
    this.demandRateSetCard?.dialogConfirmed.subscribe((ok)=>{
      const attributes = { demandRates: this.editDemandRateSet?.demandRates }
      this.demandRateSetCard?.setLoading(true);
      this.http.patch<DemandRateSet>(`${this.rest.URLS.demandRateSets}${this.activeDemandRateSet?.id}/`, attributes
      ).subscribe(set => {
        Object.assign(this.activeDemandRateSet!, set);
        this.demandRateSetPreview!.demandRateSet = set;
        this.demandRateSetCard?.closeDialog(true);
      },(error) => {
        // ToDo: set errors
        this.demandRateSetCard?.setLoading(false);
      });
    })
  }

  createDemandRateSet(): void {
    let dialogRef = this.dialog.open(ConfirmDialogComponent, {
      panelClass: 'absolute',
      width: '300px',
      disableClose: true,
      data: {
        title: 'Neue Nachfragevariante',
        template: this.propertiesEdit,
        closeOnConfirm: false
      }
    });
    dialogRef.afterOpened().subscribe(ok => {
      this.propertiesForm.reset();
    });
    dialogRef.componentInstance.confirmed.subscribe(() => {
      this.propertiesForm.setErrors(null);
      // display errors for all fields even if not touched
      this.propertiesForm.markAllAsTouched();
      if (this.propertiesForm.invalid) return;
      let attributes: any = {
        name: this.propertiesForm.value.name,
        description: this.propertiesForm.value.description || '',
        service: this.activeService?.id
      }
      dialogRef.componentInstance.isLoading$.next(true);
      this.http.post<DemandRateSet>(this.rest.URLS.demandRateSets, attributes
      ).subscribe(set => {
        this.demandRateSets.push(set);
        this.activeDemandRateSet = set;
        this.onDemandRateSetChange();
        dialogRef.close();
      },(error) => {
        this.propertiesForm.setErrors(error.error);
        dialogRef.componentInstance.isLoading$.next(false);
      });
    });
  }

  cloneDemandRateSet(): void {
    if (!this.activeDemandRateSet) return;
    let dialogRef = this.dialog.open(ConfirmDialogComponent, {
      panelClass: 'absolute',
      width: '300px',
      disableClose: true,
      data: {
        title: 'Nachfragevariante klonen',
        template: this.propertiesEdit,
        closeOnConfirm: false
      }
    });
    dialogRef.afterOpened().subscribe(ok => {
      let i = 2;
      let name = '';
      const existingNames = this.demandRateSets.map(drs => drs.name);
      while (true) {
        const newName = `${this.activeDemandRateSet!.name} (${i})`;
        if (existingNames.indexOf(newName) === -1){
          name = newName;
          break;
        }
        i += 1;
      }
      this.propertiesForm.reset({
        name: name,
        description: this.activeDemandRateSet!.description,
      });
    });
    dialogRef.componentInstance.confirmed.subscribe(() => {
      this.propertiesForm.setErrors(null);
      // display errors for all fields even if not touched
      this.propertiesForm.markAllAsTouched();
      if (this.propertiesForm.invalid) return;
      let attributes: any = {
        name: this.propertiesForm.value.name,
        description: this.propertiesForm.value.description || '',
        service: this.activeService?.id,
        demandRates: this.activeDemandRateSet?.demandRates
      }
      dialogRef.componentInstance.isLoading$.next(true);
      this.http.post<DemandRateSet>(this.rest.URLS.demandRateSets, attributes
      ).subscribe(set => {
        this.demandRateSets.push(set);
        this.activeDemandRateSet = set;
        this.onDemandRateSetChange();
        dialogRef.close();
      },(error) => {
        this.propertiesForm.setErrors(error.error);
        dialogRef.componentInstance.isLoading$.next(false);
      });
    });
  }

  removeDemandRateSet(): void {
    if (!this.activeDemandRateSet)
      return;
    const dialogRef = this.dialog.open(RemoveDialogComponent, {
      width: '400px',
      data: {
        title: $localize`Die Nachfragevariante wirklich entfernen?`,
        confirmButtonText: $localize`Variante entfernen`,
        message: `Es werden auch alle bereits definierten Nachfragewerte der Variante entfernt. <br><br> ${this.activeService?.name}`,
        value: this.activeDemandRateSet.name
      }
    });
    dialogRef.afterClosed().subscribe((confirmed: boolean) => {
      if (confirmed) {
        this.http.delete(`${this.rest.URLS.demandRateSets}${this.activeDemandRateSet?.id}/`
        ).subscribe(() => {
          const idx = this.demandRateSets.indexOf(this.activeDemandRateSet!);
          if (idx > -1) {
            this.demandRateSets.splice(idx, 1);
          }
          this.activeDemandRateSet = undefined;
        },(error) => {
          console.log('there was an error sending the query', error);
        });
      }
    });
  }

  onServiceChange(): void {
    if (!this.activeService) return;
    const demandRateSets = this.demandRateSetCache[this.activeService!.id];
    if (demandRateSets) {
      this.demandRateSets = demandRateSets;
      this.activeDemandRateSet = demandRateSets[0];
      this.onDemandRateSetChange();
    }
    else {
      this.isLoading$.next(true);
      this.restService.getDemandRateSets(this.activeService.id).subscribe(sets => {
        this.demandRateSetCache[this.activeService!.id] = sets;
        this.demandRateSets = sets;
        this.activeDemandRateSet = sets[0];
        this.onDemandRateSetChange();
        this.isLoading$.next(false);
      });
    }
  }

  onDemandRateSetChange(): void {
    // deep clone
    this.editDemandRateSet = JSON.parse(JSON.stringify(this.activeDemandRateSet));
  }

  setDefaultDemandRateSet(set: DemandRateSet): void {
    if (!set || set.isDefault) return;
    const attributes = { isDefault: true };
    this.http.patch<DemandRateSet>(`${this.rest.URLS.demandRateSets}${set.id}/`, attributes
    ).subscribe(ds => {
      this.demandRateSets.forEach(s => s.isDefault = false);
      set.isDefault = ds.isDefault;
    })
  }
}
