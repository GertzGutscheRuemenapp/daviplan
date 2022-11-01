import { Component, Input, OnInit, TemplateRef, ViewChild } from '@angular/core';
import { FClass, FieldType } from "../../../../rest-interfaces";
import { BehaviorSubject, Observable } from "rxjs";
import { RestAPI } from "../../../../rest-api";
import { HttpClient } from "@angular/common/http";
import { MatDialog } from "@angular/material/dialog";
import { RemoveDialogComponent } from "../../../../dialogs/remove-dialog/remove-dialog.component";
import { FormBuilder, FormControl, FormGroup } from "@angular/forms";
import { ConfirmDialogComponent } from "../../../../dialogs/confirm-dialog/confirm-dialog.component";
import { arrayMove } from "../../../../helpers/utils";

@Component({
  selector: 'app-classifications',
  templateUrl: './classifications.component.html',
  styleUrls: ['./classifications.component.scss']
})
export class ClassificationsComponent implements OnInit {
  @Input() classifications: FieldType[] = [];
  @ViewChild('nameTemplate') nameTemplate?: TemplateRef<any>;
  orderIsChanging$ = new BehaviorSubject<boolean>(false);
  selectedClassification?: FieldType;
  selectedClass?: FClass;
  nameForm: FormGroup;

  constructor(private rest: RestAPI, private http: HttpClient, private dialog: MatDialog,
              private formBuilder: FormBuilder) {
    this.nameForm = this.formBuilder.group({
      name: new FormControl('')
    });
  }

  ngOnInit(): void {}

  addClassification(): void {
    let dialogRef = this.dialog.open(ConfirmDialogComponent, {
      panelClass: 'absolute',
      width: '300px',
      disableClose: true,
      data: {
        title: 'Neue Klassifikation',
        template: this.nameTemplate,
        closeOnConfirm: false
      }
    });
    dialogRef.afterClosed().subscribe(() => {
      this.nameForm.reset();
    });
    dialogRef.componentInstance.confirmed.subscribe(() => {
      // display errors for all fields even if not touched
      this.nameForm.markAllAsTouched();
      if (this.nameForm.invalid) return;
      let attributes = {
        name: this.nameForm.value.name,
        ftype: 'CLA'
      };
      this.http.post<FieldType>(this.rest.URLS.fieldTypes, attributes
      ).subscribe(fieldType => {
        this.classifications.push(fieldType);
        this.selectedClassification = fieldType;
        dialogRef.close();
      },(error) => {
        this.nameForm.setErrors(error.error);
      });
    });
  }

  renameClassification(): void {
    if (!this.selectedClassification) return;
    let dialogRef = this.dialog.open(ConfirmDialogComponent, {
      panelClass: 'absolute',
      width: '300px',
      disableClose: true,
      data: {
        title: ' Klassifikation umbenennen',
        template: this.nameTemplate,
        closeOnConfirm: false
      }
    });
    dialogRef.afterOpened().subscribe(() => {
      this.nameForm.reset({ name: this.selectedClassification?.name });
    });
    dialogRef.afterClosed().subscribe(() => {
      this.nameForm.reset();
    });
    dialogRef.componentInstance.confirmed.subscribe(() => {
      // display errors for all fields even if not touched
      this.nameForm.markAllAsTouched();
      if (this.nameForm.invalid) return;
      this.patchClassificaton(this.selectedClassification!.id,{ name: this.nameForm.value.name }).subscribe(fieldType => {
        this.selectedClassification!.name = fieldType.name;
        dialogRef.close();
      },(error) => {
        this.nameForm.setErrors(error.error);
      });
    });
  }

  removeClassification(): void {
    if (!this.selectedClassification)
      return;
    const dialogRef = this.dialog.open(RemoveDialogComponent, {
      width: '500px',
      data: {
        title: $localize`Die Klassifikation wirklich entfernen?`,
        confirmButtonText: $localize`Klassifikation entfernen`,
        value: this.selectedClassification?.name
      }
    });
    dialogRef.afterClosed().subscribe((confirmed: boolean) => {
      if (confirmed) {
        this.http.delete(`${this.rest.URLS.fieldTypes}${this.selectedClassification?.id}/`).subscribe(res => {
          const idx = this.classifications.indexOf(this.selectedClassification!);
          if (idx > -1) {
            this.classifications.splice(idx, 1);
          }
          this.selectedClassification = undefined;
          this.selectedClass = undefined;
        },(error) => {
          this.showErrorMessage(error);
        });
      }
    });
  }

