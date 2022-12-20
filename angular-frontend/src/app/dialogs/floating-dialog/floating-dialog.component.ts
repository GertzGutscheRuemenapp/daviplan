import { Component, Inject, OnInit, TemplateRef } from '@angular/core';
import { faArrowsAlt } from "@fortawesome/free-solid-svg-icons";
import { BehaviorSubject } from "rxjs";
import { MAT_DIALOG_DATA, MatDialogRef } from "@angular/material/dialog";

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
  templateUrl: './floating-dialog.component.html',
  styleUrls: ['./floating-dialog.component.scss']
})
export class FloatingDialogComponent {
  faArrows = faArrowsAlt;
  isLoading$ = new BehaviorSubject<boolean>(false);
  constructor(public dialogRef: MatDialogRef<FloatingDialogComponent>, @Inject(MAT_DIALOG_DATA) public data: DialogData) {
    data.context = data.context || {};
    data.dragArea = data.dragArea || 'all';
  }

  setLoading(loading: boolean) {
    this.isLoading$.next(loading);
  }
}
