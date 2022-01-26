import { AfterViewInit, Component, Input, TemplateRef, ViewChild } from '@angular/core';
import { MapControl, MapService } from "../map.service";
import { LayerGroup, Layer } from "../../rest-interfaces";
import { FloatingDialog } from "../../dialogs/help-dialog/help-dialog.component";
import { MatDialog, MatDialogRef } from "@angular/material/dialog";
import { SettingsService } from "../../settings.service";

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
  legendImageDialogs: Record<number, MatDialogRef<any>> = [];
  mapControl!: MapControl;
  mapSettings: any = {};
  // -10000 = no background
  activeBackgroundId: number = -100000;
  activeBackground?: Layer;
  backgroundOpacity: number = 1;
  backgroundLayers: Layer[] = [];
  layerGroups: LayerGroup[] = [];
  activeGroups: LayerGroup[] = [];
  editMode: boolean = true;
  Object = Object;

  constructor(public dialog: MatDialog, private mapService: MapService, private settings: SettingsService) {
    // call destroy on page reload
    window.onbeforeunload = () => this.ngOnDestroy();
  }

  ngAfterViewInit (): void {
    this.mapControl = this.mapService.get(this.target);
    this.mapControl.zoomToProject();
    this.backgroundLayers = this.mapControl.getBackgroundLayers();
    this.settings.user.get(this.target).subscribe(settings => {
      settings = settings || {};
      this.mapSettings = settings;
      this.editMode = settings['legend-edit-mode'] || true;
      this.backgroundOpacity = parseFloat(settings[`background-layer-opacity`]) || 1;
      const backgroundId = parseInt(settings[`background-layer`]) || this.backgroundLayers[0].id;
      this.activeBackgroundId = backgroundId;
      this.initLayers();
    })
  }

  initLayers(): void {
    this.setBackground(this.activeBackgroundId);
    this.mapService.getLayers().subscribe(groups => {
      let layerGroups: LayerGroup[] = [];
      groups.forEach(group => {
        if (!group.children || (!this.showExternal && group.external) || (!this.showInternal && !group.external))
          return;
        group.children!.forEach(layer => {
          layer.checked = Boolean(this.mapSettings[`layer-checked-${layer.id}`]);
          layer.opacity = parseFloat(this.mapSettings[`layer-opacity-${layer.id}`]) || 1;
          this.mapControl.setLayerAttr(layer.id, { opacity: layer.opacity });
          if (layer.checked) this.mapControl.toggleLayer(layer.id, true);
        });
        layerGroups.push(group);
      });
      this.layerGroups = layerGroups;
      this.filterActiveGroups();
    })
  }

  /**
   * handle changed check state of layer
   *
   * @param layer
   */
  onLayerToggle(layer: Layer): void {
    layer.checked = !layer.checked;
    this.mapSettings[`layer-checked-${layer.id}`] = layer.checked;
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
      this.mapSettings['layer-opacity'] = value;
    else
      this.mapSettings[`layer-opacity-${layer.id}`] = value;
    this.mapControl?.setLayerAttr(layer.id, { opacity: value });
  }

  saveSettings(): void {
    if (this.mapSettings)
      this.settings.user.set(this.target, this.mapSettings);
  }

  /**
   * set layer with given id as background layer (only one at a time)
   *
   * @param id
   */
  setBackground(id: number) {
    this.mapControl.setBackground(id);
    this.activeBackground = this.backgroundLayers.find(l => { return l.id === id });
    this.mapSettings[`background-layer`] = id;
    if (this.activeBackground){
      this.mapControl.setLayerAttr(this.activeBackground.id, { opacity: this.backgroundOpacity });
    }
  }

  /**
   * open a dialog with the legend image of given layer
   *
   * @param layer
   */
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
    this.mapSettings['legend-edit-mode'] = this.editMode;
  }

  ngOnDestroy(): void {
    this.saveSettings();
  }
}
