import { AfterViewInit, Component, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { MapControl, MapService } from "../../../map/map.service";
import { InputCardComponent } from "../../../dash/input-card.component";
import { Geometry, GeometryCollection, MultiPolygon, Polygon } from "ol/geom";
import { Feature } from 'ol';
import { register } from 'ol/proj/proj4'
import union from '@turf/union';
import pointOnSurface from '@turf/point-on-surface';
import booleanWithin from "@turf/boolean-within";
import * as turf from '@turf/helpers';
import { GeoJSON, WKT } from "ol/format";
import { Profile, User } from "../../login/users";
import proj4 from 'proj4';
import { HttpClient } from "@angular/common/http";
import { RestAPI } from "../../../rest-api";

export interface ProjectSettings {
  projectArea: string,
  startYear: number,
  endYear: number
}

proj4.defs("EPSG:25832", "+proj=utm +zone=32 +ellps=GRS80 +units=m +no_defs");
register(proj4);

@Component({
  selector: 'app-project-definition',
  templateUrl: './project-definition.component.html',
  styleUrls: ['./project-definition.component.scss']
})
export class ProjectDefinitionComponent implements AfterViewInit, OnDestroy {
  previewMapControl?: MapControl;
  areaSelectMapControl?: MapControl;
  projectGeom?: MultiPolygon;
  __projectGeom?: MultiPolygon;
  projectAreaErrors = [];
  projectSettings?: ProjectSettings;
  @ViewChild('areaCard') areaCard!: InputCardComponent;

  constructor(private mapService: MapService, private http: HttpClient, private rest: RestAPI) { }

  ngAfterViewInit(): void {
    this.setupPreviewMap();
    this.setupAreaCard();
    this.fetchProjectSettings();
  }

  fetchProjectSettings(): void {
    this.http.get<ProjectSettings>(this.rest.URLS.projectSettings).subscribe(projectSettings => {
      this.projectSettings = projectSettings;
      let previewLayer = this.previewMapControl?.map?.getLayer('project-area');
      if (previewLayer) {
        const format = new WKT();
        if (projectSettings.projectArea) {
          const wktSplit = projectSettings.projectArea.split(';'),
                epsg = wktSplit[0].replace('SRID=','EPSG:'),
                wkt = wktSplit[1];

          let feature = format.readFeature(wkt);
          feature.getGeometry().transform(epsg, `EPSG:${this.previewMapControl?.srid}`);
          this.projectGeom = feature.getGeometry();
          const source = previewLayer.getSource();
          source.clear();
          source.addFeature(feature);
          if (this.projectGeom?.getArea())
            this.previewMapControl?.map?.centerOnLayer('project-area');
        }
      }
    })
  }

  setupPreviewMap(): void {
    this.previewMapControl = this.mapService.get('project-preview-map');
    this.previewMapControl.setBackground(this.previewMapControl.getBackgroundLayers()[0].id);
    this.previewMapControl.map?.addVectorLayer('project-area',{
      visible: true,
      stroke: { color: 'orange' },
      fill: { color: 'yellow' },
      opacity: 0.5
    });
  }

  setupAreaCard(): void {
    const _this = this;
    this.areaCard.dialogOpened.subscribe(x => {
      this.projectAreaErrors = [];
      this.areaCard.setLoading(true);
      this.areaSelectMapControl = this.mapService.get('project-area-select-map');
      this.areaSelectMapControl.setBackground(this.areaSelectMapControl.getBackgroundLayers()[0].id)

      let projectLayer = this.areaSelectMapControl.map?.addVectorLayer('project-area', {
        stroke: { color: 'red', width: 5 },
        visible: true
      });
      let projectArea = new Feature(this.projectGeom);
      projectLayer?.getSource().addFeature(projectArea);
      const hasProjectArea = this.projectGeom?.getArea();
      if (hasProjectArea)
        this.areaSelectMapControl.map?.centerOnLayer('project-area');
      const format = new GeoJSON();
      this.areaSelectMapControl.map?.selected.subscribe(features => {
        let mergedGeom: turf.Feature<turf.MultiPolygon | turf.Polygon> | null = null;
        features.forEach(f => {
          // const json = format.writeGeometryObject(f.getGeometry());
          const poly = turf.multiPolygon(f.getGeometry().getCoordinates());
          mergedGeom = mergedGeom? union(poly, mergedGeom): poly;
        })
        // @ts-ignore
        this.__projectGeom = mergedGeom? format.readFeature(mergedGeom.geometry).getGeometry(): new MultiPolygon([]);
        if (this.__projectGeom instanceof Polygon)
          // @ts-ignore
          this.__projectGeom = new MultiPolygon([this.__projectGeom.getCoordinates()]);
        projectArea.setGeometry(this.__projectGeom);
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
      if (hasProjectArea) {
        const _this = this;
        let done = false;
        selectLayer?.getSource().addEventListener('featuresloadend', function () {
          if (done) return;
          done = true;
          _this.areaCard.setLoading(false);
          let mapEPSG = `EPSG:${_this.previewMapControl?.srid}`;
          let clonedPG = _this.projectGeom!.clone();
          clonedPG.transform(mapEPSG, 'EPSG:4326');
          const projectPoly = turf.multiPolygon(clonedPG.getCoordinates());
          const select = selectLayer?.get('select');
          selectLayer?.getSource().getFeatures().forEach((feature: Feature<any>) => {
            let fs: turf.Feature<any>[] = [];
            let cloned = feature.clone();
            cloned.getGeometry().transform(mapEPSG, 'EPSG:4326');
            cloned.getGeometry().getCoordinates().forEach((coords: any) => {
              let poly = turf.polygon(coords);
              // let buffered = buffer(poly, -1, {units: 'kilometers'});
              fs.push(poly);
            })
            const coll = turf.featureCollection(fs),
                  pos = pointOnSurface(coll);
            // const featPoly = turf.multiPolygon(feature.getGeometry().getCoordinates());
            // let intersection = intersect(featPoly, projectPoly);
            let intersection = booleanWithin(pos, projectPoly);
            if (intersection) {
              select.getFeatures().push(feature);
            }
          })
        });
      }
    })
    this.areaCard.dialogClosed.subscribe(x => {
      this.areaSelectMapControl?.destroy();
    })
    this.areaCard.dialogConfirmed.subscribe(ok => {
      const format = new WKT();
      let wkt = this.__projectGeom? `SRID=${this.areaSelectMapControl?.srid};` + format.writeGeometry(this.__projectGeom) : null
      this.http.patch<ProjectSettings>(`${this.rest.URLS.projectSettings}`,
        { projectArea: wkt }
      ).subscribe(data => {
        this.areaCard?.closeDialog(true);
        this.fetchProjectSettings();
      },(error) => {
        this.projectAreaErrors = error.error;
      });
    })
  }

  ngOnDestroy(): void {
    this.previewMapControl?.destroy();
  }

}
