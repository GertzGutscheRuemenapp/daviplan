import { Component, Inject, TemplateRef } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { Observable } from "rxjs";

export interface DialogData {
  title: string,
  message: string,
  confirmButtonText: string,
  cancelButtonText: string,
  template: TemplateRef<any>,
  closeOnConfirm: boolean,
  // postEdit: Observable<any>;
}

@Component({
  selector: 'confirm-dialog',
  templateUrl: './confirm-dialog.component.html',
  styleUrls: ['./confirm-dialog.component.scss']
})

export class ConfirmDialogComponent {

  constructor(
    public dialogRef: MatDialogRef<ConfirmDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: DialogData) {
    data.confirmButtonText = data.confirmButtonText || $localize`Bestätigen`;
    data.cancelButtonText = data.cancelButtonText || $localize`Abbrechen`;
  }

  onConfirmClick() {
/*    if (this.data.postEdit) {
      this.data.postEdit.subscribe(() => this.dialogRef.close(true),(error) => {
        console.log('there was an error sending the query', error);
      });

    }*/
    if (this.data.closeOnConfirm)
      this.dialogRef.close(true);
  }
}
