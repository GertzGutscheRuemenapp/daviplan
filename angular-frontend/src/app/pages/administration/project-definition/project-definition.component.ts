import { AfterViewInit, Component, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { MapControl, MapService } from "../../../map/map.service";
import { InputCardComponent } from "../../../dash/input-card.component";

@Component({
  selector: 'app-project-definition',
  templateUrl: './project-definition.component.html',
  styleUrls: ['./project-definition.component.scss']
})
export class ProjectDefinitionComponent implements AfterViewInit, OnDestroy {
  previewMapControl?: MapControl;
  areaSelectMapControl?: MapControl;
  @ViewChild('areaCard') areaCard!: InputCardComponent;

  constructor(private mapService: MapService) { }

  ngAfterViewInit(): void {
    this.previewMapControl = this.mapService.get('project-preview-map');
    this.previewMapControl.setBackground(this.previewMapControl.getBackgroundLayers()[0].id)
    this.setupAreaCard();
  }

  setupAreaCard(): void {
    this.areaCard.dialogOpened.subscribe(x => {
      this.areaSelectMapControl = this.mapService.get('project-area-select-map');
      this.areaSelectMapControl.setBackground(this.areaSelectMapControl.getBackgroundLayers()[0].id)
      this.areaSelectMapControl.map?.addWFS({
        name: 'bkg-gemeinden',
        url: function (extent: any) {
          return (
            'https://sgx.geodatenzentrum.de/wfs_vg250?service=WFS&' +
            'version=1.1.0&request=GetFeature&typename=vg250_gem&' +
            'outputFormat=application/json&srsname=EPSG:3857&' +
            'bbox=' +
            extent.join(',') +
            ',EPSG:3857'
          );
        },
        visible: true,
        selectable: true,
        tooltipField: 'gen'
      });
    })
    this.areaCard.dialogClosed.subscribe(x => {
      this.areaSelectMapControl?.destroy();
    })
  }

  ngOnDestroy(): void {
    this.previewMapControl?.destroy();
  }

}
