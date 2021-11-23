import { Component, ElementRef, Inject, Input, OnInit, ViewChild } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialog, MatDialogConfig, MatDialogRef } from "@angular/material/dialog";
import { faArrowsAlt } from '@fortawesome/free-solid-svg-icons';

export interface DialogData {
  title: string;
  text: string;
}

@Component({
  selector: 'app-help-dialog',
  templateUrl: './help-dialog.component.html',
  styleUrls: ['./help-dialog.component.scss']
})
export class HelpDialog {
  faArrows = faArrowsAlt;
  constructor(public dialogRef: MatDialogRef<HelpDialog>, @Inject(MAT_DIALOG_DATA) public data: DialogData) {}
}

@Component({
  selector: 'app-help-button',
  template: `
    <button #helpButton mat-icon-button color="primary" class="small" (click)="onClick()">
        <mat-icon>help_outline</mat-icon>
    </button>
    <div #content style="display: none;">
      <ng-content></ng-content>
    </div>
  `
})
export class HelpDialogComponent implements OnInit {
  @Input() title: string = '';
  @Input() text: string = '';
  @Input() width: number = 350;
  @Input() position: string = 'right';
  @Input() top: number = -50;
  @ViewChild('content') content!: ElementRef;
  @ViewChild('helpButton', { read: ElementRef }) helpButton!: ElementRef;
  dialogRef?: MatDialogRef<HelpDialog>;

  constructor(public dialog: MatDialog) {}

  ngOnInit() {
  }

  onClick() {
    if (this.dialogRef && this.dialogRef.getState() === 0) {
      this.dialogRef.close();
    }
    else {
      this.dialog.closeAll();
      const rect: DOMRect = this.helpButton.nativeElement.getBoundingClientRect();
      const position = {
        left: (this.position === 'left') ? `${rect.left - this.width - 10}px`: `${rect.left + 40}px`,
        top: `${rect.top + this.top}px`
      }
      this.dialogRef = this.dialog.open(HelpDialog, {
        width: `${this.width}px`,
        panelClass: 'help-container',
        hasBackdrop: false,
        autoFocus: false,
        position: position,
        data: { title: this.title, text: this.content.nativeElement.innerHTML }
      });
    }
  }
}
