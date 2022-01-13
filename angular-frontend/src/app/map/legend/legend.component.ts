import { AfterViewInit, ChangeDetectorRef, Component, Input, OnInit, TemplateRef, ViewChild } from '@angular/core';
import { MapControl, MapService } from "../map.service";
import { LayerGroup, Layer } from "../../pages/basedata/external-layers/external-layers.component";
import { CookieService } from "../../helpers/cookies.service";
import { FloatingDialog } from "../../dialogs/help-dialog/help-dialog.component";
import { MatDialog } from "@angular/material/dialog";

@Component({
  selector: 'app-legend',
  templateUrl: './legend.component.html',
  styleUrls: ['./legend.component.scss']
})
export class LegendComponent implements AfterViewInit {
  @Input() target!: string;
  @ViewChild('legendImage') legendImageTemplate?: TemplateRef<any>;
  layers: any;
  mapControl!: MapControl;
  activeBackgroundId: number = -1000;
  activeBackground?: Layer;
  backgroundOpacity = 1;
  backgroundLayers: Layer[] = [];
  layerGroups: LayerGroup[] = [];
  activeGroups: LayerGroup[] = [];
  editMode: boolean = true;
  Object = Object;

  constructor(public dialog: MatDialog, private mapService: MapService,
              private cdRef:ChangeDetectorRef, private cookies: CookieService) {
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
      this.layerGroups = groups;
      groups.forEach(group => group.children!.forEach(layer => {
        layer.checked = <boolean>(this.cookies.get(`legend-layer-checked-${layer.id}`) || false);
        if (layer.checked) this.mapControl.toggleLayer(layer.id, true);
      }))
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
    if(value === null) return;
    this.mapControl?.setLayerAttr(layer.id, { opacity: value });
  }

  setBackground(id: number) {
    this.activeBackground = this.backgroundLayers.find(l => { return l.id === id });
    this.cookies.set(`background-layer`, id);
    this.mapControl.setBackground(id);
  }

  showLegendImage(layer: Layer): void {
    this.dialog.open(FloatingDialog, {
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
}
