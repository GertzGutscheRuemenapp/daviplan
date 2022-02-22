import { Component, ElementRef, Inject, Input, TemplateRef, ViewChild } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialog, MatDialogRef } from "@angular/material/dialog";
import { faArrowsAlt, faQuestion } from '@fortawesome/free-solid-svg-icons';

export interface DialogData {
  title: string;
  text: string;
  headerIcon: string;
  template: TemplateRef<any>;
  context: any;
  resizable: boolean;
  dragArea: 'header' | 'all';
  minWidth: string;
}

@Component({
  selector: 'app-help-dialog',
  templateUrl: './help-dialog.component.html',
  styleUrls: ['./help-dialog.component.scss']
})
export class FloatingDialog {
  faArrows = faArrowsAlt;
  constructor(public dialogRef: MatDialogRef<FloatingDialog>, @Inject(MAT_DIALOG_DATA) public data: DialogData) {
    data.context = data.context || {};
    data.dragArea = data.dragArea || 'all';
  }
}

@Component({
  selector: 'app-help-button',
  template: `
    <button #helpButton title="Hilfe" mat-icon-button color="primary" class="small"
            (click)="onClick($event)">
        <mat-icon>help_outline</mat-icon>
<!--      <fa-icon [icon]="faQuestion" style="font-size: 12px;"></fa-icon>-->
    </button>
    <div #content style="display: none;">
      <ng-content></ng-content>
    </div>
  `
})
export class HelpDialogComponent {
  @Input() title: string = '';
  @Input() text: string = '';
  @Input() width: number = 350;
  @Input() position: string = 'right';
  @Input() top: number = -50;
  @Input() template?: TemplateRef<any>;
  @Input() context?: any;
  @ViewChild('content') content!: ElementRef;
  @ViewChild('helpButton', { read: ElementRef }) helpButton!: ElementRef;
  faQuestion = faQuestion;
  dialogRef?: MatDialogRef<FloatingDialog>;

  constructor(public dialog: MatDialog) {}

  onClick(event: Event) {
    event.stopPropagation();
    if (this.dialogRef && this.dialogRef.getState() === 0) {
      this.dialogRef.close();
    }
    else {
      const rect: DOMRect = this.helpButton.nativeElement.getBoundingClientRect();
      const position = {
        left: (this.position === 'left') ? `${rect.left - this.width - 10}px`:
              (this.position === 'center') ? `${rect.left - this.width / 2 }px`:
              `${rect.left + 40}px`,
        top: `${rect.top + this.top}px`
      }
      this.dialogRef = this.dialog.open(FloatingDialog, {
        width: `${this.width}px`,
        panelClass: 'help-container',
        hasBackdrop: false,
        autoFocus: false,
        position: position,
        data: {
          title: this.title,
          text: this.content.nativeElement.innerHTML,
          context: this.context,
          template: this.template,
          headerIcon: 'help_outline'
        }
      });
    }
  }
}
