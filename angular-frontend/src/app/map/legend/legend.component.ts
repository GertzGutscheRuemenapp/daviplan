import { AfterViewInit, ChangeDetectorRef, Component, Input, TemplateRef, ViewChild } from '@angular/core';
import { MapControl, MapLayerGroup, MapService } from "../map.service";
import { FloatingDialog } from "../../dialogs/help-dialog/help-dialog.component";
import { MatDialog, MatDialogRef } from "@angular/material/dialog";
import { MapLayer, VectorLayer } from '../layers';

@Component({
  selector: 'app-legend',
  templateUrl: './legend.component.html',
  styleUrls: ['./legend.component.scss']
})
export class LegendComponent implements AfterViewInit {
  @Input() target!: string;
  @Input() showInternal: boolean = true;
  @Input() showExternal: boolean = true;
  @ViewChild('legendImage') legendImageTemplate?: TemplateRef<any>;
  legendImageDialogs: Record<number | string, MatDialogRef<any>> = {};
  mapControl?: MapControl;

  constructor(public dialog: MatDialog, private mapService: MapService, private cdRef: ChangeDetectorRef) {
  }

  ngAfterViewInit (): void {
    this.mapControl = this.mapService.get(this.target);
    this.cdRef.detectChanges();
    this.mapControl.zoomToProject();
  }

  /**
   * handle changed check state of layer
   *
   * @param layer
   */
  toggleLayer(layer: MapLayer): void {
    layer.setVisible(!layer.visible);
  }

  // ToDo: use template filter
  nVisible(group: MapLayerGroup): number {
    return group.children.filter(l => l.visible).length;
  }

  /**
   * open a dialog with the legend image of given layer
   *
   * @param layer
   */
  toggleLegendImage(layer: MapLayer): void {
    if (layer.id === undefined) return;
    let dialogRef = this.legendImageDialogs[layer.id];
    if (dialogRef && dialogRef.getState() === 0)
      dialogRef.close();
    else
      this.legendImageDialogs[layer.id] = this.dialog.open(FloatingDialog, {
        panelClass: 'help-container',
        hasBackdrop: false,
        autoFocus: false,
        data: {
          title: layer.name,
          context: { layer: layer },
          template: this.legendImageTemplate
        }
      });
  }

  toggleLabel(layer: VectorLayer): void {
    layer.setShowLabel(!layer.showLabel);
  }

  toggleLayerLegend(layer: VectorLayer): void {
    if (!layer.legend) return;
    layer.legend.elapsed = !layer.legend.elapsed;
  }

  setBGOpacity(value: number | null) {
    if (value === null) return;
    this.mapControl?.background?.setOpacity(value);
  }

}
