// card.component.ts
import { Component, Input, Output, TemplateRef, EventEmitter } from '@angular/core';
import { ConfirmDialogComponent } from "../dialogs/confirm-dialog.component";
import { MatDialog, MatDialogRef } from "@angular/material/dialog";

@Component({
  selector: 'app-data-card',
  templateUrl: './data-card.component.html',
  styleUrls: [ './dash-card.component.scss', './data-card.component.scss']
})

export class DataCardComponent {
  dialogRef?: MatDialogRef<ConfirmDialogComponent>;
  @Input() title: string = '';
  @Input() confirmButtonText: string = '';
  @Input() width: string = '500px';
  @Input() cancelButtonText: string = '';
  @Input() previewTemplate!: TemplateRef<any>;
  @Input() editTemplate!: TemplateRef<any>;
  @Output() dialogClosed = new EventEmitter<boolean>();
  @Output() dialogConfirmed = new EventEmitter<boolean>();

  constructor(public dialog: MatDialog) {

  }

  onEdit() {
    this.dialogRef = this.dialog.open(ConfirmDialogComponent, {
      panelClass: 'absolute',
      width: this.width,
      disableClose: true,
      data: {
        title: this.title,
        template: this.editTemplate,
        closeOnConfirm: false
      }
    });
    this.dialogRef.afterClosed().subscribe((ok: boolean) => {
      this.dialogClosed.emit(ok);
    });
    this.dialogRef.componentInstance.confirmed.subscribe(() => {
      this.dialogConfirmed.emit();
    });

  }

  closeDialog() {
    if (this.dialogRef)
      this.dialogRef.close();
  }

  setLoading(enable: boolean){
    if (this.dialogRef)
      this.dialogRef.componentInstance.isLoading = enable;
  }
}
