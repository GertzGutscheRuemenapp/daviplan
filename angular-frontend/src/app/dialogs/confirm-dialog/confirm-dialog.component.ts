import { AfterViewInit, Component, EventEmitter, Inject, Input, Output, TemplateRef } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';

interface DialogData {
  title: string,
  message: string,
  confirmButtonText: string,
  cancelButtonText: string,
  hideConfirmButton: boolean,
  template: TemplateRef<any>,
  closeOnConfirm: boolean,
  context: any;
  subtitle?: string;
  infoText?: string;
  infoExpanded?: boolean;
}

@Component({
  selector: 'confirm-dialog',
  templateUrl: './confirm-dialog.component.html',
  styleUrls: ['./confirm-dialog.component.scss']
})

export class ConfirmDialogComponent implements AfterViewInit  {
  public isLoading: boolean = false;
  @Output() confirmed = new EventEmitter<boolean>();
  initReady = false;

  constructor(public dialogRef: MatDialogRef<ConfirmDialogComponent>,
              @Inject(MAT_DIALOG_DATA) public data: DialogData) {
    data.confirmButtonText = data.confirmButtonText || $localize`Bestätigen`;
    data.cancelButtonText = data.cancelButtonText || (data.hideConfirmButton)? 'OK': $localize`Abbrechen`;
    data.context = data.context || {};
  }

  onConfirmClick() {
    // remove focus from inputs
    document.body.focus()
    // this.dialogRef._containerInstance._elementRef.nativeElement.focus()
    if (this.data.closeOnConfirm)
      this.dialogRef.close(true);
    this.confirmed.emit(true);
  }

  ngAfterViewInit() {
    // workaround for disabling closing-animation of help panel in dialog
    setTimeout(() => this.initReady = true);
  }
}
