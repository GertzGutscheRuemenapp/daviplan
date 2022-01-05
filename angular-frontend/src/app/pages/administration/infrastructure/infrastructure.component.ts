import { AfterViewInit, Component, TemplateRef, ViewChild } from '@angular/core';
import { HttpClient } from "@angular/common/http";
import { RestAPI } from "../../../rest-api";
import { Observable } from "rxjs";
import { User } from "../../login/users";
import { ConfirmDialogComponent } from "../../../dialogs/confirm-dialog/confirm-dialog.component";
import { MatDialog } from "@angular/material/dialog";
import { FormBuilder, FormControl, FormGroup } from "@angular/forms";
import { InputCardComponent } from "../../../dash/input-card.component";

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
  { id: 1, name: 'Kinderbetreuung', description: 'Betreuung von Kindern in Einrichtungen, ohne Tagespflege', services: [{ id: 1, name: 'Kita' }, { id: 2, name: 'Krippe' }]},
  { id: 2, name: 'Schulen', description: 'Allgemeinbildende Schulen ohne Privatschulen und ohne berufsbildende Schulen', services: [{ id: 3, name: 'Grundschule' }, { id: 4, name: 'Gymnasium' }]},
  { id: 3, name: 'Ärzte', description: 'Haus- und fachärztliche Versorgung. Fachärzte eingeschränkt auf Kinderärzte, Frauenärzte, Augenärzte und Internisten.', services: [{ id: 5, name: 'Allgemeinmedizinerin' }, { id: 6, name: 'Internistin' }, { id: 7, name: 'Hautärztin' }]},
  { id: 4, name: 'Feuerwehr', description: 'Nicht-polizeiliche Gefahrenabwehr, insbesondere durch die freiwilligen Feuerwehren.', services: [{ id: 8, name: 'Brandschutz???' }, { id: 9, name: '????' }]},
]

@Component({
  selector: 'app-infrastructure',
  templateUrl: './infrastructure.component.html',
  styleUrls: ['./infrastructure.component.scss']
})
export class InfrastructureComponent implements AfterViewInit  {
  infrastructures: Infrastructure[] = [];
  selectedInfrastructure?: Infrastructure;
  infrastructureForm: FormGroup;
  @ViewChild('infrastructureEditCard') infrastructureEditCard?: InputCardComponent;
  @ViewChild('infrastructureEdit') infrastructureEditTemplate?: TemplateRef<any>;
  @ViewChild('removeInfrastructureTemplate') removeInfrastructureTemplate?: TemplateRef<any>;
  Object = Object;

  constructor(private http: HttpClient, private rest: RestAPI,
              private dialog: MatDialog, private formBuilder: FormBuilder) {
    this.infrastructureForm = this.formBuilder.group({
      name: new FormControl(''),
      description: new FormControl('')
    });
  }

  ngAfterViewInit() {
    this.fetchInfrastructures();
    this.setupInfrastructureCard();
  }

  fetchInfrastructures(): Observable<Infrastructure[]> {
    let query = this.http.get<Infrastructure[]>(this.rest.URLS.infrastructures);
    query.subscribe((infrastructures) => {
      this.infrastructures = infrastructures;
      this.selectedInfrastructure = (infrastructures.length > 0)? infrastructures[0]: undefined;
    });
    return query;
  }

  setupInfrastructureCard(): void {
    this.infrastructureEditCard?.dialogOpened.subscribe(ok => {
      this.infrastructureForm.reset({
        name: this.selectedInfrastructure?.name,
        description: this.selectedInfrastructure?.description,
      });
    })
    this.infrastructureEditCard?.dialogConfirmed.subscribe((ok)=>{
      this.infrastructureForm.setErrors(null);
      // display errors for all fields even if not touched
      this.infrastructureForm.markAllAsTouched();
      if (this.infrastructureForm.invalid) return;
      let attributes: any = {
        name: this.infrastructureForm.value.name,
        description: this.infrastructureForm.value.description
      }
      this.infrastructureEditCard?.setLoading(true);
      this.http.patch<Infrastructure>(`${this.rest.URLS.infrastructures}${this.selectedInfrastructure?.id}/`, attributes
      ).subscribe(infrastructure => {
        this.selectedInfrastructure!.name = infrastructure.name;
        this.selectedInfrastructure!.description = infrastructure.description;
        this.infrastructureEditCard?.closeDialog(true);
      },(error) => {
        // ToDo: set specific errors to fields
        this.infrastructureForm.setErrors(error.error);
        this.infrastructureEditCard?.setLoading(false);
      });
    })
    this.infrastructureEditCard?.dialogClosed.subscribe(ok => {
      this.infrastructureForm.reset()
    })
  }

  addInfrastructure(): void {
    let dialogRef = this.dialog.open(ConfirmDialogComponent, {
      panelClass: 'absolute',
      width: '300px',
      disableClose: true,
      data: {
        title: 'Neue Infrastruktur',
        template: this.infrastructureEditTemplate,
        closeOnConfirm: false
      }
    });
    dialogRef.afterClosed().subscribe(ok => {
      this.infrastructureForm.reset();
    });
    dialogRef.componentInstance.confirmed.subscribe(() => {
      this.infrastructureForm.setErrors(null);
      // display errors for all fields even if not touched
      this.infrastructureForm.markAllAsTouched();
      if (this.infrastructureForm.invalid) return;
      let attributes: any = {
        name: this.infrastructureForm.value.name,
        description: this.infrastructureForm.value.description
      }
      dialogRef.componentInstance.isLoading = true;
      this.http.post<Infrastructure>(this.rest.URLS.infrastructures, attributes
      ).subscribe(infrastructure => {
        this.infrastructures.push(infrastructure);
        this.selectedInfrastructure = infrastructure;
        dialogRef.close();
      },(error) => {
        this.infrastructureForm.setErrors(error.error);
        dialogRef.componentInstance.isLoading = false;
      });
    });
  }

  removeInfrastructure(): void {
    if (!this.selectedInfrastructure)
      return;
    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      width: '400px',
      data: {
        title: $localize`Die Infrastruktur wirklich entfernen?`,
        confirmButtonText: $localize`Infrastruktur entfernen`,
        template: this.removeInfrastructureTemplate,
        closeOnConfirm: true
      },
      panelClass: 'warning'
    });
    dialogRef.afterClosed().subscribe((confirmed: boolean) => {
      if (confirmed === true) {
        this.http.delete(`${this.rest.URLS.infrastructures}${this.selectedInfrastructure?.id}/`
        ).subscribe(res => {
          const idx = this.infrastructures.indexOf(this.selectedInfrastructure!);
          if (idx > -1) {
            this.infrastructures.splice(idx, 1);
          }
          this.selectedInfrastructure = undefined;
        },(error) => {
          console.log('there was an error sending the query', error);
        });
      }
    });

  }
}
