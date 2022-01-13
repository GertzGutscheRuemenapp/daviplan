import { AfterViewInit, ChangeDetectorRef, Component, Input, OnInit, TemplateRef, ViewChild } from '@angular/core';
import { MapControl, MapService } from "../map.service";
import { LayerGroup, Layer } from "../../pages/basedata/external-layers/external-layers.component";
import { CookieService } from "../../helpers/cookies.service";
import { FloatingDialog } from "../../dialogs/help-dialog/help-dialog.component";
import { MatDialog, MatDialogRef } from "@angular/material/dialog";

@Component({
  selector: 'app-legend',
  templateUrl: './legend.component.html',
  styleUrls: ['./legend.component.scss']
})
export class LegendComponent implements AfterViewInit {
  @Input() target!: string;
  @Input() showInternal?: boolean = false;
  @ViewChild('legendImage') legendImageTemplate?: TemplateRef<any>;
  legendImageDialogs: Record<number, MatDialogRef<any>> = [];
  mapControl!: MapControl;
  activeBackgroundId: number = -1000;
  activeBackground?: Layer;
  backgroundOpacity: number;
  backgroundLayers: Layer[] = [];
  layerGroups: LayerGroup[] = [];
  activeGroups: LayerGroup[] = [];
  editMode: boolean;
  Object = Object;

  constructor(public dialog: MatDialog, private mapService: MapService,
              private cdRef:ChangeDetectorRef, private cookies: CookieService) {
    this.backgroundOpacity = parseFloat(<string>this.cookies.get(`background-layer-opacity`) || '1');
    this.editMode = <boolean>this.cookies.get('legend-edit-mode') || false;
  }

  ngAfterViewInit (): void {
    this.mapControl = this.mapService.get(this.target);
    this.initSelect();
  }

  initSelect(): void {
    this.backgroundLayers = this.mapControl.getBackgroundLayers();
    const backgroundId = parseInt(<string>this.cookies.get(`background-layer`) || this.backgroundLayers[0].id.toString());
    this.activeBackgroundId = backgroundId;
    this.setBackground(backgroundId);

    this.mapService.getLayers().subscribe(groups => {
      let layerGroups: LayerGroup[] = [];
      groups.forEach(group => {
        if (!group.children || !(group.external || this.showInternal))
          return;
        group.children!.forEach(layer => {
          layer.checked = <boolean>(this.cookies.get(`legend-layer-checked-${layer.id}`) || false);
          layer.opacity = parseFloat(<string>this.cookies.get(`legend-layer-opacity-${layer.id}`) || '1');
          this.mapControl.setLayerAttr(layer.id, { opacity: layer.opacity });
          if (layer.checked) this.mapControl.toggleLayer(layer.id, true);
        });
        layerGroups.push(group);
      });
      this.layerGroups = layerGroups;
      this.filterActiveGroups();
    })
    this.cdRef.detectChanges();
  }

  onLayerToggle(layer: Layer): void {
    layer.checked = !layer.checked;
    this.cookies.set(`legend-layer-checked-${layer.id}`, layer.checked);
    this.mapControl.toggleLayer(layer.id, layer.checked);
    this.filterActiveGroups();
  }

  // ToDo: use template filter
  filterActiveGroups(): void {
    this.activeGroups = this.layerGroups.filter(g => g.children!.filter(l => l.checked).length > 0);
  }

  opacityChanged(layer: Layer, value: number | null): void {
    if(value === null || !layer) return;
    if (layer === this.activeBackground)
      this.cookies.set('background-layer-opacity', value);
    else
      this.cookies.set(`legend-layer-opacity-${layer.id}`, value);
    this.mapControl?.setLayerAttr(layer.id, { opacity: value });
  }

  setBackground(id: number) {
    this.activeBackground = this.backgroundLayers.find(l => { return l.id === id });
    this.cookies.set(`background-layer`, id);
    if (this.activeBackground){
      this.mapControl.setBackground(id);
      this.mapControl.setLayerAttr(this.activeBackground.id, { opacity: this.backgroundOpacity });
    }
  }

  toggleLegendImage(layer: Layer): void {
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

  toggleEditMode(): void {
    this.editMode = !this.editMode;
    this.cookies.set('legend-edit-mode', this.editMode)
  }
}
