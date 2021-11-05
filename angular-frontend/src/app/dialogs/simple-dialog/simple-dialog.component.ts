import { Component, EventEmitter, Inject, Output, TemplateRef } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialog, MatDialogRef } from "@angular/material/dialog";

interface DialogData {
  title?: string,
  template: TemplateRef<any>,
  context?: any;
  subtitle?: string;
  infoText?: string;
  infoExpanded?: boolean;
  showOkButton?: boolean;
  showCloseButton?: boolean;
}

@Component({
  selector: 'app-simple-dialog',
  templateUrl: './simple-dialog.component.html',
  styleUrls: ['./simple-dialog.component.scss']
})
export class SimpleDialogComponent {
  @Output() confirmed = new EventEmitter<boolean>();

  constructor(public dialogRef: MatDialogRef<SimpleDialogComponent>,
              @Inject(MAT_DIALOG_DATA) public data: DialogData) {
    data.context = data.context || {};
  }
}
