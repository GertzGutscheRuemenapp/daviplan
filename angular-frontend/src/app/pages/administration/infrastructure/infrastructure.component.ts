import { AfterViewInit, Component, TemplateRef, ViewChild } from '@angular/core';
import { HttpClient } from "@angular/common/http";
import { RestAPI } from "../../../rest-api";
import { Observable } from "rxjs";
import { ConfirmDialogComponent } from "../../../dialogs/confirm-dialog/confirm-dialog.component";
import { MatDialog } from "@angular/material/dialog";
import { FormBuilder, FormControl, FormGroup } from "@angular/forms";
import { InputCardComponent } from "../../../dash/input-card.component";
import { RemoveDialogComponent } from "../../../dialogs/remove-dialog/remove-dialog.component";
import { arrayMove } from "../../../helpers/utils";
import { Infrastructure, Symbol } from "../../../rest-interfaces"


export const mockInfrastructures: Infrastructure[] = [
  { id: 1, order: 1, name: 'Kinderbetreuung', description: 'Betreuung von Kindern in Einrichtungen, ohne Tagespflege', services: [{ id: 1, infrastructure: 1, description: '', name: 'Kita' }, { id: 2, description: '', infrastructure: 1, name: 'Krippe' }]},
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
      this.infrastructures = this.sortInfrastructures(infrastructures);
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
    const dialogRef = this.dialog.open(RemoveDialogComponent, {
      data: {
        title: $localize`Die Infrastruktur wirklich entfernen?`,
        confirmButtonText: $localize`Infrastruktur entfernen`,
        value: this.selectedInfrastructure?.name
      }
    });
    dialogRef.afterClosed().subscribe((confirmed: boolean) => {
      if (confirmed) {
        this.http.delete(`${this.rest.URLS.infrastructures}${this.selectedInfrastructure?.id}/`
        ).subscribe(res => {
          const idx = this.infrastructures.indexOf(this.selectedInfrastructure!);
          if (idx > -1) {
            this.infrastructures.splice(idx, 1);
          }
          this.selectedInfrastructure = undefined;
          this.patchOrder();
        },(error) => {
          console.log('there was an error sending the query', error);
        });
      }
    });
  }

  sortInfrastructures(infrastructures: Infrastructure[]): Infrastructure[] {
    return infrastructures.sort((a, b) =>
      (a.order > b.order)? 1: (a.order < b.order)? -1: 0);
  }

  /**
   * patches layer.order of infrastructures to their current place in the array
   *
   */
  patchOrder(): void {
    for ( let i = 0; i < this.infrastructures.length; i += 1){
      const infrastructure = this.infrastructures[i];
      this.http.patch<Infrastructure>(`${this.rest.URLS.infrastructures}${infrastructure.id}/`,
        { order: i + 1 }).subscribe(res => {
          infrastructure.order = res.order;
      });
    }
  }

  moveSelectedUp(): void {
    if (!this.selectedInfrastructure) return;
    const idx = this.infrastructures.indexOf(this.selectedInfrastructure);
    if (idx <= 0) return;
    arrayMove(this.infrastructures, idx, idx - 1);
    this.patchOrder();
  }

  moveSelectedDown(): void {
    if (!this.selectedInfrastructure) return;
    const idx = this.infrastructures.indexOf(this.selectedInfrastructure);
    if (idx === -1 || idx === this.infrastructures.length - 1) return;
    arrayMove(this.infrastructures, idx, idx + 1);
    this.patchOrder();
  }
}