  addClass(): void {
    if (!this.selectedClassification) return;
    let dialogRef = this.dialog.open(ConfirmDialogComponent, {
      panelClass: 'absolute',
      width: '300px',
      disableClose: true,
      data: {
        title: `Neue Klasse (${this.selectedClassification.name})`,
        template: this.nameTemplate,
        closeOnConfirm: false
      }
    });
    dialogRef.afterClosed().subscribe(() => {
      this.nameForm.reset();
    });
    dialogRef.componentInstance.confirmed.subscribe(() => {
      this.nameForm.markAllAsTouched();
      if (this.nameForm.invalid) return;
      let classes = Object.assign([],this.selectedClassification!.classification || []);
      const value = this.nameForm.value.name;
      classes.push({ value: value, order: classes.length + 1 })
      const attributes = { classification: classes };
      this.patchClassificaton(this.selectedClassification!.id, attributes).subscribe(fieldType => {
        Object.assign(this.selectedClassification!, fieldType);
        this.selectedClass = this.selectedClassification!.classification!.find(c => c.value == value);
        dialogRef.close();
      },(error) => {
        this.nameForm.setErrors(error.error);
      });
    });
  }

  removeClass(): void {
    if (!this.selectedClass || !this.selectedClassification)
      return;
    const dialogRef = this.dialog.open(RemoveDialogComponent, {
      width: '500px',
      data: {
        title: `Die Klasse wirklich entfernen?`,
        confirmButtonText: `Klasse entfernen`,
        message: 'Es werden eventuell vorhandene Einträge dieser Klasse auf leere Zeichenketten gesetzt.',
        value: this.selectedClass?.value
      }
    });
    dialogRef.afterClosed().subscribe((confirmed: boolean) => {
      if (confirmed) {
        const classes = Object.assign([], this.selectedClassification!.classification);
        const idx = classes.indexOf(this.selectedClass!);
        if (idx > -1) {
          classes.splice(idx, 1);
        }
        this.patchClassificaton(this.selectedClassification!.id, { classification: classes }).subscribe(fieldType => {
          Object.assign(this.selectedClassification!, fieldType);
          const classes = this.selectedClassification!.classification || [];
          this.selectedClass = (classes.length > 0)? classes[0]: undefined;
        },(error) => {
          this.showErrorMessage(error);
        });
      }
    });
  }

  patchClassificaton(id: number, attributes: any): Observable<FieldType> {
    return this.http.patch<FieldType>(`${this.rest.URLS.fieldTypes}${id}/`, attributes);
  }

  showErrorMessage(error: any): void {
    this.dialog.open(ConfirmDialogComponent, {
      panelClass: 'absolute',
      width: '300px',
      disableClose: true,
      data: {
        title: 'Fehler',
        hideConfirmButton: true,
        message: `<i>${error.error}</i>`,
        closeOnConfirm: true
      }
    });
  }

  moveClass(direction: string): void {
    if (!this.selectedClass || !this.selectedClassification) return;
    this.orderIsChanging$.next(true);
    const idx = this.selectedClassification.classification!.indexOf(this.selectedClass);
    if (direction === 'up'){
      if (idx <= 0) return;
      arrayMove(this.selectedClassification.classification!, idx, idx - 1);
    }
    else if (direction === 'down'){
      if (idx === -1 || idx === this.selectedClassification.classification!.length - 1) return;
      arrayMove(this.selectedClassification.classification!, idx, idx + 1);
    }
    else return;

    this.selectedClassification.classification!.forEach((fclass,i) => {
      fclass.order = i + 1;
    });
    this.patchClassificaton(this.selectedClassification.id, { classification: this.selectedClassification.classification })
      .subscribe(() => this.orderIsChanging$.next(false))
  }
}
