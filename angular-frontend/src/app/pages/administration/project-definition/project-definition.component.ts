import { AfterViewInit, Component, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { MapControl, MapService } from "../../../map/map.service";
import { InputCardComponent } from "../../../dash/input-card.component";
import { Geometry, GeometryCollection, MultiPolygon } from "ol/geom";
import { Feature } from "ol";
import union from '@turf/union';
import * as turf from '@turf/helpers';
import { GeoJSON } from "ol/format";

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
    const _this = this;
    this.areaCard.dialogOpened.subscribe(x => {
      this.areaCard.setLoading(true);
      this.areaSelectMapControl = this.mapService.get('project-area-select-map');
      this.areaSelectMapControl.setBackground(this.areaSelectMapControl.getBackgroundLayers()[0].id)

      let projectLayer = this.areaSelectMapControl.map?.addVectorLayer('project-area', {
        stroke: { color: 'red', width: 5 },
        visible: true
      });
      let format = new GeoJSON();
      let projectArea = new Feature({ });
      projectLayer?.getSource().addFeature(projectArea);
      this.areaSelectMapControl.map?.selected.subscribe(features => {
        let mergedGeom: turf.Feature<turf.MultiPolygon | turf.Polygon> | null = null;
        features.forEach(f => {
          // const json = format.writeGeometryObject(f.getGeometry());
          const poly = turf.multiPolygon(f.getGeometry().getCoordinates());
          mergedGeom = mergedGeom? union(poly, mergedGeom): poly;
        })
        // @ts-ignore
        let coords = mergedGeom? mergedGeom.geometry : [];
        const projectGeom = format.readFeature(coords).getGeometry();
        projectArea.setGeometry(projectGeom);
      })

      let selectLayer = this.areaSelectMapControl.map?.addVectorLayer(
        'bkg-gemeinden', {
          url: function (extent: any) {
            return (
              'https://sgx.geodatenzentrum.de/wfs_vg250?service=WFS&' +
              'version=1.1.0&request=GetFeature&typename=vg250_gem&' +
              'outputFormat=application/json&srsname=EPSG:3857&' +
              'bbox=' +
              extent.join(',') +
              ',EPSG:3857'
            )},
          visible: true,
          selectable: true,
          opacity: 0.5,
          tooltipField: 'gen',
          stroke: { color: 'black', selectedColor: 'black' },
          fill: { color: 'rgba(255, 255, 255, 0.5)', selectedColor: 'yellow' }
      });
      selectLayer?.getSource().addEventListener('featuresloadend', function(){
        _this.areaCard.setLoading(false);
      });
      // layer.
    })
    this.areaCard.dialogClosed.subscribe(x => {
      this.areaSelectMapControl?.destroy();
    })
    this.areaCard.dialogConfirmed.subscribe(ok => {
      this.areaCard.closeDialog()
    })
  }

  ngOnDestroy(): void {
    this.previewMapControl?.destroy();
  }

}
