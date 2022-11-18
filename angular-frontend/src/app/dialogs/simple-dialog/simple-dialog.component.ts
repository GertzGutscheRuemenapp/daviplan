import { Component, EventEmitter, Inject, Output, TemplateRef } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialog, MatDialogRef } from "@angular/material/dialog";
import { BehaviorSubject } from "rxjs";

interface DialogData {
  title?: string,
  message?: string,
  template: TemplateRef<any>,
  context?: any,
  subtitle?: string,
  infoText?: string,
  infoExpanded?: boolean,
  showConfirmButton?: boolean,
  showCloseButton?: boolean,
  showAnimatedDots?: boolean,
  centerContent?: boolean
}

@Component({
  selector: 'app-simple-dialog',
  templateUrl: './simple-dialog.component.html',
  styleUrls: ['./simple-dialog.component.scss']
})
export class SimpleDialogComponent {
  @Output() confirmed = new EventEmitter<boolean>();
  isLoading$ = new BehaviorSubject<boolean>(false);

  constructor(public dialogRef: MatDialogRef<SimpleDialogComponent>,
              @Inject(MAT_DIALOG_DATA) public data: DialogData) {
    data.context = data.context || {};
  }

  public static show(message: string, dialog: MatDialog,
                     options?: { loading?: boolean, showConfirmButton?: boolean, showCloseButton?: boolean,
                       disableClose?: boolean, width?: string, showAnimatedDots?: boolean, title?: string,
                       centerContent?: boolean, icon?: string }
  ): MatDialogRef<SimpleDialogComponent> {
    const dialogRef = dialog.open(SimpleDialogComponent, {
      autoFocus: true,
      panelClass: 'absolute',
      width: options?.width || '300px',
      disableClose: (options?.disableClose != undefined)? options?.disableClose: true,
      data: {
        title: options?.title,
        message: message,
        showConfirmButton: options?.showConfirmButton,
        showCloseButton: options?.showCloseButton,
        showAnimatedDots: options?.showAnimatedDots,
        centerContent: options?.centerContent
      }
    });
    if (options?.loading)
      dialogRef.componentInstance.isLoading$.next(true);
    return dialogRef;
  }
}
