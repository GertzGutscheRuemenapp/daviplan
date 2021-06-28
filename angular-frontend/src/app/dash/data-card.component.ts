// card.component.ts
import { Component, Input, Output, TemplateRef, EventEmitter } from '@angular/core';
import { ConfirmDialogComponent } from "../dialogs/confirm-dialog.component";
import { MatDialog, MatDialogRef } from "@angular/material/dialog";
import { Observable } from "rxjs";

/*export interface InputData {
  title: string;
  message: string;
  confirmButtonText: string;
  cancelButtonText: string;
  inputs: DataInput[];
}*/

@Component({
  selector: 'app-data-card',
  templateUrl: './data-card.component.html',
  styleUrls: ['./data-card.component.scss']
})

export class DataCardComponent {
  dialogRef?: MatDialogRef<ConfirmDialogComponent>;
  @Input() title: string = '';
  @Input() confirmButtonText: string = '';
  @Input() cancelButtonText: string = '';
  @Input() previewTemplate!: TemplateRef<any>;
  @Input() editTemplate!: TemplateRef<any>;
  @Output() dialogClosed = new EventEmitter<boolean>();

  constructor(public dialog: MatDialog) {

  }

  onEdit() {
    this.dialogRef = this.dialog.open(ConfirmDialogComponent, {
      width: '300px',
      data: {
        title: this.title,
        template: this.editTemplate,
        closeOnConfirm: false
      }
    });
    this.dialogRef.afterClosed().subscribe((ok: boolean) => {
      this.dialogClosed.emit(ok);
    });
  }
}
