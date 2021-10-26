import { AfterViewInit, Component, OnDestroy, ViewChild } from '@angular/core';
import { CheckTreeComponent } from "../../../elements/check-tree/check-tree.component";
import { MapControl, MapService } from "../../../map/map.service";

@Component({
  selector: 'app-external-layers',
  templateUrl: './external-layers.component.html',
  styleUrls: ['./external-layers.component.scss']
})
export class ExternalLayersComponent implements AfterViewInit, OnDestroy {
  @ViewChild('layerTree') layerTree!: CheckTreeComponent;
  layerGroups = [
    {name: 'Ökologie', id: 11, children: [{id: 1, name: 'Naturschutzgebiete'}, {id: 2, name: 'Wälder'}, {id: 8, name: 'unzerschnittene Freiräume'}, {id: 8, name: 'Wasserschutzgebiete'}]},
    {name: 'Verkehr', id: 12, children: [{id: 3, name: 'ÖPNV'}, {id: 4, name: 'Lärmkarte'}, {id: 5, name: 'Fahrradwege'}]},
    {name: 'Infrastruktur', id: 13, children: [{id: 6, name: 'Hochspannungsmasten'}, {id: 7, name: 'ALKIS Gebäudedaten'}]}
  ]
  mapControl?: MapControl;

  selectedLayer: any = undefined;
  selectedGroup: any = undefined;

  constructor(private mapService: MapService) { }

  ngAfterViewInit(): void {
    this.layerTree.selected.subscribe(node => {
      this.selectedLayer = (node.expandable) ? undefined : this.getLayer(node.id);
      this.selectedGroup = (node.expandable) ? this.getGroup(node.id) : undefined;
      console.log(this.selectedLayer);
    })
    this.mapControl = this.mapService.get('base-layers-map');
  }

  getLayer(id: number | undefined): any {
    if (id === undefined) return;
    for (let group of this.layerGroups) {
      for (let layer of group.children){
        if (layer.id === id) {
          return layer;
        }
      }
    }
    return;
  }

  getGroup(id: number | undefined): any {
    if (id === undefined) return;
    for (let group of this.layerGroups) {
        if (group.id === id) {
          return group;
      }
    }
    return;
  }

  ngOnDestroy(): void {
    this.mapControl?.destroy();
  }

}
