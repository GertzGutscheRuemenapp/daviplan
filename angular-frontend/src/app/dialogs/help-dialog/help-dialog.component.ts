import { Component, ElementRef, Input, TemplateRef, ViewChild } from '@angular/core';
import { MatDialog, MatDialogRef } from "@angular/material/dialog";
import { faQuestion } from '@fortawesome/free-solid-svg-icons';
import { FloatingDialogComponent } from "../floating-dialog/floating-dialog.component";

@Component({
  templateUrl: './help-dialog.component.html',
  selector: 'app-help-button',
})
export class HelpDialogComponent {
  @Input() title: string = '';
  @Input() text: string = '';
  @Input() width: number = 350;
  @Input() position: 'right' | 'left' | 'center' = 'right';
  @Input() top: number = -50;
  @Input() template?: TemplateRef<any>;
  @Input() context?: any;
  @ViewChild('content') content!: ElementRef;
  @ViewChild('helpButton', { read: ElementRef }) helpButton!: ElementRef;
  faQuestion = faQuestion;
  dialogRef?: MatDialogRef<FloatingDialogComponent>;

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
      this.dialogRef = this.dialog.open(FloatingDialogComponent, {
        width: `${this.width}px`,
        panelClass: 'floating-container',
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
