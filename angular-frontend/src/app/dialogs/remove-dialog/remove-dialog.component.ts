import { Component, EventEmitter, Inject, Input, OnInit, Output, TemplateRef } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from "@angular/material/dialog";
import { ConfirmDialogComponent } from "../confirm-dialog/confirm-dialog.component";

interface DialogData {
  title: string,
  value: any,
  confirmButtonText: string,
  cancelButtonText: string,
  closeOnConfirm: boolean,
  message: string
}

@Component({
  selector: 'app-remove-dialog',
  templateUrl: './remove-dialog.component.html',
  styleUrls: ['./remove-dialog.component.scss']
})
export class RemoveDialogComponent implements OnInit {

  constructor(public dialogRef: MatDialogRef<ConfirmDialogComponent>,
              @Inject(MAT_DIALOG_DATA) public data: DialogData) {
    data.title = data.title || $localize`Objekt entfernen`;
    data.confirmButtonText = data.confirmButtonText || $localize`Entfernen`;
    data.cancelButtonText = $localize`Abbrechen`;
    data.closeOnConfirm = (data.closeOnConfirm != null) ? data.closeOnConfirm : true;
    this.dialogRef.addPanelClass('warning');
  }

  onConfirmClick() {
    document.body.focus();
    this.dialogRef.close(true);
  }

  ngOnInit(): void {
  }
}
