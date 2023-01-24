import { AfterViewInit, Component, ElementRef, Input, OnInit, TemplateRef, ViewChild } from '@angular/core';
import { EcoFabSpeedDialComponent } from "@ecodev/fab-speed-dial";
import { MapControl, MapService } from "../map.service";
import { FormBuilder, FormControl, FormGroup } from "@angular/forms";
import { ConfirmDialogComponent } from "../../dialogs/confirm-dialog/confirm-dialog.component";
import { MatDialog, MatDialogRef } from "@angular/material/dialog";
import { FloatingDialogComponent } from "../../dialogs/floating-dialog/floating-dialog.component";
import { showMessage } from "../../helpers/utils";

@Component({
  selector: 'app-map-controls',
  templateUrl: './map-controls.component.html',
  styleUrls: ['./map-controls.component.scss']
})
export class MapControlsComponent implements AfterViewInit {
  @Input() target!: string;
  @Input() showOnHover?: boolean = false;
  @Input() bookmarks?: boolean = false;
  @ViewChild('leftDial') leftDial?: EcoFabSpeedDialComponent;
  @ViewChild('rightDial') rightDial?: EcoFabSpeedDialComponent;
  @ViewChild('leftDialBack') leftDialBack?: HTMLElement;
  @ViewChild('extentDialogTemplate') extentDialogTemplate?: TemplateRef<any>;
  @ViewChild('addExtentTemplate') addExtentTemplate?: TemplateRef<any>;
  @ViewChild('extentButton', { read: ElementRef }) extentButton?: ElementRef;
  addExtentForm: FormGroup;
  mapControl!: MapControl;
  expanded: boolean = false;
  extentDialogRef?: MatDialogRef<FloatingDialogComponent>;

  constructor(private mapService: MapService, private formBuilder: FormBuilder, private dialog: MatDialog) {
    this.addExtentForm = this.formBuilder.group({
      name: new FormControl('')
    })
  }

  ngAfterViewInit (): void {
    this.mapControl = this.mapService.get(this.target);
  }

  action(a: string): void {}

  zoomIn(): void {
    this.mapControl?.map?.zoom(1);
  }

  zoomOut(): void {
    this.mapControl?.map?.zoom(-1);
  }

  toggleFullscreen(): void {
    this.mapControl?.map?.toggleFullscreen();
  }

  exportPNG(): void {
    this.mapControl?.exportMapAsPNG();
  }

  exportLegend(): void {
    // showMessage('Noch nicht implementiert', this.dialog);
    this.mapControl?.exportLegend();
  }

  copyTitle(): void {
    this.mapControl?.exportTitleToClipboard();
  }

  print(): void {
    this.mapControl?.map?.print();
  }

  toggle(): void {
    this.leftDial?.toggle();
    this.rightDial?.toggle();
    this.expanded = !this.expanded;
  }

  saveExtent(name: string): void {
    this.mapControl.saveCurrentExtent(name);
  }

  loadExtent(name: string): void {
    this.mapControl.loadExtent(name);
  }

  openExtentDialog(): void {
    const rect: DOMRect = this.extentButton?.nativeElement.getBoundingClientRect();
    if (this.extentDialogRef && this.extentDialogRef.getState() === 0) {
      return;
    }
    const position = rect? {
      left: `${rect.left - 410}px`,
      top: `${rect.top + 20}px`
    }: undefined;
    this.extentDialogRef = this.dialog.open(FloatingDialogComponent, {
      panelClass: 'floating-container',
      hasBackdrop: false,
      autoFocus: false,
      position: position,
      data: {
        title: 'Kartenausschnitte',
        template: this.extentDialogTemplate,
        minWidth: '400px'
      }
    });
  }

  addExtent(): void {
    let dialogRef = this.dialog.open(ConfirmDialogComponent, {
      panelClass: 'absolute',
      width: '400px',
      disableClose: true,
      data: {
        title: 'Als neuen Kartenausschnitt speichern',
        template: this.addExtentTemplate,
        closeOnConfirm: false
      }
    });
    dialogRef.afterOpened().subscribe(sth => {
      this.addExtentForm.reset();
    });
    dialogRef.componentInstance.confirmed.subscribe(() => {
      this.addExtentForm.markAllAsTouched();
      if (this.addExtentForm.invalid) return;
      this.mapControl.saveCurrentExtent(this.addExtentForm.value.name);
      dialogRef.close();
    });
  }

  removeExtent(name: string): void {
    this.mapControl.removeExtent(name);
  }

}
