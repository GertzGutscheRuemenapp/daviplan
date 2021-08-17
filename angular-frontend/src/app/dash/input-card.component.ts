// card.component.ts
import { Component, Input, Output, TemplateRef, EventEmitter, AfterViewInit, ElementRef } from '@angular/core';
import { ConfirmDialogComponent } from "../dialogs/confirm-dialog.component";
import { MatDialog, MatDialogRef } from "@angular/material/dialog";
import { MatButton } from "@angular/material/button";

@Component({
  selector: 'app-input-card',
  templateUrl: './input-card.component.html',
  styleUrls: [ './input-card.component.scss']
})

export class InputCardComponent implements AfterViewInit {
  dialogRef?: MatDialogRef<ConfirmDialogComponent>;
  @Input() editButton?: HTMLElement;
  @Input() title: string = '';
  @Input() subtitle: string = '';
  @Input() dialogTitle: string = '';
  @Input() infoText: string = '';
  @Input() confirmButtonText: string = '';
  @Input() dialogWidth: string = '500px';
  @Input() cancelButtonText: string = '';
  @Input() previewTemplate!: TemplateRef<any>;
  @Input() editTemplate!: TemplateRef<any>;
  @Output() dialogClosed = new EventEmitter<boolean>();
  @Output() dialogConfirmed = new EventEmitter<boolean>();

  constructor(public dialog: MatDialog) {  }

  ngAfterViewInit(): void {
    let _this = this;
    if (this.editButton)
      this.editButton.addEventListener('click', function(){
        _this.onEdit();
      });
  }

  onEdit() {
    this.dialogRef = this.dialog.open(ConfirmDialogComponent, {
      panelClass: 'absolute',
      width: this.dialogWidth,
      disableClose: false,
      autoFocus: false,
      data: {
        title: this.dialogTitle || this.title,
        template: this.editTemplate,
        closeOnConfirm: false
      }
    });
    this.dialogRef.afterClosed().subscribe((ok: boolean) => {
      this.dialogClosed.emit(!!ok);
    });
    this.dialogRef.componentInstance.confirmed.subscribe(() => {
      this.dialogConfirmed.emit();
    });

  }

  closeDialog(confirmed: boolean = false) {
    if (this.dialogRef)
      this.dialogRef.close(confirmed);
  }

  setLoading(enable: boolean){
    if (this.dialogRef)
      this.dialogRef.componentInstance.isLoading = enable;
  }
}
