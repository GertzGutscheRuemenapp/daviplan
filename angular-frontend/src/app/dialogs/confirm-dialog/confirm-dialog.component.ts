import {Component, EventEmitter, Inject, Output, TemplateRef} from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';

export interface DialogData {
  title: string,
  message: string,
  confirmButtonText: string,
  cancelButtonText: string,
  template: TemplateRef<any>,
  closeOnConfirm: boolean,
  context: any;
}

@Component({
  selector: 'confirm-dialog',
  templateUrl: './confirm-dialog.component.html',
  styleUrls: ['./confirm-dialog.component.scss']
})

export class ConfirmDialogComponent {
  public isLoading: boolean = false;
  @Output() confirmed = new EventEmitter<boolean>();

  constructor(
    public dialogRef: MatDialogRef<ConfirmDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: DialogData) {
    data.confirmButtonText = data.confirmButtonText || $localize`Bestätigen`;
    data.cancelButtonText = data.cancelButtonText || $localize`Abbrechen`;
    data.context = data.context || {};
  }

  onConfirmClick() {
    // remove focus from inputs
    document.body.focus()
    // this.dialogRef._containerInstance._elementRef.nativeElement.focus()
    if (this.data.closeOnConfirm)
      this.dialogRef.close(true);
    this.confirmed.emit();
  }
}
