// card.component.ts
import {
  Component,
  Input,
  Output,
  TemplateRef,
  EventEmitter,
  AfterViewInit,
  ViewChild
} from '@angular/core';
import { ConfirmDialogComponent } from "../dialogs/confirm-dialog/confirm-dialog.component";
import { MatDialog, MatDialogRef } from "@angular/material/dialog";
import { MatButton } from "@angular/material/button";

@Component({
  selector: 'app-input-card',
  templateUrl: './input-card.component.html',
  styleUrls: [ './input-card.component.scss']
})

export class InputCardComponent implements AfterViewInit {
  dialogRef?: MatDialogRef<ConfirmDialogComponent>;
  @ViewChild('editButton') prebuildEditButton?: MatButton;
  @Input() editButton?: HTMLElement | MatButton;
  @Input() title: string = '';
  @Input() subtitle: string = '';
  @Input() dialogTitle: string = '';
  @Input() infoText: string = '';
  @Input() dialogInfoText: string = '';
  @Input() showDialogCloseButton: boolean = false;
  @Input() confirmButtonText: string = '';
  @Input() width: string = '';
  @Input() dialogWidth: string = '500px';
  @Input() cancelButtonText: string = '';
  @Input() previewTemplate!: TemplateRef<any>;
  @Input() editTemplate!: TemplateRef<any>;
  @Input() borderless: boolean = false;
  @Input() topRightHelp: boolean = false;
  @Input() infoExpanded: boolean = false;
  @Input() disabled: boolean = false;
  @Output() dialogOpened = new EventEmitter<any>();
  @Output() dialogClosed = new EventEmitter<boolean>();
  @Output() dialogConfirmed = new EventEmitter<boolean>();

  constructor(public dialog: MatDialog) {  }

  ngAfterViewInit(): void {
    let _this = this;
    if (this.editTemplate){
      let button = (!this.editButton) ? this.prebuildEditButton : this.editButton;
      let natButton = (button instanceof MatButton) ? button._getHostElement() : button;
      natButton.addEventListener('click', function(){
        _this.onEdit();
      });
    }
  }

  onEdit() {
    this.dialogRef = this.dialog.open(ConfirmDialogComponent, {
      panelClass: 'absolute',
      width: this.dialogWidth,
      disableClose: true,
      autoFocus: false,
      data: {
        title: this.dialogTitle || this.title || this.subtitle,
        template: this.editTemplate,
        closeOnConfirm: false,
        infoText: this.dialogInfoText,
        showCloseButton: this.showDialogCloseButton,
        confirmButtonText: $localize`Speichern`
      }
    });
    this.dialogRef.afterOpened().subscribe(x => {
      this.dialogOpened.emit();
    })
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
      this.dialogRef.componentInstance.isLoading$.next(enable);
  }
}
